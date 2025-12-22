/**
 * ControlsPanel Component
 * Left panel with all user input controls for supply prediction
 */

import React from 'react';

export interface ControlState {
  zoneId: string;
  timestamp: string;
  activeDrivers: number;
  reserveBookings: number;
  onDemandRequests: number;
  weatherSeverity: number;
  eventDensity: number;
}

interface ControlsPanelProps {
  controls: ControlState;
  onChange: (controls: ControlState) => void;
  onPredict: () => void;
  loading: boolean;
}

const ControlsPanel: React.FC<ControlsPanelProps> = ({
  controls,
  onChange,
  onPredict,
  loading,
}) => {
  const handleChange = (field: keyof ControlState, value: string | number) => {
    onChange({ ...controls, [field]: value });
  };

  const formatDateTimeLocal = (isoString: string): string => {
    const date = new Date(isoString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const handleDateTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const localValue = e.target.value;
    const date = new Date(localValue);
    handleChange('timestamp', date.toISOString());
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 sm:p-5 space-y-4 sm:space-y-5 h-full w-full flex flex-col overflow-auto">
      <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-2 sm:mb-3">Input Parameters</h2>

      {/* Zone Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Zone
        </label>
        <select
          value={controls.zoneId}
          onChange={(e) => handleChange('zoneId', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="Z1">Z1</option>
          <option value="Z2">Z2</option>
          <option value="Z3">Z3</option>
          <option value="Z4">Z4</option>
          <option value="Z5">Z5</option>
        </select>
      </div>

      {/* DateTime Picker */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Pickup Time
        </label>
        <input
          type="datetime-local"
          value={formatDateTimeLocal(controls.timestamp)}
          onChange={handleDateTimeChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Weather Severity Slider */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Weather Severity: {controls.weatherSeverity === 0 ? 'Clear' : controls.weatherSeverity === 1 ? 'Rain' : 'Storm'}
        </label>
        <input
          type="range"
          min="0"
          max="2"
          value={controls.weatherSeverity}
          onChange={(e) => handleChange('weatherSeverity', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Clear</span>
          <span>Rain</span>
          <span>Storm</span>
        </div>
      </div>

      {/* Event Density Slider */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Event Density: {controls.eventDensity === 0 ? 'None' : controls.eventDensity === 1 ? 'Small' : 'Stadium'}
        </label>
        <input
          type="range"
          min="0"
          max="2"
          value={controls.eventDensity}
          onChange={(e) => handleChange('eventDensity', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>None</span>
          <span>Small</span>
          <span>Stadium</span>
        </div>
      </div>

      {/* Active Drivers */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Current Active Drivers
        </label>
        <input
          type="number"
          min="0"
          value={controls.activeDrivers}
          onChange={(e) => handleChange('activeDrivers', parseInt(e.target.value) || 0)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Reserve Bookings */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Reserve Bookings (Next 60 min)
        </label>
        <input
          type="number"
          min="0"
          value={controls.reserveBookings}
          onChange={(e) => handleChange('reserveBookings', parseInt(e.target.value) || 0)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* On-Demand Requests */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          On-Demand Requests (Last 60 min)
        </label>
        <input
          type="number"
          min="0"
          value={controls.onDemandRequests}
          onChange={(e) => handleChange('onDemandRequests', parseInt(e.target.value) || 0)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Predict Button */}
      <button
        onClick={onPredict}
        disabled={loading}
        className={`w-full py-3 px-4 rounded-md font-medium text-white transition-colors ${
          loading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
        }`}
      >
        {loading ? 'Predicting...' : 'Predict Supply'}
      </button>
    </div>
  );
};

export default ControlsPanel;

