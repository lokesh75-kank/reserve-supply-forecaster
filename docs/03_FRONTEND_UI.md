# Frontend UI Plan

## Overview

This document outlines the React + TypeScript frontend implementation for the Reserve Supply Forecaster dashboard. The UI allows users to simulate different scenarios and view supply forecasts.

## Technology Stack

- **Framework:** React 18+
- **Language:** TypeScript
- **Build Tool:** Vite
- **HTTP Client:** fetch API or axios
- **Styling:** Tailwind CSS (or Material UI, or plain CSS)
- **State Management:** React useState (simple app, no need for Redux)

## UI Layout

### Main Screen Structure

```
┌─────────────────────────────────────────────────────────┐
│                    Reserve Supply Forecaster            │
├──────────────────────┬──────────────────────────────────┤
│                      │                                  │
│   Controls Panel     │     Forecast Output Panel       │
│   (Left Side)        │     (Right Side)                 │
│                      │                                  │
│   - Zone Selector    │     - Expected Drivers: 27      │
│   - Time Picker      │     - Range: 22 - 33            │
│   - Weather Slider   │     - Status Badge: [Tight]     │
│   - Event Slider     │     - Recommendation Text       │
│   - Driver Inputs    │     - Bar Chart (optional)      │
│   - Predict Button   │                                  │
│                      │                                  │
└──────────────────────┴──────────────────────────────────┘
```

## Components

### 1. App.tsx (Main Container)

**Purpose:** Root component, manages API state and orchestrates child components.

**Responsibilities:**
- State management for form inputs
- API call handling
- Error state management
- Loading state management

### 2. ControlsPanel.tsx

**Purpose:** Left panel with all user input controls.

**Input Fields:**

1. **Zone Selector**
   - Type: Dropdown/Select
   - Options: Z1, Z2, Z3, Z4, Z5
   - Default: Z1

2. **Pickup Time Picker**
   - Type: DateTime picker or simple time input
   - Default: Current time + 2 hours
   - Format: ISO 8601 timestamp

3. **Weather Severity Slider**
   - Type: Range slider (0-2)
   - Labels: 0 = Clear, 1 = Rain, 2 = Storm
   - Default: 0

4. **Event Density Slider**
   - Type: Range slider (0-2)
   - Labels: 0 = None, 1 = Small, 2 = Stadium
   - Default: 0

5. **Current Active Drivers**
   - Type: Number input
   - Min: 0
   - Default: 20

6. **Reserve Bookings (Next 60 min)**
   - Type: Number input
   - Min: 0
   - Default: 5

7. **On-Demand Requests (Last 60 min)**
   - Type: Number input
   - Min: 0
   - Default: 30

8. **Predict Button**
   - Triggers API call
   - Shows loading state
   - Disabled during loading

**State Structure:**
```typescript
interface ControlState {
  zoneId: string;
  timestamp: string; // ISO format
  activeDrivers: number;
  reserveBookings: number;
  onDemandRequests: number;
  weatherSeverity: number;
  eventDensity: number;
}
```

### 3. ForecastCard.tsx

**Purpose:** Right panel displaying prediction results.

**Display Elements:**

1. **Expected Drivers**
   - Large number display
   - Label: "Expected drivers in 2 hours"

2. **Range Display**
   - Format: "Low: X | Expected: Y | High: Z"
   - Or: "Range: X - Z (Expected: Y)"

3. **Supply Status Badge**
   - Color-coded badge
   - Options: "Tight Supply" (red), "Balanced" (yellow/green), "Surplus" (green)

4. **Recommendation Text**
   - Text box showing backend comment
   - Styled as callout/alert

5. **Optional: Bar Chart**
   - Visual representation of low/expected/high
   - Simple horizontal bars or vertical bars
   - Could use a simple charting library (recharts, chart.js) or CSS bars

**Props:**
```typescript
interface ForecastData {
  expected_drivers_in_2h: number;
  low_bound: number;
  high_bound: number;
  supply_status: "Tight" | "Balanced" | "Surplus";
  comment: string;
}
```

### 4. api.ts (API Client)

**Purpose:** Helper functions to call FastAPI backend.

**Functions:**
```typescript
// api.ts
const API_BASE_URL = 'http://localhost:8000';

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
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}
```

## Styling Approach

### Option 1: Tailwind CSS (Recommended)

**Pros:** Fast development, utility-first, modern

**Setup:**
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Example Component:**
```tsx
<div className="flex flex-col space-y-4 p-6 bg-white rounded-lg shadow-md">
  <label className="text-sm font-medium">Zone</label>
  <select className="border rounded px-3 py-2">
    {/* options */}
  </select>
</div>
```

### Option 2: Material UI

**Pros:** Pre-built components, professional look

**Setup:**
```bash
npm install @mui/material @emotion/react @emotion/styled
```

### Option 3: Plain CSS

**Pros:** No dependencies, full control

**Cons:** More manual work

## Component State Management

**App.tsx State:**
```typescript
const [controls, setControls] = useState<ControlState>({
  zoneId: 'Z1',
  timestamp: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
  activeDrivers: 20,
  reserveBookings: 5,
  onDemandRequests: 30,
  weatherSeverity: 0,
  eventDensity: 0,
});

const [forecast, setForecast] = useState<PredictionResponse | null>(null);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

**Handle Predict:**
```typescript
const handlePredict = async () => {
  setLoading(true);
  setError(null);
  
  try {
    const response = await predictSupply({
      timestamp: controls.timestamp,
      zone_id: controls.zoneId,
      active_drivers: controls.activeDrivers,
      reserve_bookings_next_60min: controls.reserveBookings,
      on_demand_requests_last_60min: controls.onDemandRequests,
      weather_severity: controls.weatherSeverity,
      event_density: controls.eventDensity,
    });
    
    setForecast(response);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Prediction failed');
  } finally {
    setLoading(false);
  }
};
```

## Error Handling

- Display error message in ForecastCard or separate Error component
- Show network errors clearly
- Handle API validation errors (400) vs server errors (500)

## Loading States

- Disable Predict button during loading
- Show spinner or "Loading..." text
- Optional: skeleton loader for ForecastCard

## File Structure

```
frontend/
├── src/
│   ├── App.tsx                 # Main container
│   ├── main.tsx                # Entry point
│   ├── api.ts                  # API client
│   ├── components/
│   │   ├── ControlsPanel.tsx   # Input controls
│   │   ├── ForecastCard.tsx    # Output display
│   │   └── LoadingSpinner.tsx  # Optional loading component
│   ├── types.ts                # TypeScript interfaces
│   └── styles.css              # Global styles
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Package.json Dependencies

```json
{
  "name": "reserve-supply-forecaster-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.0",
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16"
  }
}
```

## Running the Frontend

### Development
```bash
cd frontend
npm install
npm run dev
```

### Build for Production
```bash
npm run build
npm run preview
```

