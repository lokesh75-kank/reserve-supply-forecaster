/**
 * AnalyticsCard Component
 * Displays real-time analytics: feature contributions, confidence, similar cases, and anomalies
 */

import React from 'react';
import type { PredictionAnalysisResponse } from '../api';

interface AnalyticsCardProps {
  analysis: PredictionAnalysisResponse | null;
  loading: boolean;
}

const AnalyticsCard: React.FC<AnalyticsCardProps> = ({ analysis, loading }) => {
  const getConfidenceColor = (level: string): string => {
    if (level === 'High') {
      return 'bg-green-100 text-green-800 border-green-300';
    } else if (level === 'Medium') {
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    } else {
      return 'bg-red-100 text-red-800 border-red-300';
    }
  };

  const getConfidenceBadgeColor = (level: string): string => {
    if (level === 'High') {
      return 'bg-green-500';
    } else if (level === 'Medium') {
      return 'bg-yellow-500';
    } else {
      return 'bg-red-500';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 sm:p-5 h-full w-full flex flex-col">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-3 sm:mb-4">Real-Time Analytics</h2>
        <div className="flex items-center justify-center py-6 sm:py-8 flex-1">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
            <p className="text-gray-600 text-sm">Analyzing prediction...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 sm:p-5 h-full w-full flex flex-col">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-3 sm:mb-4">Real-Time Analytics</h2>
        <div className="text-center text-gray-500 py-6 sm:py-8 flex-1 flex items-center justify-center">
          <p className="text-sm">Analytics will appear here after prediction</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 sm:p-5 space-y-4 sm:space-y-5 h-full w-full flex flex-col overflow-auto">
      <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-2 sm:mb-3">Real-Time Analytics</h2>

      {/* Confidence Score */}
      <div>
        <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-1.5 sm:mb-2">Prediction Confidence</h3>
        <div className="flex items-center gap-2 sm:gap-4">
          <div className={`inline-flex items-center px-3 sm:px-4 py-1.5 sm:py-2 rounded-full border text-xs sm:text-sm ${getConfidenceColor(analysis.confidence_level)}`}>
            <span className={`w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full mr-1.5 sm:mr-2 ${getConfidenceBadgeColor(analysis.confidence_level)}`}></span>
            <span className="font-semibold">{analysis.confidence_level}</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="w-full bg-gray-200 rounded-full h-2 sm:h-3">
              <div
                className={`h-2 sm:h-3 rounded-full transition-all ${
                  analysis.confidence_level === 'High' ? 'bg-green-500' :
                  analysis.confidence_level === 'Medium' ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${analysis.confidence_score}%` }}
              />
            </div>
          </div>
          <span className="text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">{analysis.confidence_score}%</span>
        </div>
      </div>

      {/* Feature Contributions */}
      <div>
        <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2 sm:mb-3">Feature Contributions</h3>
        <div className="space-y-2">
          {analysis.feature_contributions.slice(0, 5).map((feature, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between items-center text-sm">
                <span className="font-medium text-gray-700">
                  {feature.feature_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
                <div className="flex items-center gap-2">
                  <span className={`font-semibold ${feature.contribution >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {feature.contribution >= 0 ? '+' : ''}{feature.contribution.toFixed(1)}
                  </span>
                  <span className="text-gray-500 text-xs">({feature.percentage.toFixed(1)}%)</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    feature.contribution >= 0 ? 'bg-green-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(100, Math.abs(feature.percentage))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Similar Cases */}
      {analysis.similar_cases.length > 0 && (
        <div>
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-2 sm:mb-3">Similar Historical Cases</h3>
          <div className="space-y-2 max-h-40 sm:max-h-48 overflow-y-auto">
            {analysis.similar_cases.map((case_, idx) => (
              <div
                key={idx}
                className="bg-gray-50 border border-gray-200 rounded-md p-3 text-sm"
              >
                <div className="flex justify-between items-start mb-1">
                  <div>
                    <span className="font-semibold text-gray-800">{case_.zone_id}</span>
                    <span className="text-gray-500 ml-2">
                      {new Date(case_.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {(case_.similarity_score * 100).toFixed(0)}% similar
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                  <div>
                    <span className="text-gray-500">Active:</span>
                    <span className="font-semibold ml-1">{case_.active_drivers}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Predicted:</span>
                    <span className="font-semibold ml-1">{case_.predicted_drivers.toFixed(1)}</span>
                  </div>
                  {case_.actual_drivers !== null && case_.actual_drivers !== undefined && (
                    <div>
                      <span className="text-gray-500">Actual:</span>
                      <span className="font-semibold ml-1">{case_.actual_drivers.toFixed(1)}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Anomaly Flags */}
      {analysis.anomaly_reasons.length > 0 && (
        <div className="mt-auto">
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-1.5 sm:mb-2">Anomaly Detection</h3>
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 sm:p-4">
            <div className="flex items-start">
              <span className="text-yellow-600 text-lg sm:text-xl mr-2">⚠️</span>
              <div className="flex-1 min-w-0">
                <p className="text-yellow-800 font-semibold mb-1 sm:mb-2 text-sm sm:text-base">Unusual patterns detected:</p>
                <ul className="list-disc list-inside space-y-0.5 sm:space-y-1">
                  {analysis.anomaly_reasons.map((reason, idx) => (
                    <li key={idx} className="text-yellow-700 text-xs sm:text-sm">{reason}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Anomaly Flags Summary */}
      {analysis.anomaly_reasons.length === 0 && (
        <div className="mt-auto">
          <h3 className="text-base sm:text-lg font-semibold text-gray-700 mb-1.5 sm:mb-2">Anomaly Detection</h3>
          <div className="bg-green-50 border border-green-200 rounded-md p-3 sm:p-4">
            <div className="flex items-center">
              <span className="text-green-600 text-lg sm:text-xl mr-2">✅</span>
              <p className="text-green-800 font-semibold text-xs sm:text-sm">No anomalies detected - prediction looks normal</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsCard;

