import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";

// API base URL from environment variable
const API_BASE_URL = process.env.REACT_APP_API_BASE || 'https://maritime-backend-q150.onrender.com';

// Mock data for development/fallback
const mockPortData = [
  {
    id: 1,
    name: "Port of Mumbai",
    country: "India",
    congestion_score: 85.5,
    avg_wait_time: 12.5,
    arrivals: 45,
    departures: 38,
    last_updated: "2025-01-07T10:30:00Z"
  },
  {
    id: 2,
    name: "Port of Dubai",
    country: "UAE",
    congestion_score: 72.3,
    avg_wait_time: 8.2,
    arrivals: 62,
    departures: 58,
    last_updated: "2025-01-07T10:25:00Z"
  },
  {
    id: 3,
    name: "Port of Singapore",
    country: "Singapore",
    congestion_score: 68.1,
    avg_wait_time: 6.8,
    arrivals: 89,
    departures: 92,
    last_updated: "2025-01-07T10:28:00Z"
  },
  {
    id: 4,
    name: "Port of Colombo",
    country: "Sri Lanka",
    congestion_score: 91.2,
    avg_wait_time: 15.7,
    arrivals: 28,
    departures: 22,
    last_updated: "2025-01-07T10:20:00Z"
  },
  {
    id: 5,
    name: "Port of Karachi",
    country: "Pakistan",
    congestion_score: 78.9,
    avg_wait_time: 11.3,
    arrivals: 34,
    departures: 31,
    last_updated: "2025-01-07T10:15:00Z"
  },
  {
    id: 6,
    name: "Port of Chennai",
    country: "India",
    congestion_score: 76.4,
    avg_wait_time: 9.8,
    arrivals: 52,
    departures: 48,
    last_updated: "2025-01-07T10:22:00Z"
  }
];

