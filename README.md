# Reserve Supply Forecaster

## Project Overview

**Reserve Supply Forecaster** is a predictive analytics application that forecasts future driver supply availability for Uber Reserve services. Given a future pickup time and location (zone), the system predicts the supply envelope (low/expected/high available drivers) under different conditions (weather, events, demand), enabling operations and product teams to make better Reserve pricing & dispatch decisions.

### One-Liner
Given a future pickup time and location (zone), forecast the supply envelope (low / expected / high available drivers) under different conditions (weather, events, demand), so operations/product can make better Reserve pricing & dispatch decisions.

## Problem Statement

Uber Reserve allows riders to book rides in advance, but operations teams need to predict driver availability 1-2 hours ahead to:
- Set appropriate pricing
- Decide whether to accept more Reserve bookings
- Trigger driver incentives when supply is tight
- Balance supply and demand proactively

This project addresses **scheduling under uncertainty** by providing reliable supply forecasts with confidence intervals.

## User Flow

1. **User Input:**
   - City zone (or area)
   - Future pickup time (e.g., 8:00 PM)
   - Forecast horizon (e.g., 2 hours ahead)
   - Scenario tweaks: weather, event flag, demand level

2. **System Output:**
   - Predicted available drivers: Low / Expected / High
   - Reliability label: "Tight Supply", "Balanced", "Surplus"
   - Suggested action: "Increase incentives", "OK to accept more Reserve bookings", etc.

## Tech Stack

### Backend / Model
- **Language:** Python
- **Libraries:** pandas, numpy, scikit-learn (or xgboost)
- **API Framework:** FastAPI
- **Model:** RandomForestRegressor or XGBoostRegressor

### Frontend UI
- **Framework:** React + TypeScript
- **Build Tool:** Vite (simpler setup)
- **Styling:** Material UI, Tailwind, or plain CSS

## Project Structure

```
uber-reserve-supply-forecaster/
├── backend/
│   ├── data/
│   │   └── synthetic_supply.csv          # Generated synthetic data (14,400 rows)
│   ├── models/
│   │   ├── supply_model.pkl               # Trained RandomForest model
│   │   ├── preprocessing_params.json      # Model parameters and thresholds
│   │   └── label_encoder.pkl              # Zone label encoder
│   ├── generate_data.py                   # Data generation module
│   ├── train_model.py                     # Model training script
│   ├── app.py                             # FastAPI app (to be implemented)
│   ├── requirements.txt                   # Python dependencies
│   └── venv/                              # Virtual environment (gitignored)
├── frontend/
│   ├── src/
│   │   ├── App.tsx                        # Main app component
│   │   ├── components/                    # React components (to be implemented)
│   │   └── api.ts                        # API client (to be implemented)
│   ├── package.json                       # Node dependencies
│   └── vite.config.ts                     # Vite configuration
├── docs/
│   ├── 01_DATA_AND_MODELING.md           # Data schema and modeling approach
│   ├── 02_BACKEND_API.md                 # API design documentation
│   ├── 03_FRONTEND_UI.md                 # Frontend UI design
│   └── 04_IMPLEMENTATION_STEPS.md        # Step-by-step implementation guide
└── README.md                              # This file
```

## Core Components

1. **Data Generation** - Synthetic historical supply data with realistic patterns
2. **Model Training** - Machine learning model to predict future driver supply
3. **Backend API** - FastAPI service exposing prediction endpoints
4. **Frontend UI** - React dashboard for scenario simulation and visualization

## Key Features

- **Zone-based Forecasting:** Predict supply at granular geographic level
- **Multi-factor Modeling:** Incorporates weather, events, demand, and temporal patterns
- **Uncertainty Quantification:** Provides confidence intervals (low/expected/high)
- **Scenario Simulation:** Test different conditions (weather, events) interactively
- **Actionable Insights:** Generates recommendations based on predicted supply status

## Project Plans

Detailed implementation plans for each component:

- **[Data & Modeling Plan](docs/01_DATA_AND_MODELING.md)** - Data schema, generation strategy, and model design
- **[Backend API Plan](docs/02_BACKEND_API.md)** - FastAPI endpoints, request/response formats
- **[Frontend UI Plan](docs/03_FRONTEND_UI.md)** - React components, user interface design
- **[Implementation Steps](docs/04_IMPLEMENTATION_STEPS.md)** - Step-by-step guide to build the project

## Quick Start

### Prerequisites
- Python 3.13+ (or Python 3.8+)
- Node.js 18+ and npm

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate data and train model:**
   ```bash
   python train_model.py
   ```
   This will:
   - Generate 14,400 rows of synthetic supply data
   - Train a RandomForest model
   - Save model artifacts to `models/` directory

5. **Start API server:**
   ```bash
   uvicorn app:app --reload
   ```
   API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Access UI:** Open http://localhost:5173 in browser

## Current Status

### ✅ Completed (Phase 1 & 2)
- [x] Project structure setup
- [x] Backend virtual environment and dependencies
- [x] Frontend React + TypeScript + Vite setup
- [x] Synthetic data generation (14,400 rows)
- [x] Model training (RandomForestRegressor)
- [x] Model evaluation (Validation & Test sets)
- [x] Model artifacts saved

### 🚧 In Progress (Phase 3)
- [ ] Backend API implementation (FastAPI endpoints)
- [ ] API testing and validation

### 📋 Planned (Phase 4 & 5)
- [ ] Frontend UI components
- [ ] API integration
- [ ] End-to-end testing
- [ ] UI polish and documentation

## Model Performance

The trained model achieves:
- **Test RMSE:** 2.39 drivers
- **Test MAE:** 1.91 drivers  
- **Test R²:** 0.9070 (90.70% variance explained)

**Feature Importance:**
- `active_drivers`: 67.27%
- `reserve_bookings_next_60min`: 18.83%
- `hour_of_day`: 7.94%
- Other features: < 3% each

## Deployment

This application can be deployed for free using various platforms:

### Option 1: GitHub Pages (Frontend) + Railway (Backend) - Free!

- **Frontend**: Deploy to GitHub Pages (completely free, uses GitHub Actions)
- **Backend**: Deploy to [Railway](https://railway.app) or [Render](https://render.com) (free tiers)

**Quick Setup:**
1. **Backend**: Deploy to Railway (see [DEPLOYMENT.md](DEPLOYMENT.md))
2. **Frontend**: 
   - Add `VITE_API_URL` secret in GitHub repository settings
   - Push to main branch - GitHub Actions will auto-deploy to GitHub Pages
   - Enable GitHub Pages in repository Settings → Pages

See [DEPLOYMENT_GITHUB.md](DEPLOYMENT_GITHUB.md) for GitHub Pages deployment guide.

### Option 2: Vercel (Frontend) + Railway (Backend)

- **Frontend**: Deploy to [Vercel](https://vercel.com) (free)
- **Backend**: Deploy to [Railway](https://railway.app) (free tier)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Important Note

**GitHub Pages can only host static frontend** - it cannot run backend APIs. You'll need Railway, Render, or similar for the FastAPI backend.

## Future Enhancements

- Real-time data integration
- Historical forecast accuracy tracking
- Multi-city support
- Advanced visualization (maps, time series charts)
- A/B testing framework for pricing decisions

