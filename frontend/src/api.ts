/**
 * API Client for Reserve Supply Forecaster
 * Handles communication with the FastAPI backend
 */

// Use environment variable for production, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export interface PredictionRequest {
  timestamp: string;
  zone_id: string;
  active_drivers: number;
  reserve_bookings_next_60min: number;
  on_demand_requests_last_60min: number;
  weather_severity: number;
  event_density: number;
}

export interface PredictionResponse {
  expected_drivers_in_2h: number;
  low_bound: number;
  high_bound: number;
  supply_status: string;
  comment: string;
}

export interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
}

export interface FeatureContribution {
  feature_name: string;
  contribution: number;
  percentage: number;
}

export interface SimilarCase {
  zone_id: string;
  timestamp: string;
  active_drivers: number;
  predicted_drivers: number;
  actual_drivers?: number | null;
  similarity_score: number;
}

export interface PredictionAnalysisResponse {
  prediction: number;
  feature_contributions: FeatureContribution[];
  confidence_score: number;
  confidence_level: string;
  similar_cases: SimilarCase[];
  anomaly_flags: Record<string, boolean>;
  anomaly_reasons: string[];
}

/**
 * Predict future driver supply based on current conditions
 */
export async function predictSupply(
  request: PredictionRequest
): Promise<PredictionResponse> {
  const response = await fetch(`${API_BASE_URL}/predict_supply`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    
    // Format validation errors
    if (Array.isArray(errorData.detail)) {
      const messages = errorData.detail.map((err) => 
        `${err.loc.join('.')}: ${err.msg}`
      ).join(', ');
      throw new Error(`Validation error: ${messages}`);
    }
    
    throw new Error(
      typeof errorData.detail === 'string' 
        ? errorData.detail 
        : `API error: ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Analyze prediction with feature contributions, confidence, similar cases, and anomalies
 */
export async function analyzePrediction(
  request: PredictionRequest
): Promise<PredictionAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze_prediction`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    
    // Format validation errors
    if (Array.isArray(errorData.detail)) {
      const messages = errorData.detail.map((err) => 
        `${err.loc.join('.')}: ${err.msg}`
      ).join(', ');
      throw new Error(`Validation error: ${messages}`);
    }
    
    throw new Error(
      typeof errorData.detail === 'string' 
        ? errorData.detail 
        : `API error: ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Check API health status
 */
export async function checkHealth(): Promise<{ status: string; model_loaded: boolean }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}