export default function PortCongestionDashboard() {
  const { user, token } = useAuth();
  const [ports, setPorts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("congestion_score");
  const [sortOrder, setSortOrder] = useState("desc");

  useEffect(() => {
    fetchPortData();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchPortData = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/ports/congestion/`, {
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch port data");
      }

      const data = await response.json();
      setPorts(data.results || data);
    } catch (err) {
      console.warn("API fetch failed, using mock data:", err.message);
      // Use mock data as fallback
      setPorts(mockPortData);
      setError("Using sample data - API connection unavailable");
    } finally {
      setLoading(false);
    }
  };

  // Get congestion level and color
  const getCongestionLevel = (score) => {
    if (score >= 90) return { level: "Critical", color: "text-red-500", bg: "bg-red-500" };
    if (score >= 80) return { level: "High", color: "text-orange-500", bg: "bg-orange-500" };
    if (score >= 70) return { level: "Medium", color: "text-yellow-500", bg: "bg-yellow-500" };
    if (score >= 60) return { level: "Low", color: "text-blue-500", bg: "bg-blue-500" };
    return { level: "Minimal", color: "text-green-500", bg: "bg-green-500" };
  };

  // Filter and sort ports
  const filteredPorts = ports
    .filter(port => 
      port.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      port.country.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      if (sortOrder === "asc") {
        return aVal > bVal ? 1 : -1;
      }
      return aVal < bVal ? 1 : -1;
    });

  // Calculate summary statistics
  const totalPorts = ports.length;
  const avgCongestion = ports.length > 0 ? (ports.reduce((sum, port) => sum + port.congestion_score, 0) / ports.length).toFixed(1) : 0;
  const criticalPorts = ports.filter(port => port.congestion_score >= 90).length;
  const totalArrivals = ports.reduce((sum, port) => sum + port.arrivals, 0);
  const totalDepartures = ports.reduce((sum, port) => sum + port.departures, 0);

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header Section */}
      <div className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">Port Congestion Dashboard</h1>
            <p className="text-gray-400">Real-time port congestion analytics - {user.username}</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400">Last Updated</div>
            <div className="text-lg font-mono">{new Date().toLocaleTimeString()}</div>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-5 gap-6">
          <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
            <div className="text-2xl font-bold text-blue-400">{totalPorts}</div>
            <div className="text-sm text-gray-300">Total Ports</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
            <div className="text-2xl font-bold text-yellow-400">{avgCongestion}%</div>
            <div className="text-sm text-gray-300">Avg Congestion</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
            <div className="text-2xl font-bold text-red-400">{criticalPorts}</div>
            <div className="text-sm text-gray-300">Critical Ports</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
            <div className="text-2xl font-bold text-green-400">{totalArrivals}</div>
            <div className="text-sm text-gray-300">Total Arrivals</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
            <div className="text-2xl font-bold text-purple-400">{totalDepartures}</div>
            <div className="text-sm text-gray-300">Total Departures</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        {/* Controls */}
        <div className="mb-6 flex flex-wrap gap-4 items-center justify-between">
          <div className="flex gap-4 items-center">
            <input
              type="text"
              placeholder="Search ports or countries..."
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <select
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field);
                setSortOrder(order);
              }}
            >
              <option value="congestion_score-desc">Congestion (High to Low)</option>
              <option value="congestion_score-asc">Congestion (Low to High)</option>
              <option value="avg_wait_time-desc">Wait Time (High to Low)</option>
              <option value="avg_wait_time-asc">Wait Time (Low to High)</option>
              <option value="name-asc">Name (A to Z)</option>
              <option value="name-desc">Name (Z to A)</option>
            </select>
          </div>
          
          {error && (
            <div className="text-yellow-400 text-sm bg-yellow-900/20 px-3 py-1 rounded">
              ⚠️ {error}
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span className="ml-3 text-gray-400">Loading port data...</span>
          </div>
        )}

        {/* Port Cards Grid */}
        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {filteredPorts.map((port) => {
              const congestionInfo = getCongestionLevel(port.congestion_score);
              return (
                <div key={port.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{port.name}</h3>
                      <p className="text-gray-400 text-sm">{port.country}</p>
                    </div>
                    <div className="text-right">
                      <div className={`text-2xl font-bold ${congestionInfo.color}`}>
                        {port.congestion_score.toFixed(1)}%
                      </div>
                      <div className={`text-xs px-2 py-1 rounded ${congestionInfo.bg} text-white`}>
                        {congestionInfo.level}
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Wait Time:</span>
                      <span className="text-white font-mono">{port.avg_wait_time.toFixed(1)}h</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Arrivals:</span>
                      <span className="text-green-400 font-mono">{port.arrivals}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Departures:</span>
                      <span className="text-blue-400 font-mono">{port.departures}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Net Flow:</span>
                      <span className={`font-mono ${port.arrivals - port.departures > 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {port.arrivals - port.departures > 0 ? '+' : ''}{port.arrivals - port.departures}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Detailed Table */}
        {!loading && (
          <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700">
              <h2 className="text-xl font-semibold text-white">Detailed Port Analytics</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Port</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Country</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Congestion</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Wait Time</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Arrivals</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Departures</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Net Flow</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Last Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {filteredPorts.map((port) => {
                    const congestionInfo = getCongestionLevel(port.congestion_score);
                    const netFlow = port.arrivals - port.departures;
                    return (
                      <tr key={port.id} className="hover:bg-gray-700/50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-white">{port.name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-300">{port.country}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className={`w-3 h-3 rounded-full ${congestionInfo.bg} mr-2`}></div>
                            <span className={`text-sm font-medium ${congestionInfo.color}`}>
                              {port.congestion_score.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-mono text-gray-300">{port.avg_wait_time.toFixed(1)}h</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-mono text-green-400">{port.arrivals}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-mono text-blue-400">{port.departures}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`text-sm font-mono ${netFlow > 0 ? 'text-red-400' : netFlow < 0 ? 'text-green-400' : 'text-gray-400'}`}>
                            {netFlow > 0 ? '+' : ''}{netFlow}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-400">
                            {new Date(port.last_updated).toLocaleString()}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredPorts.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg">No ports found matching your search criteria</div>
            <button
              onClick={() => setSearchTerm("")}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Clear Search
            </button>
          </div>
        )}
      </div>
    </div>
  );
}