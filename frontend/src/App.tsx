/**
 * Main App Component
 * Reserve Supply Forecaster Dashboard
 */

import { useState } from 'react';
import ControlsPanel from './components/ControlsPanel';
import type { ControlState } from './components/ControlsPanel';
import ForecastCard from './components/ForecastCard';
import AnalyticsCard from './components/AnalyticsCard';
import { predictSupply, analyzePrediction } from './api';
import type { PredictionResponse, PredictionAnalysisResponse } from './api';
import './App.css';

function App() {
  // Initialize controls with default values (2 hours from now)
  const getDefaultTimestamp = (): string => {
    const date = new Date();
    date.setHours(date.getHours() + 2);
    return date.toISOString();
  };

  const [controls, setControls] = useState<ControlState>({
    zoneId: 'Z1',
    timestamp: getDefaultTimestamp(),
    activeDrivers: 20,
    reserveBookings: 5,
    onDemandRequests: 30,
    weatherSeverity: 0,
    eventDensity: 0,
  });

  const [forecast, setForecast] = useState<PredictionResponse | null>(null);
  const [analysis, setAnalysis] = useState<PredictionAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);

    const request = {
      timestamp: controls.timestamp,
      zone_id: controls.zoneId,
      active_drivers: controls.activeDrivers,
      reserve_bookings_next_60min: controls.reserveBookings,
      on_demand_requests_last_60min: controls.onDemandRequests,
      weather_severity: controls.weatherSeverity,
      event_density: controls.eventDensity,
    };

    try {
      // Call both endpoints in parallel for better performance
      const [predictionResponse, analysisResponse] = await Promise.all([
        predictSupply(request),
        analyzePrediction(request),
      ]);

      setForecast(predictionResponse);
      setAnalysis(analysisResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
      setForecast(null);
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Compact Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10 w-full">
        <div className="w-full px-3 sm:px-4 lg:px-6 py-3 sm:py-4">
          <div className="max-w-[1920px] mx-auto">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
              Reserve Supply Forecaster
            </h1>
            <p className="text-gray-600 text-xs sm:text-sm mt-0.5">
              Predict future driver supply availability for Uber Reserve services
            </p>
          </div>
        </div>
      </header>

      {/* Main Content - Flex grow to fill screen */}
      <main className="flex-1 w-full px-2 sm:px-3 md:px-4 lg:px-6 py-3 sm:py-4 overflow-auto">
        <div className="max-w-[1920px] mx-auto h-full">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4 lg:gap-6 h-full">
            {/* Left Panel - Controls */}
            <div className="min-h-0 flex flex-col">
              <ControlsPanel
                controls={controls}
                onChange={setControls}
                onPredict={handlePredict}
                loading={loading}
              />
            </div>

            {/* Middle Panel - Forecast */}
            <div className="min-h-0 flex flex-col">
              <ForecastCard
                forecast={forecast}
                loading={loading}
                error={error}
                timestamp={controls.timestamp}
              />
            </div>

            {/* Right Panel - Analytics */}
            <div className="min-h-0 flex flex-col md:col-span-2 xl:col-span-1">
              <AnalyticsCard
                analysis={analysis}
                loading={loading}
              />
            </div>
          </div>
        </div>
      </main>

      {/* Compact Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto w-full">
        <div className="w-full px-3 sm:px-4 lg:px-6 py-2">
          <div className="max-w-[1920px] mx-auto">
            <p className="text-center text-xs text-gray-500">
              Reserve Supply Forecaster API v1.0.0
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
