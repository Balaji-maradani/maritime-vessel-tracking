import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import VesselMap from "../components/VesselMap";
import Notifications from "../components/Notifications";
import AnalyticsDashboard from "../components/AnalyticsDashboard";

// Mock data for maritime operations
const mockVessels = [
  {
    id: 1,
    name: "MV Atlantic Star",
    imo: "9123456",
    type: "Container",
    cargo: "General Cargo",
    flag: "Singapore",
    speed: 18.5,
    heading: 145,
    destination: "Rotterdam",
    eta: "2025-01-02 14:30",
    status: "Moving",
    riskLevel: "Low",
    lat: 1.2897,
    lng: 103.8501
  },
  {
    id: 2,
    name: "MS Pacific Wave",
    imo: "9234567",
    type: "Tanker",
    cargo: "Crude Oil",
    flag: "Liberia",
    speed: 12.3,
    heading: 270,
    destination: "Houston",
    eta: "2025-01-05 08:15",
    status: "Anchored",
    riskLevel: "Medium",
    lat: 19.0760,
    lng: 72.8777
  },
  {
    id: 3,
    name: "MV Cargo Express",
    imo: "9345678",
    type: "Bulk Carrier",
    cargo: "Iron Ore",
    flag: "Marshall Islands",
    speed: 15.8,
    heading: 90,
    destination: "Shanghai",
    eta: "2025-01-08 22:00",
    status: "Moving",
    riskLevel: "High",
    lat: -20.1609,
    lng: 57.5012
  },
  {
    id: 4,
    name: "LNG Explorer",
    imo: "9456789",
    type: "LNG Carrier",
    cargo: "LNG",
    flag: "Panama",
    speed: 19.2,
    heading: 45,
    destination: "Tokyo",
    eta: "2025-01-04 16:45",
    status: "Moving",
    riskLevel: "Low",
    lat: 13.0827,
    lng: 80.2707
  },
  {
    id: 5,
    name: "MV Ocean Breeze",
    imo: "9567890",
    type: "Container",
    cargo: "Electronics",
    flag: "Hong Kong",
    speed: 0,
    heading: 0,
    destination: "Los Angeles",
    eta: "2025-01-10 11:20",
    status: "Waiting",
    riskLevel: "Medium",
    lat: 4.1755,
    lng: 73.5093
  }
];



