import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { useAuth } from '../context/AuthContext';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

// API base URL from environment variable
const API_BASE_URL = process.env.REACT_APP_API_BASE || 'https://maritime-backend-q150.onrender.com';

// Chart.js default options for consistent styling
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        color: '#e5e7eb',
        font: {
          size: 12
        }
      }
    },
    tooltip: {
      backgroundColor: 'rgba(31, 41, 55, 0.9)',
      titleColor: '#f3f4f6',
      bodyColor: '#e5e7eb',
      borderColor: '#6b7280',
      borderWidth: 1
    }
  },
  scales: {
    x: {
      ticks: {
        color: '#9ca3af',
        font: {
          size: 11
        }
      },
      grid: {
        color: 'rgba(107, 114, 128, 0.2)'
      }
    },
    y: {
      ticks: {
        color: '#9ca3af',
        font: {
          size: 11
        }
      },
      grid: {
        color: 'rgba(107, 114, 128, 0.2)'
      }
    }
  }
};

// Mock analytics data for fallback
const mockAnalyticsData = {
  kpis: {
    efficiency: 87.3,
    onTimeDelivery: 92.1,
    fuelEfficiency: 78.5,
    costSavings: 2340000,
    avgTransitTime: 23.4,
    routeOptimization: 94.2,
    incidentRate: 0.12,
    customerSatisfaction: 4.6
  },
  trends: {
    efficiency: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      data: [82.1, 84.3, 86.2, 85.8, 87.1, 87.3]
    },
    delays: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      data: [12.3, 10.8, 9.2, 8.7, 7.9, 7.9]
    },
    costs: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      data: [1850000, 1920000, 2100000, 2180000, 2250000, 2340000]
    },
    fuelConsumption: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      data: [145.2, 142.8, 138.9, 136.4, 134.1, 132.7]
    }
  },
  routeAnalysis: {
    topRoutes: [
      { route: 'Asia-Europe', efficiency: 94.2, volume: 1250, savings: 890000 },
      { route: 'Trans-Pacific', efficiency: 89.7, volume: 980, savings: 720000 },
      { route: 'Atlantic', efficiency: 91.3, volume: 750, savings: 540000 },
      { route: 'Middle East', efficiency: 86.8, volume: 620, savings: 380000 }
    ],
    vesselTypes: {
      labels: ['Container', 'Tanker', 'Bulk Carrier', 'LNG Carrier', 'Other'],
      data: [45, 25, 15, 10, 5]
    }
  },
  operationalMetrics: {
    portPerformance: [
      { port: 'Singapore', efficiency: 96.2, avgWaitTime: 2.1, throughput: 3200 },
      { port: 'Rotterdam', efficiency: 94.8, avgWaitTime: 2.8, throughput: 2850 },
      { port: 'Shanghai', efficiency: 92.1, avgWaitTime: 3.2, throughput: 4100 },
      { port: 'Los Angeles', efficiency: 89.3, avgWaitTime: 4.1, throughput: 2200 }
    ],
    alerts: {
      labels: ['Critical', 'High', 'Medium', 'Low'],
      data: [3, 12, 28, 45],
      colors: ['#dc2626', '#f59e0b', '#eab308', '#22c55e']
    }
  }
};

