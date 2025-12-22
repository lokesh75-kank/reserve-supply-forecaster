/**
 * ForecastCard Component
 * Right panel displaying prediction results and recommendations
 */

import React from 'react';
import type { PredictionResponse } from '../api';

interface ForecastCardProps {
  forecast: PredictionResponse | null;
  loading: boolean;
  error: string | null;
  timestamp?: string; // Input timestamp to calculate expected time
}

const ForecastCard: React.FC<ForecastCardProps> = ({ forecast, loading, error, timestamp }) => {
  const getStatusColor = (status: string): string => {
    if (status.includes('Tight')) {
      return 'bg-red-100 text-red-800 border-red-300';
    } else if (status.includes('Surplus')) {
      return 'bg-green-100 text-green-800 border-green-300';
    } else {
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    }
  };

  const getStatusBadgeColor = (status: string): string => {
    if (status.includes('Tight')) {
      return 'bg-red-500';
    } else if (status.includes('Surplus')) {
      return 'bg-green-500';
    } else {
      return 'bg-yellow-500';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 sm:p-5 flex items-center justify-center h-full w-full min-h-[300px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-3"></div>
          <p className="text-gray-600 text-sm">Predicting supply...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 sm:p-5 h-full w-full flex flex-col">
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <h3 className="text-red-800 font-semibold mb-1 text-sm sm:text-base">Error</h3>
          <p className="text-red-600 text-xs sm:text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!forecast) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 sm:p-5 flex items-center justify-center h-full w-full min-h-[300px]">
        <div className="text-center text-gray-500">
          <p className="text-base sm:text-lg">No prediction yet</p>
          <p className="text-xs sm:text-sm mt-2">Fill in the parameters and click "Predict Supply" to get started</p>
        </div>
      </div>
    );
  }

  // Format the pickup time selected by the user
  const getExpectedTime = (): string => {
    if (!timestamp) return 'selected pickup time';
    try {
      const pickupDate = new Date(timestamp);
      return pickupDate.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return 'selected pickup time';
    }
  };

  // Calculate bar widths for visualization
  const maxValue = Math.max(forecast.high_bound, forecast.expected_drivers_in_2h + 5);
  const lowWidth = (forecast.low_bound / maxValue) * 100;
  const expectedWidth = (forecast.expected_drivers_in_2h / maxValue) * 100;
  const highWidth = (forecast.high_bound / maxValue) * 100;

  return (
    <div className="bg-white rounded-lg shadow-md p-4 sm:p-5 space-y-4 sm:space-y-5 h-full w-full flex flex-col overflow-auto">
      <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-2 sm:mb-3">Supply Forecast</h2>

      {/* Expected Drivers - Compact Display */}
      <div className="text-center py-4 sm:py-5 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
        <p className="text-xs sm:text-sm text-gray-600 mb-1 sm:mb-2">Expected Drivers at {getExpectedTime()}</p>
        <p className="text-4xl sm:text-5xl md:text-6xl font-bold text-blue-700">{forecast.expected_drivers_in_2h.toFixed(1)}</p>
      </div>

      {/* Range Display */}
      <div className="space-y-2 sm:space-y-3">
        <h3 className="text-base sm:text-lg font-semibold text-gray-700">Prediction Range</h3>
        <div className="space-y-2">
          <div className="flex justify-between text-xs sm:text-sm text-gray-600">
            <span>Low: {forecast.low_bound.toFixed(1)}</span>
            <span>Expected: {forecast.expected_drivers_in_2h.toFixed(1)}</span>
            <span>High: {forecast.high_bound.toFixed(1)}</span>
          </div>
          
          {/* Visual Bar Chart */}
          <div className="relative h-6 sm:h-8 bg-gray-200 rounded-md overflow-hidden">
            {/* Low bound marker */}
            <div
              className="absolute left-0 top-0 h-full bg-gray-400 opacity-50"
              style={{ width: `${lowWidth}%` }}
            />
            {/* Expected value marker */}
            <div
              className="absolute left-0 top-0 h-full bg-blue-500"
              style={{ width: `${expectedWidth}%` }}
            />
            {/* High bound marker */}
            <div
              className="absolute left-0 top-0 h-full bg-gray-300 opacity-30"
              style={{ width: `${highWidth}%` }}
            />
            {/* Expected value indicator line */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-blue-700"
              style={{ left: `${expectedWidth}%` }}
            />
          </div>
        </div>
      </div>

      {/* Supply Status Badge */}
      <div>
        <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-1 sm:mb-2">Supply Status</h3>
        <div className={`inline-flex items-center px-3 sm:px-4 py-1.5 sm:py-2 rounded-full border text-sm sm:text-base ${getStatusColor(forecast.supply_status)}`}>
          <span className={`w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full mr-1.5 sm:mr-2 ${getStatusBadgeColor(forecast.supply_status)}`}></span>
          <span className="font-semibold">{forecast.supply_status}</span>
        </div>
      </div>

      {/* Recommendation */}
      <div>
        <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-1 sm:mb-2">Recommendation</h3>
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3 sm:p-4">
          <p className="text-blue-900 text-sm sm:text-base">{forecast.comment}</p>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-2 sm:gap-4 pt-3 sm:pt-4 border-t border-gray-200 mt-auto">
        <div className="text-center">
          <p className="text-xl sm:text-2xl font-bold text-gray-800">{forecast.low_bound.toFixed(0)}</p>
          <p className="text-xs text-gray-500 mt-1">Low Bound</p>
        </div>
        <div className="text-center">
          <p className="text-xl sm:text-2xl font-bold text-blue-600">{forecast.expected_drivers_in_2h.toFixed(0)}</p>
          <p className="text-xs text-gray-500 mt-1">Expected</p>
        </div>
        <div className="text-center">
          <p className="text-xl sm:text-2xl font-bold text-gray-800">{forecast.high_bound.toFixed(0)}</p>
          <p className="text-xs text-gray-500 mt-1">High Bound</p>
        </div>
      </div>
    </div>
  );
};

export default ForecastCard;

