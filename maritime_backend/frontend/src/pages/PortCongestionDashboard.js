import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PortCongestionDashboard = () => {
  const [ports, setPorts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPortData();
  }, []);

  const fetchPortData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/ports/congestion/');
      setPorts(response.data);
    } catch (err) {
      console.error('Error fetching port data:', err);
      // Use mock data if API fails
      setPorts(mockPortData);
    } finally {
      setLoading(false);
    }
  };

  const getCongestionColor = (score) => {
    if (score >= 8) return 'bg-red-100 text-red-800';
    if (score >= 6) return 'bg-yellow-100 text-yellow-800';
    if (score >= 4) return 'bg-blue-100 text-blue-800';
    return 'bg-green-100 text-green-800';
  };

  const getCongestionLabel = (score) => {
    if (score >= 8) return 'Critical';
    if (score >= 6) return 'High';
    if (score >= 4) return 'Moderate';
    return 'Low';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Port Congestion Dashboard</h1>
        <p className="text-gray-600">Monitor port congestion levels and traffic statistics</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Total Ports</h3>
          <p className="text-3xl font-bold text-blue-600">{ports.length}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Critical Congestion</h3>
          <p className="text-3xl font-bold text-red-600">
            {ports.filter(port => port.congestion_score >= 8).length}
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Total Arrivals</h3>
          <p className="text-3xl font-bold text-green-600">
            {ports.reduce((sum, port) => sum + port.arrivals, 0)}
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Total Departures</h3>
          <p className="text-3xl font-bold text-purple-600">
            {ports.reduce((sum, port) => sum + port.departures, 0)}
          </p>
        </div>
      </div>

      {/* Ports Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Port Congestion Status</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Port
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Country
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Congestion Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Wait Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Arrivals
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Departures
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {ports.map((port, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{port.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{port.country}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCongestionColor(port.congestion_score)}`}>
                      {port.congestion_score.toFixed(1)} - {getCongestionLabel(port.congestion_score)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{port.avg_wait_time.toFixed(1)} hrs</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{port.arrivals}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{port.departures}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Mock data for when API is not available
const mockPortData = [
  {
    name: "Port of Dubai",
    country: "UAE",
    congestion_score: 7.2,
    avg_wait_time: 4.5,
    arrivals: 45,
    departures: 42
  },
  {
    name: "Port of Singapore",
    country: "Singapore",
    congestion_score: 8.9,
    avg_wait_time: 6.8,
    arrivals: 78,
    departures: 73
  },
  {
    name: "Port of Rotterdam",
    country: "Netherlands",
    congestion_score: 5.4,
    avg_wait_time: 2.1,
    arrivals: 56,
    departures: 59
  },
  {
    name: "Port of Shanghai",
    country: "China",
    congestion_score: 9.1,
    avg_wait_time: 8.2,
    arrivals: 92,
    departures: 87
  },
  {
    name: "Port of Los Angeles",
    country: "USA",
    congestion_score: 6.7,
    avg_wait_time: 3.9,
    arrivals: 34,
    departures: 38
  }
];

export default PortCongestionDashboard;