export default function Dashboard() {
  const { user } = useAuth();
  const [selectedVessel, setSelectedVessel] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [vesselTypeFilter, setVesselTypeFilter] = useState("");
  const [cargoTypeFilter, setCargoTypeFilter] = useState("");
  const [flagFilter, setFlagFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Filter vessels based on search and filters
  const filteredVessels = mockVessels.filter(vessel => {
    const matchesSearch = !searchQuery || 
      vessel.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      vessel.imo.includes(searchQuery);
    
    const matchesType = !vesselTypeFilter || vessel.type === vesselTypeFilter;
    const matchesCargo = !cargoTypeFilter || vessel.cargo === cargoTypeFilter;
    const matchesFlag = !flagFilter || vessel.flag === flagFilter;
    const matchesStatus = !statusFilter || vessel.status === statusFilter;

    return matchesSearch && matchesType && matchesCargo && matchesFlag && matchesStatus;
  });

  // Get unique values for dropdowns
  const vesselTypes = [...new Set(mockVessels.map(v => v.type))];
  const cargoTypes = [...new Set(mockVessels.map(v => v.cargo))];
  const flags = [...new Set(mockVessels.map(v => v.flag))];

  // Calculate stats
  const totalShips = mockVessels.length;
  const delayedShips = mockVessels.filter(v => v.riskLevel === "High").length;
  const dangerZoneShips = mockVessels.filter(v => v.riskLevel === "High" || v.riskLevel === "Medium").length;
  const congestionShips = mockVessels.filter(v => v.status === "Waiting").length;
  const newAlerts = 3; // Simplified alert count for stats display

  if (!user) {
    return <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-white">Loading...</div>
    </div>;
  }

  // Get user role for conditional rendering
  const userRole = user.role?.toUpperCase() || "OPERATOR";
  const isOperator = userRole === "OPERATOR";
  const isAnalyst = userRole === "ANALYST";
  const isAdmin = userRole === "ADMIN";

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* SECTION 5 - Quick Operational Stats (Top widgets) */}
      <div className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">
              {isOperator && "Maritime Operations Control"}
              {isAnalyst && "Maritime Analytics Dashboard"}
              {isAdmin && "System Administration Panel"}
            </h1>
            <p className="text-gray-400">
              {isOperator && `Operator Dashboard - ${user.username}`}
              {isAnalyst && `Analytics Dashboard - ${user.username}`}
              {isAdmin && `Admin Panel - ${user.username}`}
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400">Last Updated</div>
            <div className="text-lg font-mono">{new Date().toLocaleTimeString()}</div>
          </div>
        </div>
        
        <div className="grid grid-cols-5 gap-6">
          {/* OPERATOR STATS */}
          {isOperator && (
            <>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-blue-400">{totalShips}</div>
                <div className="text-sm text-gray-300">Total Active Ships</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-yellow-400">{delayedShips}</div>
                <div className="text-sm text-gray-300">Ships Delayed</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-red-400">{dangerZoneShips}</div>
                <div className="text-sm text-gray-300">Ships in Danger Zone</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-orange-400">{congestionShips}</div>
                <div className="text-sm text-gray-300">Ships in Congestion</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-red-500">{newAlerts}</div>
                <div className="text-sm text-gray-300">Recent Alerts</div>
              </div>
            </>
          )}

          {/* ANALYST STATS */}
          {isAnalyst && (
            <>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-green-400">87%</div>
                <div className="text-sm text-gray-300">On-Time Delivery</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-blue-400">142</div>
                <div className="text-sm text-gray-300">Routes Analyzed</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-purple-400">23.4h</div>
                <div className="text-sm text-gray-300">Avg Transit Time</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-yellow-400">$2.3M</div>
                <div className="text-sm text-gray-300">Cost Savings</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-cyan-400">94%</div>
                <div className="text-sm text-gray-300">Efficiency Score</div>
              </div>
            </>
          )}

          {/* ADMIN STATS */}
          {isAdmin && (
            <>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-green-400">156</div>
                <div className="text-sm text-gray-300">Active Users</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-blue-400">99.8%</div>
                <div className="text-sm text-gray-300">System Uptime</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-purple-400">2.1TB</div>
                <div className="text-sm text-gray-300">Data Processed</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-yellow-400">847</div>
                <div className="text-sm text-gray-300">API Calls/min</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="text-2xl font-bold text-red-400">3</div>
                <div className="text-sm text-gray-300">Security Events</div>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="flex h-[calc(100vh-200px)]">
        {/* SECTION 2 - Ship Search & Filters (Left Sidebar) - OPERATOR & ANALYST ONLY */}
        {(isOperator || isAnalyst) && (
          <div className="w-80 bg-gray-800 border-r border-gray-700 p-6 overflow-y-auto">
            <h2 className="text-xl font-bold mb-6 text-blue-400">
              {isOperator ? "Ship Search & Filters" : "Analytics Filters"}
            </h2>
          
          {/* Search */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Search by Vessel Name / IMO</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter name or IMO..."
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Vessel Type Filter */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Vessel Type</label>
            <select
              value={vesselTypeFilter}
              onChange={(e) => setVesselTypeFilter(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              {vesselTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          {/* Cargo Type Filter */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Cargo Type</label>
            <select
              value={cargoTypeFilter}
              onChange={(e) => setCargoTypeFilter(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Cargo Types</option>
              {cargoTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          {/* Flag Filter */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Flag</label>
            <select
              value={flagFilter}
              onChange={(e) => setFlagFilter(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Flags</option>
              {flags.map(flag => (
                <option key={flag} value={flag}>{flag}</option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Status</option>
              <option value="Moving">Moving</option>
              <option value="Anchored">Anchored</option>
              <option value="Waiting">Waiting</option>
            </select>
          </div>

          {/* Clear Filters */}
          <button
            onClick={() => {
              setSearchQuery("");
              setVesselTypeFilter("");
              setCargoTypeFilter("");
              setFlagFilter("");
              setStatusFilter("");
            }}
            className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-md transition-colors"
          >
            Clear All Filters
          </button>

          <div className="mt-4 text-sm text-gray-400">
            {isOperator ? `Showing ${filteredVessels.length} of ${totalShips} vessels` : `Analyzing ${filteredVessels.length} vessel routes`}
          </div>
        </div>
        )}

        {/* ADMIN SIDEBAR - System Management */}
        {isAdmin && (
          <div className="w-80 bg-gray-800 border-r border-gray-700 p-6 overflow-y-auto">
            <h2 className="text-xl font-bold mb-6 text-blue-400">System Management</h2>
            
            {/* User Management */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3 text-gray-300">User Management</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                  <span className="text-sm">Active Users</span>
                  <span className="text-green-400 font-bold">156</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                  <span className="text-sm">Operators</span>
                  <span className="text-blue-400">89</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                  <span className="text-sm">Analysts</span>
                  <span className="text-purple-400">52</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                  <span className="text-sm">Admins</span>
                  <span className="text-red-400">15</span>
                </div>
              </div>
            </div>

            {/* System Health */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3 text-gray-300">System Health</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                  <span className="text-sm">CPU Usage</span>
                  <span className="text-yellow-400">34%</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                  <span className="text-sm">Memory</span>
                  <span className="text-green-400">67%</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                  <span className="text-sm">Storage</span>
                  <span className="text-blue-400">45%</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                  <span className="text-sm">Network</span>
                  <span className="text-green-400">Normal</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div>
              <h3 className="text-lg font-semibold mb-3 text-gray-300">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors">
                  Backup System
                </button>
                <button className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 rounded text-sm transition-colors">
                  Generate Report
                </button>
                <button className="w-full px-3 py-2 bg-yellow-600 hover:bg-yellow-700 rounded text-sm transition-colors">
                  Maintenance Mode
                </button>
              </div>
            </div>
          </div>
        )}

        {/* SECTION 1 - Main Content Area */}
        <div className="flex-1 bg-gray-900 relative">
          {/* OPERATOR - Real Interactive Map */}
          {isOperator && (
            <VesselMap 
              vessels={filteredVessels.map(vessel => ({
                id: vessel.id,
                name: vessel.name,
                type: vessel.type,
                status: vessel.status,
                speed: vessel.speed,
                destination: vessel.destination,
                lat: vessel.lat,
                lng: vessel.lng
              }))}
              onVesselClick={setSelectedVessel}
            />
          )}

          {/* ANALYST - Advanced Analytics Dashboard */}
          {isAnalyst && (
            <div className="h-full bg-gray-900 p-6 overflow-y-auto">
              <AnalyticsDashboard userRole="ANALYST" />
            </div>
          )}

          {/* ADMIN - System Dashboard */}
          {isAdmin && (
            <div className="h-full bg-gray-900 p-6 overflow-y-auto">
              <div className="grid grid-cols-2 gap-6 h-full">
                {/* Audit Logs */}
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
                  <h3 className="text-lg font-bold mb-4 text-blue-400">Recent Audit Logs</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                      <span>User login: operator_john</span>
                      <span className="text-green-400">14:32</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                      <span>Data export: vessel_reports.csv</span>
                      <span className="text-blue-400">14:28</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                      <span>System backup completed</span>
                      <span className="text-green-400">14:15</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                      <span>Failed login attempt</span>
                      <span className="text-red-400">14:02</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                      <span>User role changed: analyst_sarah</span>
                      <span className="text-yellow-400">13:45</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                      <span>Database maintenance started</span>
                      <span className="text-purple-400">13:30</span>
                    </div>
                  </div>
                </div>

                {/* System Performance */}
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
                  <h3 className="text-lg font-bold mb-4 text-blue-400">System Performance</h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm">CPU Usage</span>
                        <span className="text-sm">34%</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div className="bg-yellow-400 h-2 rounded-full" style={{width: '34%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm">Memory Usage</span>
                        <span className="text-sm">67%</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div className="bg-green-400 h-2 rounded-full" style={{width: '67%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm">Storage Usage</span>
                        <span className="text-sm">45%</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div className="bg-blue-400 h-2 rounded-full" style={{width: '45%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm">Network I/O</span>
                        <span className="text-sm">23%</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div className="bg-purple-400 h-2 rounded-full" style={{width: '23%'}}></div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Active Sessions */}
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
                  <h3 className="text-lg font-bold mb-4 text-blue-400">Active User Sessions</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                      <div>
                        <div className="font-medium">operator_john</div>
                        <div className="text-gray-400 text-xs">192.168.1.45</div>
                      </div>
                      <span className="text-green-400">Active</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                      <div>
                        <div className="font-medium">analyst_sarah</div>
                        <div className="text-gray-400 text-xs">192.168.1.67</div>
                      </div>
                      <span className="text-green-400">Active</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                      <div>
                        <div className="font-medium">admin_mike</div>
                        <div className="text-gray-400 text-xs">192.168.1.23</div>
                      </div>
                      <span className="text-yellow-400">Idle</span>
                    </div>
                  </div>
                </div>

                {/* Database Status */}
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
                  <h3 className="text-lg font-bold mb-4 text-blue-400">Database Status</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Connection Pool</span>
                      <span className="text-green-400">Healthy</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Query Performance</span>
                      <span className="text-green-400">Optimal</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Replication Lag</span>
                      <span className="text-blue-400">0.2s</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Last Backup</span>
                      <span className="text-gray-400">2 hours ago</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Data Size</span>
                      <span className="text-purple-400">2.1 TB</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* SECTION 4 - Right Sidebar - Role-based content */}
        <div className="w-80 bg-gray-800 border-l border-gray-700 p-6 overflow-y-auto">
          {/* OPERATOR - Real-time Alerts & Notifications */}
          {isOperator && (
            <>
              {/* Quick Analytics Summary for Operators */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-blue-400">Quick Analytics</h3>
                <div className="grid grid-cols-2 gap-2 mb-4">
                  <div className="bg-gray-700 p-2 rounded text-center">
                    <div className="text-lg font-bold text-green-400">87.3%</div>
                    <div className="text-xs text-gray-300">Efficiency</div>
                  </div>
                  <div className="bg-gray-700 p-2 rounded text-center">
                    <div className="text-lg font-bold text-blue-400">92.1%</div>
                    <div className="text-xs text-gray-300">On-Time</div>
                  </div>
                  <div className="bg-gray-700 p-2 rounded text-center">
                    <div className="text-lg font-bold text-purple-400">$2.3M</div>
                    <div className="text-xs text-gray-300">Savings</div>
                  </div>
                  <div className="bg-gray-700 p-2 rounded text-center">
                    <div className="text-lg font-bold text-yellow-400">23.4h</div>
                    <div className="text-xs text-gray-300">Avg Time</div>
                  </div>
                </div>
              </div>

              <h2 className="text-xl font-bold mb-6 text-blue-400">Alerts & Notifications</h2>
              <Notifications 
                limit={8} 
                autoRefresh={true} 
                refreshInterval={30000} 
              />
            </>
          )}

          {/* ANALYST - Analytics Summary Sidebar */}
          {isAnalyst && (
            <>
              <h2 className="text-xl font-bold mb-6 text-blue-400">Key Insights</h2>
              
              {/* Top KPIs */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-gray-300">Performance KPIs</h3>
                <div className="space-y-3">
                  <div className="bg-gray-700 p-3 rounded">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm">Overall Efficiency</span>
                      <span className="text-blue-400 font-bold">87.3%</span>
                    </div>
                    <div className="text-xs text-green-400">↗ +2.1% vs last period</div>
                  </div>
                  <div className="bg-gray-700 p-3 rounded">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm">Cost Savings</span>
                      <span className="text-green-400 font-bold">$2.34M</span>
                    </div>
                    <div className="text-xs text-green-400">↗ +12.3% vs last period</div>
                  </div>
                  <div className="bg-gray-700 p-3 rounded">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm">On-Time Delivery</span>
                      <span className="text-purple-400 font-bold">92.1%</span>
                    </div>
                    <div className="text-xs text-green-400">↗ +1.8% vs last period</div>
                  </div>
                </div>
              </div>

              {/* Route Performance */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-gray-300">Top Routes</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                    <div>
                      <div className="text-sm font-medium">Asia-Europe</div>
                      <div className="text-xs text-gray-400">1,250 vessels</div>
                    </div>
                    <div className="text-right">
                      <div className="text-green-400 font-bold">94.2%</div>
                      <div className="text-xs text-gray-400">efficiency</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                    <div>
                      <div className="text-sm font-medium">Trans-Pacific</div>
                      <div className="text-xs text-gray-400">980 vessels</div>
                    </div>
                    <div className="text-right">
                      <div className="text-yellow-400 font-bold">89.7%</div>
                      <div className="text-xs text-gray-400">efficiency</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
                    <div>
                      <div className="text-sm font-medium">Atlantic</div>
                      <div className="text-xs text-gray-400">750 vessels</div>
                    </div>
                    <div className="text-right">
                      <div className="text-green-400 font-bold">91.3%</div>
                      <div className="text-xs text-gray-400">efficiency</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Predictive Analytics */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-gray-300">Predictive Insights</h3>
                <div className="space-y-2 text-sm">
                  <div className="p-3 bg-blue-900/30 border border-blue-600 rounded">
                    <div className="font-medium mb-1 flex items-center gap-2">
                      <span>🌊</span>
                      <span>Weather Impact</span>
                    </div>
                    <div className="text-gray-300">Storm system may delay 3 vessels by 6-8 hours</div>
                  </div>
                  <div className="p-3 bg-yellow-900/30 border border-yellow-600 rounded">
                    <div className="font-medium mb-1 flex items-center gap-2">
                      <span>🏭</span>
                      <span>Port Congestion</span>
                    </div>
                    <div className="text-gray-300">Singapore port expected 15% increase in wait times</div>
                  </div>
                  <div className="p-3 bg-green-900/30 border border-green-600 rounded">
                    <div className="font-medium mb-1 flex items-center gap-2">
                      <span>⚡</span>
                      <span>Optimization</span>
                    </div>
                    <div className="text-gray-300">New route optimization could save $180K monthly</div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div>
                <h3 className="text-lg font-semibold mb-3 text-gray-300">Quick Actions</h3>
                <div className="space-y-2">
                  <button className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors">
                    📊 Generate Report
                  </button>
                  <button className="w-full px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm transition-colors">
                    📈 Export Analytics
                  </button>
                  <button className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 rounded text-sm transition-colors">
                    🔍 Deep Dive Analysis
                  </button>
                </div>
              </div>
            </>
          )}

          {/* ADMIN - System Stats */}
          {isAdmin && (
            <>
              <h2 className="text-xl font-bold mb-6 text-blue-400">System Overview</h2>
              
              {/* Security Events */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-gray-300">Security Events</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-red-900/30 border border-red-600 rounded">
                    <span className="text-sm">Failed Login Attempts</span>
                    <span className="text-red-400">3</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-yellow-900/30 border border-yellow-600 rounded">
                    <span className="text-sm">Suspicious Activity</span>
                    <span className="text-yellow-400">1</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-green-900/30 border border-green-600 rounded">
                    <span className="text-sm">Security Scans</span>
                    <span className="text-green-400">Passed</span>
                  </div>
                </div>
              </div>

              {/* System Alerts */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-gray-300">System Alerts</h3>
                <div className="space-y-2 text-sm">
                  <div className="p-3 bg-blue-900/30 border border-blue-600 rounded">
                    <div className="font-medium mb-1">Backup Completed</div>
                    <div className="text-gray-400">Daily backup finished successfully</div>
                    <div className="text-xs text-gray-500 mt-1">2 hours ago</div>
                  </div>
                  <div className="p-3 bg-green-900/30 border border-green-600 rounded">
                    <div className="font-medium mb-1">System Update</div>
                    <div className="text-gray-400">Security patches applied</div>
                    <div className="text-xs text-gray-500 mt-1">6 hours ago</div>
                  </div>
                </div>
              </div>

              {/* Resource Usage */}
              <div>
                <h3 className="text-lg font-semibold mb-3 text-gray-300">Resource Usage</h3>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">API Requests/min</span>
                      <span className="text-sm">847</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div className="bg-blue-400 h-2 rounded-full" style={{width: '70%'}}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">Database Connections</span>
                      <span className="text-sm">23/50</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div className="bg-green-400 h-2 rounded-full" style={{width: '46%'}}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">Cache Hit Rate</span>
                      <span className="text-sm">94%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div className="bg-purple-400 h-2 rounded-full" style={{width: '94%'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* SECTION 3 - Ship Details Popup */}
      {selectedVessel && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-600">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-blue-400">{selectedVessel.name}</h3>
              <button
                onClick={() => setSelectedVessel(null)}
                className="text-gray-400 hover:text-white text-xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-400">IMO</div>
                  <div className="font-mono">{selectedVessel.imo}</div>
                </div>
                <div>
                  <div className="text-gray-400">Type</div>
                  <div>{selectedVessel.type}</div>
                </div>
                <div>
                  <div className="text-gray-400">Cargo</div>
                  <div>{selectedVessel.cargo}</div>
                </div>
                <div>
                  <div className="text-gray-400">Flag</div>
                  <div>{selectedVessel.flag}</div>
                </div>
                <div>
                  <div className="text-gray-400">Speed</div>
                  <div>{selectedVessel.speed} knots</div>
                </div>
                <div>
                  <div className="text-gray-400">Heading</div>
                  <div>{selectedVessel.heading}°</div>
                </div>
                <div>
                  <div className="text-gray-400">Destination</div>
                  <div>{selectedVessel.destination}</div>
                </div>
                <div>
                  <div className="text-gray-400">ETA</div>
                  <div className="text-xs">{selectedVessel.eta}</div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-gray-400">Risk Level:</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  selectedVessel.riskLevel === 'High' ? 'bg-red-600 text-white' :
                  selectedVessel.riskLevel === 'Medium' ? 'bg-yellow-600 text-black' :
                  'bg-green-600 text-white'
                }`}>
                  {selectedVessel.riskLevel}
                </span>
              </div>
            </div>
            
            <div className="flex gap-2 mt-6">
              <button className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md transition-colors text-sm">
                Track Vessel
              </button>
              <button className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-md transition-colors text-sm">
                Voyage History
              </button>
              <button className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors text-sm">
                Subscribe Alerts
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