const AnalyticsDashboard = ({ userRole = 'OPERATOR' }) => {
  const { token } = useAuth();
  const [analyticsData, setAnalyticsData] = useState(mockAnalyticsData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedTimeRange, setSelectedTimeRange] = useState('6M'); // 1M, 3M, 6M, 1Y

  // Fetch analytics data from backend
  const fetchAnalyticsData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const endpoints = {
        kpis: `${API_BASE_URL}/api/analytics/kpis/?period=${selectedTimeRange}`,
        trends: `${API_BASE_URL}/api/analytics/trends/?period=${selectedTimeRange}`,
        routes: `${API_BASE_URL}/api/analytics/routes/?period=${selectedTimeRange}`,
        operations: `${API_BASE_URL}/api/analytics/operations/?period=${selectedTimeRange}`
      };

      const responses = await Promise.allSettled([
        fetch(endpoints.kpis, {
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          }
        }),
        fetch(endpoints.trends, {
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          }
        }),
        fetch(endpoints.routes, {
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          }
        }),
        fetch(endpoints.operations, {
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          }
        })
      ]);

      const newAnalyticsData = { ...mockAnalyticsData };

      // Process KPIs
      if (responses[0].status === 'fulfilled' && responses[0].value.ok) {
        const kpisData = await responses[0].value.json();
        newAnalyticsData.kpis = { ...newAnalyticsData.kpis, ...kpisData };
      }

      // Process trends
      if (responses[1].status === 'fulfilled' && responses[1].value.ok) {
        const trendsData = await responses[1].value.json();
        newAnalyticsData.trends = { ...newAnalyticsData.trends, ...trendsData };
      }

      // Process route analysis
      if (responses[2].status === 'fulfilled' && responses[2].value.ok) {
        const routesData = await responses[2].value.json();
        newAnalyticsData.routeAnalysis = { ...newAnalyticsData.routeAnalysis, ...routesData };
      }

      // Process operational metrics
      if (responses[3].status === 'fulfilled' && responses[3].value.ok) {
        const operationsData = await responses[3].value.json();
        newAnalyticsData.operationalMetrics = { ...newAnalyticsData.operationalMetrics, ...operationsData };
      }

      setAnalyticsData(newAnalyticsData);
      setLastUpdate(new Date());
      console.log('Analytics data updated successfully');

    } catch (err) {
      console.warn('Failed to fetch analytics data, using mock data:', err.message);
      setError(`Failed to load analytics: ${err.message}`);
      // Keep existing mock data on error
    } finally {
      setLoading(false);
    }
  }, [token, selectedTimeRange]);

  // Initialize analytics data
  useEffect(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  // Chart data configurations
  const efficiencyTrendData = useMemo(() => ({
    labels: analyticsData.trends.efficiency.labels,
    datasets: [
      {
        label: 'Efficiency %',
        data: analyticsData.trends.efficiency.data,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  }), [analyticsData.trends.efficiency]);

  const delayTrendData = useMemo(() => ({
    labels: analyticsData.trends.delays.labels,
    datasets: [
      {
        label: 'Delay Rate %',
        data: analyticsData.trends.delays.data,
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  }), [analyticsData.trends.delays]);

  const costSavingsData = useMemo(() => ({
    labels: analyticsData.trends.costs.labels,
    datasets: [
      {
        label: 'Cost Savings ($)',
        data: analyticsData.trends.costs.data,
        backgroundColor: '#10b981',
        borderColor: '#059669',
        borderWidth: 1
      }
    ]
  }), [analyticsData.trends.costs]);

  const vesselTypesData = useMemo(() => ({
    labels: analyticsData.routeAnalysis.vesselTypes.labels,
    datasets: [
      {
        data: analyticsData.routeAnalysis.vesselTypes.data,
        backgroundColor: [
          '#3b82f6',
          '#ef4444',
          '#f59e0b',
          '#10b981',
          '#8b5cf6'
        ],
        borderColor: '#374151',
        borderWidth: 2
      }
    ]
  }), [analyticsData.routeAnalysis.vesselTypes]);

  const alertsData = useMemo(() => ({
    labels: analyticsData.operationalMetrics.alerts.labels,
    datasets: [
      {
        data: analyticsData.operationalMetrics.alerts.data,
        backgroundColor: analyticsData.operationalMetrics.alerts.colors,
        borderColor: '#374151',
        borderWidth: 2
      }
    ]
  }), [analyticsData.operationalMetrics.alerts]);

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format percentage
  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  if (loading && !analyticsData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-gray-300">Loading analytics...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Time Range Selector */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-blue-400">
            {userRole === 'ANALYST' ? 'Advanced Analytics' : 'Operational Analytics'}
          </h2>
          <p className="text-gray-400 text-sm">
            Last updated: {lastUpdate.toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-4">
          {error && (
            <button
              onClick={fetchAnalyticsData}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
            >
              Retry
            </button>
          )}
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1M">Last Month</option>
            <option value="3M">Last 3 Months</option>
            <option value="6M">Last 6 Months</option>
            <option value="1Y">Last Year</option>
          </select>
          {loading && (
            <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-4">
          <div className="text-red-400 font-medium">Analytics Error</div>
          <div className="text-red-300 text-sm mt-1">{error}</div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <div className="text-2xl font-bold text-blue-400">
            {formatPercentage(analyticsData.kpis.efficiency)}
          </div>
          <div className="text-sm text-gray-300">Overall Efficiency</div>
          <div className="text-xs text-green-400 mt-1">↗ +2.1% vs last period</div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <div className="text-2xl font-bold text-green-400">
            {formatPercentage(analyticsData.kpis.onTimeDelivery)}
          </div>
          <div className="text-sm text-gray-300">On-Time Delivery</div>
          <div className="text-xs text-green-400 mt-1">↗ +1.8% vs last period</div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <div className="text-2xl font-bold text-purple-400">
            {formatCurrency(analyticsData.kpis.costSavings)}
          </div>
          <div className="text-sm text-gray-300">Cost Savings</div>
          <div className="text-xs text-green-400 mt-1">↗ +12.3% vs last period</div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <div className="text-2xl font-bold text-yellow-400">
            {analyticsData.kpis.avgTransitTime}h
          </div>
          <div className="text-sm text-gray-300">Avg Transit Time</div>
          <div className="text-xs text-red-400 mt-1">↘ -0.8h vs last period</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Efficiency Trend */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Efficiency Trend</h3>
          <div className="h-64">
            <Line data={efficiencyTrendData} options={chartOptions} />
          </div>
        </div>

        {/* Delay Trend */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Delay Rate Trend</h3>
          <div className="h-64">
            <Line data={delayTrendData} options={chartOptions} />
          </div>
        </div>

        {/* Cost Savings */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Monthly Cost Savings</h3>
          <div className="h-64">
            <Bar data={costSavingsData} options={chartOptions} />
          </div>
        </div>

        {/* Vessel Types Distribution */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Fleet Composition</h3>
          <div className="h-64">
            <Doughnut 
              data={vesselTypesData} 
              options={{
                ...chartOptions,
                scales: undefined,
                plugins: {
                  ...chartOptions.plugins,
                  legend: {
                    ...chartOptions.plugins.legend,
                    position: 'right'
                  }
                }
              }} 
            />
          </div>
        </div>
      </div>

      {/* Role-specific sections */}
      {userRole === 'ANALYST' && (
        <>
          {/* Advanced Analytics for Analysts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Route Performance */}
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">Top Route Performance</h3>
              <div className="space-y-3">
                {analyticsData.routeAnalysis.topRoutes.map((route, index) => (
                  <div key={route.route} className="flex justify-between items-center p-3 bg-gray-700 rounded">
                    <div>
                      <div className="font-medium text-white">{route.route}</div>
                      <div className="text-sm text-gray-400">
                        {route.volume} vessels • {formatCurrency(route.savings)} saved
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${
                        route.efficiency >= 90 ? 'text-green-400' : 
                        route.efficiency >= 85 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {formatPercentage(route.efficiency)}
                      </div>
                      <div className="text-xs text-gray-400">efficiency</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Alert Distribution */}
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">Alert Distribution</h3>
              <div className="h-64">
                <Doughnut 
                  data={alertsData} 
                  options={{
                    ...chartOptions,
                    scales: undefined,
                    plugins: {
                      ...chartOptions.plugins,
                      legend: {
                        ...chartOptions.plugins.legend,
                        position: 'bottom'
                      }
                    }
                  }} 
                />
              </div>
            </div>
          </div>

          {/* Port Performance Table */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Port Performance Analysis</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-600">
                    <th className="text-left py-2 text-gray-300">Port</th>
                    <th className="text-right py-2 text-gray-300">Efficiency</th>
                    <th className="text-right py-2 text-gray-300">Avg Wait Time</th>
                    <th className="text-right py-2 text-gray-300">Throughput</th>
                  </tr>
                </thead>
                <tbody>
                  {analyticsData.operationalMetrics.portPerformance.map((port) => (
                    <tr key={port.port} className="border-b border-gray-700">
                      <td className="py-2 text-white font-medium">{port.port}</td>
                      <td className={`py-2 text-right font-bold ${
                        port.efficiency >= 95 ? 'text-green-400' : 
                        port.efficiency >= 90 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {formatPercentage(port.efficiency)}
                      </td>
                      <td className="py-2 text-right text-gray-300">{port.avgWaitTime}h</td>
                      <td className="py-2 text-right text-gray-300">{port.throughput.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {userRole === 'OPERATOR' && (
        <>
          {/* Operational Focus for Operators */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Metrics */}
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">Quick Metrics</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Fuel Efficiency</span>
                  <span className="text-blue-400 font-bold">
                    {formatPercentage(analyticsData.kpis.fuelEfficiency)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Route Optimization</span>
                  <span className="text-green-400 font-bold">
                    {formatPercentage(analyticsData.kpis.routeOptimization)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Incident Rate</span>
                  <span className="text-yellow-400 font-bold">
                    {analyticsData.kpis.incidentRate}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Customer Rating</span>
                  <span className="text-purple-400 font-bold">
                    {analyticsData.kpis.customerSatisfaction}/5.0
                  </span>
                </div>
              </div>
            </div>

            {/* Fuel Consumption Trend */}
            <div className="lg:col-span-2 bg-gray-800 rounded-lg p-4 border border-gray-600">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">Fuel Consumption Trend (tons/day)</h3>
              <div className="h-48">
                <Line 
                  data={{
                    labels: analyticsData.trends.fuelConsumption.labels,
                    datasets: [
                      {
                        label: 'Fuel Consumption',
                        data: analyticsData.trends.fuelConsumption.data,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4,
                        fill: true
                      }
                    ]
                  }} 
                  options={chartOptions} 
                />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AnalyticsDashboard;