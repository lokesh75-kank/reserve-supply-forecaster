# Data & Modeling Plan

## Overview

This document outlines the data schema, generation strategy, and machine learning modeling approach for the Reserve Supply Forecaster.

## Data Schema

### Historical Supply Table

**Table Name:** `historical_supply`

**Primary Purpose:** Train and validate the supply forecasting model with synthetic ride-marketplace data.

### Columns

| Column Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `timestamp` | datetime | Observation time in 15-min intervals | 2025-01-01 18:00:00 |
| `zone_id` | string | Geographic zone identifier | Z1, Z2, Z3, Z4, Z5 |
| `active_drivers` | integer | Current active drivers in zone at timestamp | 20, 35, 12 |
| `reserve_bookings_next_60min` | integer | Number of Reserve pickups scheduled in next hour | 5, 8, 3 |
| `on_demand_requests_last_60min` | integer | On-demand trip requests in last 60 minutes | 30, 45, 20 |
| `weather_severity` | integer | Weather condition (0=clear, 1=rain, 2=storm) | 0, 1, 2 |
| `event_density` | integer | Event intensity (0=none, 1=small, 2=stadium) | 0, 1, 2 |
| `hour_of_day` | integer | Hour of day (0-23) | 8, 18, 22 |
| `day_of_week` | integer | Day of week (0=Mon, 6=Sun) | 0, 5, 6 |
| `active_drivers_t_plus_120` | integer | **TARGET:** Active drivers 2 hours after timestamp | 27, 40, 15 |

## Data Generation Strategy

### Zones
- **5 zones** to keep it simple and manageable
- Zone IDs: Z1, Z2, Z3, Z4, Z5
- Each zone will have distinct supply/demand patterns

### Time Coverage
- **30 days** of historical data
- **15-minute intervals** (96 observations per day)
- Total: ~2,880 rows per zone, ~14,400 total rows

### Pattern Injection

#### 1. Base Supply Pattern
- **Rush Hours (7-9 AM, 5-7 PM):** Higher demand, moderate supply
- **Night (10 PM - 2 AM):** Lower supply, variable demand
- **Weekend vs Weekday:** Different patterns
- **Base formula:** `base_supply = f(hour_of_day, day_of_week)`

#### 2. Weather Effects
- **Clear (0):** Normal supply
- **Rain (1):** Supply decreases by 10-15%, demand increases by 20-30%
- **Storm (2):** Supply decreases by 25-35%, demand increases by 40-50%

#### 3. Event Effects
- **No Event (0):** Normal patterns
- **Small Event (1):** Localized demand spike (+30-50 requests)
- **Stadium Event (2):** Major demand spike (+100-200 requests), supply may decrease slightly

#### 4. Reserve Bookings Impact
- Higher Reserve bookings → slightly lower available supply 2 hours ahead
- Creates realistic coupling between bookings and future availability

#### 5. Noise and Randomness
- Add Gaussian noise to simulate real-world variability
- Autocorrelation between time steps to simulate temporal dependencies

### Data Generation Implementation

**File:** `backend/train_model.py`

**Approach:**
1. Define zone list and time range
2. Generate base supply curve per zone (time-of-day, day-of-week effects)
3. For each (zone, timestamp):
   - Compute base supply
   - Apply weather modifier
   - Apply event modifier
   - Add noise
   - Compute target `active_drivers_t_plus_120` by shifting 2 hours ahead
4. Save to CSV: `backend/data/synthetic_supply.csv`

## Modeling Approach

### Problem Formulation

**Task:** Regression problem
- **Input:** Current conditions (zone, time, supply, demand, weather, events)
- **Output:** Expected active drivers in 2 hours
- **Additional Output:** Uncertainty envelope (low/high bounds)

### Feature Engineering

**Input Features:**
1. `zone_id` - One-hot encoded or label encoded (5 zones)
2. `hour_of_day` - Numeric (0-23) or cyclic encoding (sin/cos)
3. `day_of_week` - Numeric (0-6) or cyclic encoding
4. `active_drivers` - Numeric (current supply)
5. `reserve_bookings_next_60min` - Numeric
6. `on_demand_requests_last_60min` - Numeric (demand pressure)
7. `weather_severity` - Numeric (0-2) or one-hot
8. `event_density` - Numeric (0-2) or one-hot

**Target Variable:**
- `active_drivers_t_plus_120` - Active drivers 2 hours in future

### Model Selection

**Primary Choice:** RandomForestRegressor or XGBoostRegressor

**Rationale:**
- Handles nonlinear relationships well
- Fast training on ~14K rows
- Provides feature importance insights
- Can estimate prediction uncertainty

**Implementation Steps:**
1. Load and preprocess data
2. Split: 70% train, 20% validation, 10% test
3. Train model on training set
4. Evaluate on validation set (compute RMSE, MAE)
5. Estimate residual standard deviation (σ) from validation set
6. Save model to `backend/models/supply_model.pkl`

### Prediction Envelope Calculation

For each prediction:

```
y_hat = model.predict(features)  # Expected value
sigma = residual_std_dev  # From validation set
low_bound = y_hat - 1.0 * sigma
high_bound = y_hat + 1.0 * sigma
```

**Alternative:** Use quantile regression or prediction intervals if model supports it.

### Supply Status Classification

Convert numeric prediction to categorical label:

- **"Tight Supply":** `y_hat < threshold_low`
  - Threshold: e.g., 20th percentile of training target distribution
- **"Balanced":** `threshold_low <= y_hat < threshold_high`
  - Middle 60% of distribution
- **"Surplus":** `y_hat >= threshold_high`
  - Top 20th percentile

These thresholds should be computed from training data distribution.

### Feature Importance

After training, extract and log feature importance to understand model behavior:
- Which factors matter most?
- Weather vs events vs time-of-day
- Useful for model interpretation and future feature engineering

## Model Evaluation Metrics

- **RMSE (Root Mean Squared Error):** Overall prediction accuracy
- **MAE (Mean Absolute Error):** Average error magnitude
- **R² Score:** Variance explained
- **Coverage:** % of test cases where true value falls within [low, high] bounds (should be ~68% if using 1-sigma)

## Next Steps

After model training:
1. Generate model artifact (`supply_model.pkl`)
2. Save preprocessing parameters (scalers, encoders if needed)
3. Document feature importance
4. Create prediction function for API endpoint
