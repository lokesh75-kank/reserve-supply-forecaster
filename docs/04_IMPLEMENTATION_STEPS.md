# Implementation Steps

## Overview

This document provides a step-by-step guide to implement the Reserve Supply Forecaster project from scratch. Follow these steps in order to build the complete system.

## Phase 1: Project Setup

### Step 1.1: Initialize Repository Structure

```bash
mkdir -p backend/data backend/models
mkdir -p frontend/src/components
mkdir -p docs
```

### Step 1.2: Initialize Backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
touch requirements.txt
touch train_model.py
touch app.py
```

### Step 1.3: Initialize Frontend (React + Vite)

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
```

## Phase 2: Data Generation & Model Training

### Step 2.1: Create Requirements File

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

### Step 2.2: Implement Data Generation

**File:** `backend/train_model.py`

**Tasks:**
1. Import libraries (pandas, numpy, datetime)
2. Define zones list: `['Z1', 'Z2', 'Z3', 'Z4', 'Z5']`
3. Generate 30 days of timestamps at 15-min intervals
4. For each (zone, timestamp):
   - Compute base supply using time-of-day and day-of-week patterns
   - Add weather and event effects
   - Add random noise
   - Compute `active_drivers_t_plus_120` by looking ahead 2 hours
5. Create DataFrame with all columns
6. Save to `backend/data/synthetic_supply.csv`

**Key Functions to Implement:**
- `generate_base_supply(hour, day_of_week, zone)` - Base pattern
- `apply_weather_effect(supply, weather_severity)` - Modify supply
- `apply_event_effect(demand, event_density)` - Modify demand
- `compute_future_supply(...)` - Calculate target variable

### Step 2.3: Implement Model Training

**Continue in:** `backend/train_model.py`

**Tasks:**
1. Load CSV data
2. Feature engineering:
   - Extract `hour_of_day` and `day_of_week` from timestamp
   - Encode `zone_id` (label encoding or one-hot)
   - Select features: zone, hour, day, active_drivers, reserve_bookings, on_demand, weather, event
   - Target: `active_drivers_t_plus_120`
3. Train/validation/test split (70/20/10)
4. Train RandomForestRegressor or XGBoostRegressor
5. Evaluate on validation set (RMSE, MAE, R²)
6. Compute residual standard deviation from validation predictions
7. Compute supply status thresholds (20th, 80th percentiles of target)
8. Save model to `backend/models/supply_model.pkl`
9. Save preprocessing parameters (scaler, encoder, thresholds, sigma) to JSON or pickle

**Test:**
```bash
cd backend
python train_model.py
# Should generate data, train model, and save artifacts
```

## Phase 3: Backend API Implementation

### Step 3.1: Create FastAPI Application

**File:** `backend/app.py`

**Tasks:**
1. Import FastAPI, Pydantic, joblib, pandas, numpy
2. Load model and preprocessing parameters on startup
3. Define Pydantic models for request/response
4. Add CORS middleware
5. Implement `/health` endpoint
6. Implement `/predict_supply` endpoint:
   - Validate request
   - Preprocess features (match training format)
   - Run prediction
   - Calculate low/high bounds
   - Determine supply status
   - Generate recommendation comment
   - Return response
7. Add error handling

**Key Functions:**
- `load_model()` - Load from pickle file
- `preprocess_features(request)` - Convert request to model input
- `get_supply_status(prediction, thresholds)` - Classify status
- `get_recommendation(status)` - Generate comment

**Test:**
```bash
cd backend
uvicorn app:app --reload
# Test with curl or Postman
curl -X POST "http://localhost:8000/predict_supply" \
  -H "Content-Type: application/json" \
  -d '{"timestamp": "2025-01-10T18:00:00", "zone_id": "Z1", ...}'
```

### Step 3.2: Verify API Endpoints

- Test `/health` returns 200
- Test `/predict_supply` with valid request
- Test `/predict_supply` with invalid data (should return 400)
- Verify CORS headers allow frontend origin

## Phase 4: Frontend Implementation

### Step 4.1: Setup Styling

