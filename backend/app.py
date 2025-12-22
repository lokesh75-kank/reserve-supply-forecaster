"""
FastAPI application for Reserve Supply Forecaster

This API provides endpoints to predict future driver supply availability
for Uber Reserve services based on current conditions.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import joblib
import json
import os
import numpy as np
import pandas as pd
from typing import Optional, List, Dict
import logging
from sklearn.metrics.pairwise import euclidean_distances

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Reserve Supply Forecaster API",
    description="API for predicting future driver supply availability",
    version="1.0.0"
)

# CORS middleware for frontend
# Allow all localhost origins for development
logger.info("Configuring CORS middleware...")
# IMPORTANT: CORS middleware must be added BEFORE other middleware
# CORS configuration - allow localhost for development and frontend URL for production
frontend_url = os.getenv("FRONTEND_URL", "")
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
]
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",  # Also allow any localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORS configured - Frontend URL: {frontend_url or 'Not set (using localhost)'}")
logger.info("CORS middleware configured with origins: http://localhost:5173, http://localhost:5174, http://localhost:3000")

# Global variables for model and preprocessing parameters
model = None
label_encoder = None
preprocessing_params = None
training_data = None  # For finding similar cases
feature_means = None  # For permutation-based contributions


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SupplyPredictionRequest(BaseModel):
    """Request model for supply prediction."""
    timestamp: str = Field(..., description="ISO 8601 timestamp (e.g., '2025-01-10T18:00:00')")
    zone_id: str = Field(..., description="Zone identifier (Z1-Z5)")
    active_drivers: int = Field(..., ge=0, description="Current active drivers in zone")
    reserve_bookings_next_60min: int = Field(..., ge=0, description="Reserve bookings in next 60 minutes")
    on_demand_requests_last_60min: int = Field(..., ge=0, description="On-demand requests in last 60 minutes")
    weather_severity: int = Field(..., ge=0, le=2, description="Weather severity (0=clear, 1=rain, 2=storm)")
    event_density: int = Field(..., ge=0, le=2, description="Event density (0=none, 1=small, 2=stadium)")

    @field_validator('zone_id')
    @classmethod
    def validate_zone_id(cls, v):
        valid_zones = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']
        if v not in valid_zones:
            raise ValueError(f"zone_id must be one of: {valid_zones}")
        return v

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("timestamp must be a valid ISO 8601 format")
        return v


class SupplyPredictionResponse(BaseModel):
    """Response model for supply prediction."""
    expected_drivers_in_2h: float = Field(..., description="Predicted active drivers in 2 hours")
    low_bound: float = Field(..., description="Lower bound of prediction interval")
    high_bound: float = Field(..., description="Upper bound of prediction interval")
    supply_status: str = Field(..., description="Supply status: Tight, Balanced, or Surplus")
    comment: str = Field(..., description="Actionable recommendation")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model_loaded: bool
    version: str


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    model_type: str
    features: list[str]
    validation_metrics: dict
    test_metrics: dict
    thresholds: dict


class FeatureContribution(BaseModel):
    """Feature contribution to prediction."""
    feature_name: str
    contribution: float
    percentage: float


class SimilarCase(BaseModel):
    """Similar historical case."""
    zone_id: str
    timestamp: str
    active_drivers: int
    predicted_drivers: float
    actual_drivers: Optional[float] = None
    similarity_score: float


class PredictionAnalysisResponse(BaseModel):
    """Response model for prediction analysis."""
    prediction: float
    feature_contributions: List[FeatureContribution]
    confidence_score: float
    confidence_level: str  # "High", "Medium", "Low"
    similar_cases: List[SimilarCase]
    anomaly_flags: Dict[str, bool]
    anomaly_reasons: List[str]


# ============================================================================
# MODEL LOADING FUNCTIONS
# ============================================================================

def load_model_artifacts():
    """Load model and preprocessing parameters."""
    global model, label_encoder, preprocessing_params
    
    logger.info("Loading model artifacts...")
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    
    # Load model
    model_path = os.path.join(models_dir, 'supply_model.pkl')
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        raise FileNotFoundError(f"Model file not found: {model_path}")
    logger.info(f"Loading model from {model_path}")
    model = joblib.load(model_path)
    logger.info("Model loaded successfully")
    
    # Load label encoder
    encoder_path = os.path.join(models_dir, 'label_encoder.pkl')
    if not os.path.exists(encoder_path):
        logger.error(f"Label encoder file not found: {encoder_path}")
        raise FileNotFoundError(f"Label encoder file not found: {encoder_path}")
    logger.info(f"Loading label encoder from {encoder_path}")
    label_encoder = joblib.load(encoder_path)
    logger.info("Label encoder loaded successfully")
    
    # Load preprocessing parameters
    params_path = os.path.join(models_dir, 'preprocessing_params.json')
    if not os.path.exists(params_path):
        logger.error(f"Preprocessing parameters file not found: {params_path}")
        raise FileNotFoundError(f"Preprocessing parameters file not found: {params_path}")
    logger.info(f"Loading preprocessing parameters from {params_path}")
    with open(params_path, 'r') as f:
        preprocessing_params = json.load(f)
    
    logger.info("Model and preprocessing parameters loaded successfully")
    
    # Load training data for similar case finding and feature means calculation
    global training_data, feature_means
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'synthetic_supply.csv')
    if os.path.exists(data_path):
        logger.info(f"Loading training data from {data_path}")
        training_data = pd.read_csv(data_path, parse_dates=['timestamp'])
        logger.info(f"Loaded {len(training_data)} training samples")
        
        # Calculate feature means/medians for permutation-based contributions
        logger.info("Calculating feature statistics for permutation-based contributions...")
        feature_means = {}
        
        # Prepare training features to match model input format
        X_train = training_data.copy()
        X_train['hour_of_day'] = X_train['hour_of_day'].astype(int)
        X_train['day_of_week'] = X_train['day_of_week'].astype(int)
        X_train['zone_id_encoded'] = label_encoder.transform(X_train['zone_id'])
        
        feature_cols = preprocessing_params['feature_names']
        
        # Calculate mean for each feature
        for feature in feature_cols:
            if feature in X_train.columns:
                feature_means[feature] = float(X_train[feature].mean())
                logger.debug(f"  {feature}: mean = {feature_means[feature]:.2f}")
        
        logger.info(f"Calculated means for {len(feature_means)} features")
    else:
        logger.warning("Training data not found - similar cases and feature contributions will be limited")
        training_data = None
        feature_means = None


@app.on_event("startup")
async def startup_event():
    """Load model on application startup."""
    logger.info("=" * 60)
    logger.info("Starting Reserve Supply Forecaster API")
    logger.info("=" * 60)
    try:
        load_model_artifacts()
        logger.info("API startup complete - Ready to accept requests")
    except Exception as e:
        logger.error(f"Error loading model: {e}", exc_info=True)
        raise


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def preprocess_features(request: SupplyPredictionRequest) -> np.ndarray:
    """
    Preprocess request data to match model input format.
    
    Args:
        request: SupplyPredictionRequest object
    
    Returns:
        numpy array of features in the correct order
    """
    # Parse timestamp to extract hour_of_day and day_of_week
    dt = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
    hour_of_day = dt.hour
    day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
    
    # Encode zone_id
    zone_encoded = label_encoder.transform([request.zone_id])[0]
    
    # Create feature array in the exact order expected by the model
    # Order: zone_id_encoded, hour_of_day, day_of_week, active_drivers,
    #        reserve_bookings_next_60min, on_demand_requests_last_60min,
    #        weather_severity, event_density
    features = np.array([[
        zone_encoded,
        hour_of_day,
        day_of_week,
        request.active_drivers,
        request.reserve_bookings_next_60min,
        request.on_demand_requests_last_60min,
        request.weather_severity,
        request.event_density
    ]])
    
    return features


def get_supply_status(prediction: float, threshold_low: float, threshold_high: float) -> str:
    """
    Determine supply status based on prediction and thresholds.
    
    Args:
        prediction: Predicted number of drivers
        threshold_low: Low threshold (20th percentile)
        threshold_high: High threshold (80th percentile)
    
    Returns:
        Supply status: "Tight", "Balanced", or "Surplus"
    """
    if prediction < threshold_low:
        return "Tight Supply"
    elif prediction >= threshold_high:
        return "Surplus"
    else:
        return "Balanced"


def get_recommendation(status: str, expected: float) -> str:
    """
    Generate actionable recommendation based on supply status.
    
    Args:
        status: Supply status string
        expected: Expected number of drivers
    
    Returns:
        Recommendation comment
    """
    if status == "Tight Supply":
        return "Increase incentives; limit new Reserve bookings."
    elif status == "Balanced":
        return "Supply looks stable. OK to accept Reserve bookings."
    else:  # Surplus
        return "Surplus supply available. Can accept more Reserve bookings."


def calculate_feature_contributions(model, features: np.ndarray, feature_names: List[str]) -> List[FeatureContribution]:
    """
    Calculate feature contributions using permutation-based method.
    For each feature, replace it with its mean value and measure prediction change.
    This gives instance-specific, interpretable contributions.
    
    Args:
        model: Trained RandomForest model
        features: Input features array (shape: [1, n_features])
        feature_names: List of feature names
    
    Returns:
        List of FeatureContribution objects with actual driver changes
    """
    if feature_means is None:
        logger.warning("Feature means not available, falling back to simplified method")
        return _calculate_feature_contributions_simplified(model, features, feature_names)
    
    # Get original prediction
    base_prediction = float(model.predict(features)[0])
    contributions = []
    
    # Create a copy of features for permutation
    features_array = features[0].copy()
    
    # For each feature, calculate contribution by permuting it
    for i, feature_name in enumerate(feature_names):
        if feature_name not in feature_means:
            # Skip if we don't have mean for this feature
            logger.warning(f"No mean value for feature: {feature_name}")
            contributions.append({
                'feature_name': feature_name,
                'contribution': 0.0,
                'importance': 0.0
            })
            continue
        
        # Get the mean value for this feature
        mean_value = feature_means[feature_name]
        original_value = features_array[i]
        
        # Skip if feature is already at mean (no contribution)
        if abs(original_value - mean_value) < 1e-6:
            contributions.append({
                'feature_name': feature_name,
                'contribution': 0.0,
                'importance': 0.0
            })
            continue
        
        # Create permuted features: replace this feature with its mean
        permuted_features = features_array.copy()
        permuted_features[i] = mean_value
        
        # Make prediction with permuted feature
        permuted_prediction = float(model.predict(permuted_features.reshape(1, -1))[0])
        
        # Contribution = original prediction - permuted prediction
        # Positive means feature increases prediction, negative means it decreases
        contribution = base_prediction - permuted_prediction
        
        contributions.append({
            'feature_name': feature_name,
            'contribution': float(contribution),
            'importance': abs(float(contribution))  # Use absolute for percentage calculation
        })
    
    # Calculate percentages based on absolute contributions
    total_abs_contribution = sum(abs(c['contribution']) for c in contributions)
    if total_abs_contribution > 0:
        for c in contributions:
            c['percentage'] = (abs(c['contribution']) / total_abs_contribution) * 100
    else:
        for c in contributions:
            c['percentage'] = 0.0
    
    # Sort by absolute contribution (most impactful first)
    contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
    
    logger.debug(f"Feature contributions calculated. Base prediction: {base_prediction:.2f}")
    logger.debug(f"Total absolute contributions: {total_abs_contribution:.2f}")
    
    return [
        FeatureContribution(
            feature_name=c['feature_name'],
            contribution=round(c['contribution'], 2),
            percentage=round(c['percentage'], 1)
        )
        for c in contributions
    ]


def _calculate_feature_contributions_simplified(model, features: np.ndarray, feature_names: List[str]) -> List[FeatureContribution]:
    """
    Fallback simplified method when feature means are not available.
    Uses feature importance weighted by feature values.
    """
    base_prediction = model.predict(features)[0]
    contributions = []
    
    # Use feature importances weighted by actual feature values
    for i, feature_name in enumerate(feature_names):
        importance = model.feature_importances_[i]
        feature_value = features[0, i]
        
        # Simplified approximation
        contribution = importance * feature_value * base_prediction * 0.1
        
        contributions.append({
            'feature_name': feature_name,
            'contribution': float(contribution),
            'importance': float(importance)
        })
    
    # Normalize contributions
    total_importance = sum(c['importance'] for c in contributions)
    if total_importance > 0:
        scale_factor = base_prediction / total_importance if total_importance > 0 else 1.0
        for c in contributions:
            c['contribution'] = c['importance'] * scale_factor * base_prediction * 0.3
    
    # Calculate percentages
    total_abs_contribution = sum(abs(c['contribution']) for c in contributions)
    if total_abs_contribution > 0:
        for c in contributions:
            c['percentage'] = (abs(c['contribution']) / total_abs_contribution) * 100
    else:
        for c in contributions:
            c['percentage'] = 0.0
    
    # Sort by absolute contribution
    contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
    
    return [
        FeatureContribution(
            feature_name=c['feature_name'],
            contribution=round(c['contribution'], 2),
            percentage=round(c['percentage'], 1)
        )
        for c in contributions
    ]


def calculate_confidence_score(prediction: float, residual_std: float, threshold_low: float, threshold_high: float) -> tuple:
    """
    Calculate confidence score based on prediction uncertainty.
    
    Args:
        prediction: Predicted value
        residual_std: Residual standard deviation
        threshold_low: Low threshold
        threshold_high: High threshold
    
    Returns:
        Tuple of (confidence_score, confidence_level)
    """
    # Confidence based on:
    # 1. Relative uncertainty (lower std relative to prediction = higher confidence)
    # 2. Distance from thresholds (middle of range = higher confidence)
    
    # Relative uncertainty component (0-50 points)
    relative_uncertainty = residual_std / max(prediction, 1.0)
    uncertainty_score = max(0, 50 - (relative_uncertainty * 100))
    
    # Position in range component (0-50 points)
    range_size = threshold_high - threshold_low
    if range_size > 0:
        distance_from_low = abs(prediction - threshold_low)
        distance_from_high = abs(prediction - threshold_high)
        min_distance = min(distance_from_low, distance_from_high)
        position_score = min(50, (min_distance / range_size) * 50)
    else:
        position_score = 25
    
    confidence_score = uncertainty_score + position_score
    confidence_score = max(0, min(100, confidence_score))
    
    # Determine confidence level
    if confidence_score >= 70:
        level = "High"
    elif confidence_score >= 40:
        level = "Medium"
    else:
        level = "Low"
    
    return round(confidence_score, 1), level


def find_similar_cases(features: np.ndarray, request: SupplyPredictionRequest, n_cases: int = 5) -> List[SimilarCase]:
    """
    Find similar historical cases from training data.
    
    Args:
        features: Preprocessed features array
        request: Original request object
        n_cases: Number of similar cases to return
    
    Returns:
        List of SimilarCase objects
    """
    if training_data is None:
        return []
    
    try:
        # Prepare training features for comparison
        X_train = training_data.copy()
        X_train['hour_of_day'] = X_train['hour_of_day'].astype(int)
        X_train['day_of_week'] = X_train['day_of_week'].astype(int)
        X_train['zone_id_encoded'] = label_encoder.transform(X_train['zone_id'])
        
        feature_cols = preprocessing_params['feature_names']
        X_train_features = X_train[feature_cols].values
        
        # Calculate distances
        distances = euclidean_distances(features, X_train_features)[0]
        
        # Get top N similar cases
        top_indices = np.argsort(distances)[:n_cases]
        
        similar_cases = []
        for idx in top_indices:
            row = training_data.iloc[idx]
            similarity_score = 1.0 / (1.0 + distances[idx])  # Convert distance to similarity (0-1)
            
            similar_cases.append(SimilarCase(
                zone_id=row['zone_id'],
                timestamp=row['timestamp'].isoformat() if pd.notna(row['timestamp']) else "",
                active_drivers=int(row['active_drivers']),
                predicted_drivers=float(model.predict(X_train_features[idx:idx+1])[0]),
                actual_drivers=float(row['active_drivers_t_plus_120']) if 'active_drivers_t_plus_120' in row else None,
                similarity_score=round(similarity_score, 3)
            ))
        
        return similar_cases
    except Exception as e:
        logger.error(f"Error finding similar cases: {e}", exc_info=True)
        return []


def detect_anomalies(features: np.ndarray, prediction: float, request: SupplyPredictionRequest, 
                     threshold_low: float, threshold_high: float) -> tuple:
    """
    Detect anomalies in the prediction.
    
    Args:
        features: Preprocessed features
        prediction: Predicted value
        request: Original request
        threshold_low: Low threshold
        threshold_high: High threshold
    
    Returns:
        Tuple of (anomaly_flags dict, anomaly_reasons list)
    """
    flags = {}
    reasons = []
    
    # Check if prediction is extreme
    if prediction < threshold_low * 0.5:
        flags['extreme_low'] = True
        reasons.append(f"Prediction ({prediction:.1f}) is extremely low (below 50% of low threshold)")
    elif prediction > threshold_high * 1.5:
        flags['extreme_high'] = True
        reasons.append(f"Prediction ({prediction:.1f}) is extremely high (above 150% of high threshold)")
    else:
        flags['extreme_low'] = False
        flags['extreme_high'] = False
    
    # Check for unusual feature combinations
    if request.weather_severity == 2 and request.event_density == 2:
        flags['extreme_conditions'] = True
        reasons.append("Combination of storm weather and stadium event is rare")
    else:
        flags['extreme_conditions'] = False
    
    # Check if active drivers is unusually low/high
    if request.active_drivers == 0:
        flags['zero_drivers'] = True
        reasons.append("Current active drivers is zero - unusual scenario")
    elif request.active_drivers > 50:
        flags['very_high_drivers'] = True
        reasons.append(f"Current active drivers ({request.active_drivers}) is unusually high")
    else:
        flags['zero_drivers'] = False
        flags['very_high_drivers'] = False
    
    # Check prediction consistency with current supply
    supply_change = prediction - request.active_drivers
    if abs(supply_change) > 30:
        flags['large_change'] = True
        reasons.append(f"Predicted change ({supply_change:+.1f} drivers) is unusually large")
    else:
        flags['large_change'] = False
    
    return flags, reasons


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    logger.info("Root endpoint accessed")
    return {
        "message": "Reserve Supply Forecaster API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns API status and model loading status.
    """
    logger.debug("Health check requested")
    health_status = HealthResponse(
        status="healthy",
        model_loaded=model is not None,
        version="1.0.0"
    )
    logger.info(f"Health check: status={health_status.status}, model_loaded={health_status.model_loaded}")
    return health_status


