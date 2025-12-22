"""
Reserve Supply Forecaster - Model Training

This script:
1. Loads synthetic historical supply data (or generates if missing)
2. Trains a RandomForest model to predict supply 2 hours ahead
3. Saves model and preprocessing parameters
"""

import pandas as pd
import numpy as np
import json
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import os

# Import data generation functions
from generate_data import generate_synthetic_data


# ============================================================================
# MODEL TRAINING FUNCTIONS
# ============================================================================

def prepare_features(df):
    """Prepare features for model training."""
    # Create a copy for feature engineering
    X = df.copy()
    
    # Extract temporal features (already present, but ensure they're numeric)
    X['hour_of_day'] = X['hour_of_day'].astype(int)
    X['day_of_week'] = X['day_of_week'].astype(int)
    
    # Encode zone_id using label encoding
    le = LabelEncoder()
    X['zone_id_encoded'] = le.fit_transform(X['zone_id'])
    
    # Select features
    feature_cols = [
        'zone_id_encoded',
        'hour_of_day',
        'day_of_week',
        'active_drivers',
        'reserve_bookings_next_60min',
        'on_demand_requests_last_60min',
        'weather_severity',
        'event_density'
    ]
    
    X_features = X[feature_cols]
    y = X['active_drivers_t_plus_120']
    
    return X_features, y, le


def train_model(df):
    """Train RandomForest model and return model, metrics, and preprocessing objects."""
    print("\nPreparing features...")
    X, y, label_encoder = prepare_features(df)
    
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    
    # Split data: 70% train, 20% validation, 10% test
    print("\nSplitting data...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=1/3, random_state=42
    )
    
    print(f"Train: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")
    
    # Train RandomForest model
    print("\nTraining RandomForest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate on validation set (for model development/tuning)
    print("\nEvaluating on validation set...")
    y_val_pred = model.predict(X_val)
    
    val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
    val_mae = mean_absolute_error(y_val, y_val_pred)
    val_r2 = r2_score(y_val, y_val_pred)
    
    print(f"Validation RMSE: {val_rmse:.2f}")
    print(f"Validation MAE: {val_mae:.2f}")
    print(f"Validation R²: {val_r2:.4f}")
    
    # Compute residual standard deviation from validation set
    val_residuals = y_val - y_val_pred
    residual_std = np.std(val_residuals)
    print(f"Residual Standard Deviation: {residual_std:.2f}")
    
    # Evaluate on test set (final unbiased performance estimate)
    print("\nEvaluating on test set (final performance)...")
    y_test_pred = model.predict(X_test)
    
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    print(f"Test RMSE: {test_rmse:.2f}")
    print(f"Test MAE: {test_mae:.2f}")
    print(f"Test R²: {test_r2:.4f}")
    
    # Compute test set residual standard deviation
    test_residuals = y_test - y_test_pred
    test_residual_std = np.std(test_residuals)
    print(f"Test Residual Standard Deviation: {test_residual_std:.2f}")
    
    # Compute supply status thresholds (20th and 80th percentiles)
    threshold_low = np.percentile(y_train, 20)
    threshold_high = np.percentile(y_train, 80)
    print(f"\nSupply Thresholds - Low: {threshold_low:.2f}, High: {threshold_high:.2f}")
    
    # Feature importance
    print("\nFeature Importance:")
    feature_names = X.columns.tolist()
    importances = model.feature_importances_
    for name, importance in sorted(zip(feature_names, importances), 
                                    key=lambda x: x[1], reverse=True):
        print(f"  {name}: {importance:.4f}")
    
    return {
        'model': model,
        'label_encoder': label_encoder,
        'feature_names': feature_names,
        # Validation metrics (for development)
        'val_rmse': val_rmse,
        'val_mae': val_mae,
        'val_r2': val_r2,
        # Test metrics (final performance)
        'test_rmse': test_rmse,
        'test_mae': test_mae,
        'test_r2': test_r2,
        # Use validation residual std for prediction intervals (as per design)
        'residual_std': residual_std,
        'test_residual_std': test_residual_std,
        'threshold_low': threshold_low,
        'threshold_high': threshold_high
    }


def save_model_artifacts(model_info, output_dir='models'):
    """Save model and preprocessing parameters."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save model
    model_path = os.path.join(output_dir, 'supply_model.pkl')
    joblib.dump(model_info['model'], model_path)
    print(f"\nSaved model to {model_path}")
    
    # Save preprocessing parameters
    preprocess_path = os.path.join(output_dir, 'preprocessing_params.json')
    preprocess_params = {
        'feature_names': model_info['feature_names'],
        'residual_std': float(model_info['residual_std']),
        'threshold_low': float(model_info['threshold_low']),
        'threshold_high': float(model_info['threshold_high']),
        'label_encoder_classes': model_info['label_encoder'].classes_.tolist(),
        # Include both validation and test metrics for reference
        'validation_metrics': {
            'rmse': float(model_info['val_rmse']),
            'mae': float(model_info['val_mae']),
            'r2': float(model_info['val_r2'])
        },
        'test_metrics': {
            'rmse': float(model_info['test_rmse']),
            'mae': float(model_info['test_mae']),
            'r2': float(model_info['test_r2'])
        }
    }
    
    with open(preprocess_path, 'w') as f:
        json.dump(preprocess_params, f, indent=2)
    print(f"Saved preprocessing parameters to {preprocess_path}")
    
    # Save label encoder separately (for easier loading)
    encoder_path = os.path.join(output_dir, 'label_encoder.pkl')
    joblib.dump(model_info['label_encoder'], encoder_path)
    print(f"Saved label encoder to {encoder_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("=" * 60)
    print("Reserve Supply Forecaster - Model Training")
    print("=" * 60)
    
    # Step 1: Load or generate data
    csv_path = os.path.join('data', 'synthetic_supply.csv')
    if os.path.exists(csv_path):
        print(f"\nLoading existing data from {csv_path}...")
        df = pd.read_csv(csv_path, parse_dates=['timestamp'])
        print(f"Loaded {len(df)} rows of data")
    else:
        print("\nData file not found. Generating new data...")
        df = generate_synthetic_data(output_path=csv_path)
    
    # Step 2: Train model
    model_info = train_model(df)
    
    # Step 3: Save model artifacts
    save_model_artifacts(model_info)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