**Option A: Tailwind CSS**
```bash
cd frontend
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Update `tailwind.config.js`:
```js
content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
```

**Option B: Material UI**
```bash
npm install @mui/material @emotion/react @emotion/styled
```

### Step 4.2: Create API Client

**File:** `frontend/src/api.ts`

**Tasks:**
1. Define TypeScript interfaces for request/response
2. Implement `predictSupply()` function using fetch
3. Add error handling

### Step 4.3: Create ControlsPanel Component

**File:** `frontend/src/components/ControlsPanel.tsx`

**Tasks:**
1. Define props interface (onChange handlers)
2. Create form inputs:
   - Zone dropdown
   - DateTime picker
   - Weather slider (0-2)
   - Event slider (0-2)
   - Number inputs for drivers, bookings, requests
3. Add labels and styling
4. Emit changes to parent via callbacks

### Step 4.4: Create ForecastCard Component

**File:** `frontend/src/components/ForecastCard.tsx`

**Tasks:**
1. Define props interface (forecast data, loading, error)
2. Display expected drivers (large number)
3. Display low/expected/high range
4. Show supply status badge (color-coded)
5. Display recommendation comment
6. Optional: Simple bar chart visualization
7. Handle loading and error states

### Step 4.5: Create Main App Component

**File:** `frontend/src/App.tsx`

**Tasks:**
1. Import components and API client
2. Set up state:
   - Control values (zone, time, inputs)
   - Forecast result
   - Loading state
   - Error state
3. Implement `handlePredict()` function
4. Render layout:
   - Left: ControlsPanel
   - Right: ForecastCard
5. Add error display
6. Style with flexbox or grid layout

### Step 4.6: Test Frontend

```bash
cd frontend
npm run dev
# Open http://localhost:5173
# Test with different inputs
# Verify API calls work
```

## Phase 5: Integration & Testing

### Step 5.1: End-to-End Testing

**Tasks:**
1. Start backend: `cd backend && uvicorn app:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Test scenarios:
   - Default inputs → get prediction
   - Change weather to storm → verify prediction changes
   - Change event density → verify impact
   - Test different zones
   - Test edge cases (0 drivers, high demand)

### Step 5.2: UI Polish

**Tasks:**
1. Improve styling and spacing
2. Add loading spinners
3. Add error message styling
4. Ensure responsive design (mobile-friendly)
5. Add tooltips or help text for inputs

### Step 5.3: Documentation

**Tasks:**
1. Update README.md with setup instructions
2. Add comments to code
3. Document any assumptions or limitations

## Phase 6: Optional Enhancements

### Step 6.1: Add Visualization

- Implement bar chart for low/expected/high bounds
- Add time series chart showing supply over time (if multiple predictions)

### Step 6.2: Add Model Info Endpoint

- Implement `/model_info` endpoint
- Display feature importance in frontend

### Step 6.3: Add Input Validation

- Frontend validation before API call
- Better error messages

## Checklist

- [ ] Project structure created
- [ ] Backend requirements installed
- [ ] Data generation script working
- [ ] Model trained and saved
- [ ] FastAPI endpoints implemented
- [ ] API tested with curl/Postman
- [ ] Frontend project initialized
- [ ] API client implemented
- [ ] ControlsPanel component built
- [ ] ForecastCard component built
- [ ] App component integrated
- [ ] End-to-end flow working
- [ ] Styling polished
- [ ] README updated

## Estimated Time

- Phase 1 (Setup): 30 minutes
- Phase 2 (Data & Model): 2-3 hours
- Phase 3 (Backend API): 2-3 hours
- Phase 4 (Frontend): 3-4 hours
- Phase 5 (Integration): 1-2 hours
- **Total: 8-12 hours**

## Troubleshooting

### Backend Issues

- **Model not found:** Ensure `train_model.py` runs successfully first
- **Import errors:** Check virtual environment is activated
- **CORS errors:** Verify CORS middleware allows frontend origin

### Frontend Issues

- **API call fails:** Check backend is running and URL is correct
- **TypeScript errors:** Ensure types match API response structure
- **Build errors:** Check all dependencies are installed

### Data/Model Issues

- **Poor predictions:** Adjust data generation patterns or model hyperparameters
- **NaN predictions:** Check feature preprocessing matches training

