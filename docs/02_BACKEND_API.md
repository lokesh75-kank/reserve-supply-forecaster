# Backend API Plan

## Overview

This document outlines the FastAPI backend implementation for the Reserve Supply Forecaster API. The API exposes endpoints to make supply predictions based on current conditions.

## Technology Stack

- **Framework:** FastAPI
- **Language:** Python 3.9+
- **ASGI Server:** Uvicorn
- **Model Loading:** joblib/pickle for .pkl files
- **Data Processing:** pandas, numpy

## API Endpoints

### 1. Prediction Endpoint

**Endpoint:** `POST /predict_supply`

**Purpose:** Predict future driver supply (2 hours ahead) given current conditions.

#### Request Format

```json
{
  "timestamp": "2025-01-10T18:00:00",
  "zone_id": "Z3",
  "active_drivers": 20,
  "reserve_bookings_next_60min": 5,
  "on_demand_requests_last_60min": 30,
  "weather_severity": 1,
  "event_density": 2
}
```

#### Request Schema

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `timestamp` | string (ISO 8601) | Current observation time | Required |
| `zone_id` | string | Zone identifier | Must be one of: Z1, Z2, Z3, Z4, Z5 |
| `active_drivers` | integer | Current active drivers in zone | >= 0 |
| `reserve_bookings_next_60min` | integer | Reserve bookings in next 60 min | >= 0 |
| `on_demand_requests_last_60min` | integer | On-demand requests in last 60 min | >= 0 |
| `weather_severity` | integer | Weather condition | 0, 1, or 2 |
| `event_density` | integer | Event intensity | 0, 1, or 2 |

#### Response Format

```json
{
  "expected_drivers_in_2h": 27.5,
  "low_bound": 22.1,
  "high_bound": 33.0,
  "supply_status": "Tight",
  "comment": "Increase incentives; limit new Reserve bookings."
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `expected_drivers_in_2h` | float | Predicted active drivers in 2 hours |
| `low_bound` | float | Lower bound of prediction interval |
| `high_bound` | float | Upper bound of prediction interval |
| `supply_status` | string | One of: "Tight", "Balanced", "Surplus" |
| `comment` | string | Actionable recommendation |

#### Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid zone_id. Must be one of: Z1, Z2, Z3, Z4, Z5"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Model prediction failed"
}
```

### 2. Health Check Endpoint

**Endpoint:** `GET /health`

**Purpose:** Check API and model availability.

#### Response Format

```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### 3. Model Info Endpoint (Optional)

**Endpoint:** `GET /model_info`

**Purpose:** Return model metadata (feature importance, training metrics).

#### Response Format

```json
{
  "model_type": "RandomForestRegressor",
  "features": ["zone_id", "hour_of_day", "day_of_week", ...],
  "training_rmse": 3.2,
  "training_mae": 2.1,
  "r2_score": 0.85
}
```

## Implementation Structure

### File: `backend/app.py`

**Main Components:**

1. **FastAPI App Initialization**
   ```python
   from fastapi import FastAPI
   app = FastAPI(title="Reserve Supply Forecaster API")
   ```

2. **Model Loading**
   - Load model on startup (using startup event or lazy loading)
   - Load preprocessing parameters if needed
   - Validate model is ready

3. **Pydantic Models** (Request/Response schemas)
   ```python
   from pydantic import BaseModel, Field
   
   class SupplyPredictionRequest(BaseModel):
       timestamp: str
       zone_id: str
       active_drivers: int = Field(ge=0)
       reserve_bookings_next_60min: int = Field(ge=0)
       on_demand_requests_last_60min: int = Field(ge=0)
       weather_severity: int = Field(ge=0, le=2)
       event_density: int = Field(ge=0, le=2)
   
   class SupplyPredictionResponse(BaseModel):
       expected_drivers_in_2h: float
       low_bound: float
       high_bound: float
       supply_status: str
       comment: str
   ```

4. **Feature Preprocessing Function**
   - Convert request to model input format
   - Handle zone_id encoding (one-hot or label encoding)
   - Extract hour_of_day and day_of_week from timestamp
   - Ensure feature order matches training

5. **Prediction Function**
   - Preprocess input
   - Run model prediction
   - Calculate low/high bounds using residual std dev
   - Determine supply status from thresholds
   - Generate recommendation comment

6. **Status Comment Logic**
   ```python
   def get_status_comment(status: str, expected: float) -> str:
       if status == "Tight":
           return "Increase incentives; limit new Reserve bookings."
       elif status == "Balanced":
           return "Supply looks stable. OK to accept Reserve bookings."
       else:  # Surplus
           return "Surplus supply available. Can accept more Reserve bookings."
   ```

## Error Handling

- **Validation Errors:** Use Pydantic validators for request validation
- **Model Errors:** Try-except around prediction, return 500 with detail
- **Missing Model File:** Return 503 Service Unavailable if model not loaded

## CORS Configuration

Enable CORS for frontend requests:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Running the API

### Development

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Production (Optional)

- Use Gunicorn with Uvicorn workers
- Add rate limiting if needed
- Add authentication/API keys if required

## Testing the API

**Manual Test with curl:**
```bash
curl -X POST "http://localhost:8000/predict_supply" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-01-10T18:00:00",
    "zone_id": "Z3",
    "active_drivers": 20,
    "reserve_bookings_next_60min": 5,
    "on_demand_requests_last_60min": 30,
    "weather_severity": 1,
    "event_density": 2
  }'
```

## Dependencies

**File:** `backend/requirements.txt`

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
joblib==1.3.2
python-multipart==0.0.6
```