@app.get("/model_info", response_model=ModelInfoResponse, tags=["Model"])
async def get_model_info():
    """
    Get model information including features, metrics, and thresholds.
    """
    logger.info("Model info requested")
    if model is None or preprocessing_params is None:
        logger.error("Model info requested but model not loaded")
        raise HTTPException(
            status_code=503,
            detail="Model not loaded"
        )
    
    logger.info("Returning model information")
    return ModelInfoResponse(
        model_type="RandomForestRegressor",
        features=preprocessing_params['feature_names'],
        validation_metrics=preprocessing_params.get('validation_metrics', {}),
        test_metrics=preprocessing_params.get('test_metrics', {}),
        thresholds={
            "low": preprocessing_params['threshold_low'],
            "high": preprocessing_params['threshold_high']
        }
    )


@app.post("/predict_supply", response_model=SupplyPredictionResponse, tags=["Prediction"])
async def predict_supply(request: SupplyPredictionRequest):
    """
    Predict future driver supply (2 hours ahead) given current conditions.
    
    Args:
        request: SupplyPredictionRequest with current conditions
    
    Returns:
        SupplyPredictionResponse with prediction and recommendations
    """
    logger.info("=" * 60)
    logger.info("New prediction request received")
    logger.info(f"Zone: {request.zone_id}, Timestamp: {request.timestamp}")
    logger.info(f"Active Drivers: {request.active_drivers}, Reserve Bookings: {request.reserve_bookings_next_60min}")
    logger.info(f"On-Demand Requests: {request.on_demand_requests_last_60min}")
    logger.info(f"Weather: {request.weather_severity}, Event Density: {request.event_density}")
    
    # Check if model is loaded
    if model is None or preprocessing_params is None:
        logger.error("Prediction requested but model not loaded")
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please check server logs."
        )
    
    try:
        # Preprocess features
        logger.debug("Preprocessing features...")
        features = preprocess_features(request)
        logger.debug(f"Preprocessed features: {features.tolist()}")
        
        # Make prediction
        logger.debug("Making prediction...")
        prediction = model.predict(features)[0]
        logger.info(f"Raw prediction: {prediction:.2f} drivers")
        
        # Calculate prediction bounds using residual standard deviation
        residual_std = preprocessing_params['residual_std']
        low_bound = max(0, prediction - 1.0 * residual_std)  # Ensure non-negative
        high_bound = prediction + 1.0 * residual_std
        logger.debug(f"Prediction bounds: [{low_bound:.2f}, {high_bound:.2f}]")
        
        # Determine supply status
        threshold_low = preprocessing_params['threshold_low']
        threshold_high = preprocessing_params['threshold_high']
        supply_status = get_supply_status(prediction, threshold_low, threshold_high)
        logger.info(f"Supply status: {supply_status} (thresholds: low={threshold_low}, high={threshold_high})")
        
        # Generate recommendation
        comment = get_recommendation(supply_status, prediction)
        logger.info(f"Recommendation: {comment}")
        
        response = SupplyPredictionResponse(
            expected_drivers_in_2h=round(float(prediction), 2),
            low_bound=round(float(low_bound), 2),
            high_bound=round(float(high_bound), 2),
            supply_status=supply_status,
            comment=comment
        )
        
        logger.info("=" * 60)
        logger.info(f"Prediction complete: {response.expected_drivers_in_2h} drivers (status: {supply_status})")
        logger.info("=" * 60)
        
        return response
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/analyze_prediction", response_model=PredictionAnalysisResponse, tags=["Prediction"])
async def analyze_prediction(request: SupplyPredictionRequest):
    """
    Analyze a prediction with feature contributions, confidence score, similar cases, and anomaly detection.
    
    Args:
        request: SupplyPredictionRequest with current conditions
    
    Returns:
        PredictionAnalysisResponse with detailed analysis
    """
    logger.info("=" * 60)
    logger.info("Prediction analysis requested")
    logger.info(f"Zone: {request.zone_id}, Timestamp: {request.timestamp}")
    
    if model is None or preprocessing_params is None:
        logger.error("Analysis requested but model not loaded")
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please check server logs."
        )
    
    try:
        # Preprocess features
        features = preprocess_features(request)
        
        # Make prediction
        prediction = model.predict(features)[0]
        logger.info(f"Prediction: {prediction:.2f} drivers")
        
        # Calculate feature contributions
        feature_names = preprocessing_params['feature_names']
        feature_contributions = calculate_feature_contributions(model, features, feature_names)
        logger.info(f"Calculated {len(feature_contributions)} feature contributions")
        
        # Calculate confidence score
        residual_std = preprocessing_params['residual_std']
        threshold_low = preprocessing_params['threshold_low']
        threshold_high = preprocessing_params['threshold_high']
        confidence_score, confidence_level = calculate_confidence_score(
            prediction, residual_std, threshold_low, threshold_high
        )
        logger.info(f"Confidence: {confidence_score}% ({confidence_level})")
        
        # Find similar cases
        similar_cases = find_similar_cases(features, request, n_cases=5)
        logger.info(f"Found {len(similar_cases)} similar cases")
        
        # Detect anomalies
        anomaly_flags, anomaly_reasons = detect_anomalies(
            features, prediction, request, threshold_low, threshold_high
        )
        logger.info(f"Anomaly flags: {anomaly_flags}")
        
        logger.info("=" * 60)
        logger.info("Prediction analysis complete")
        logger.info("=" * 60)
        
        return PredictionAnalysisResponse(
            prediction=round(float(prediction), 2),
            feature_contributions=feature_contributions,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            similar_cases=similar_cases,
            anomaly_flags=anomaly_flags,
            anomaly_reasons=anomaly_reasons
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
