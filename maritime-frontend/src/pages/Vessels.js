import { useEffect, useState, useMemo, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import VesselMap from "../components/VesselMap";

// Mock vessel data with Indian Ocean coordinates
const mockVessels = [
  {
    id: 1,
    name: "MV Mumbai Express",
    imo_number: "9123456",
    vessel_type: "Container Ship",
    cargo_type: "General Cargo",
    flag: "India",
    operator: "Maersk Line",
    status: "Moving",
    speed: 18.5,
    heading: 45,
    destination: "Dubai",
    lat: 19.0760,
    lng: 72.8777
  },
  {
    id: 2,
    name: "Colombo Trader",
    imo_number: "9234567",
    vessel_type: "Cargo Vessel",
    cargo_type: "Textiles",
    flag: "Sri Lanka",
    operator: "CMA CGM",
    status: "Anchored",
    speed: 0,
    heading: 0,
    destination: "Singapore",
    lat: 6.9271,
    lng: 79.8612
  },
  {
    id: 3,
    name: "Indian Ocean Pioneer",
    imo_number: "9345678",
    vessel_type: "Tanker",
    cargo_type: "Crude Oil",
    flag: "Liberia",
    operator: "Shell",
    status: "Moving",
    speed: 14.2,
    heading: 120,
    destination: "Port Louis",
    lat: -20.1609,
    lng: 57.5012
  },
  {
    id: 4,
    name: "Chennai Star",
    imo_number: "9456789",
    vessel_type: "Bulk Carrier",
    cargo_type: "Iron Ore",
    flag: "Marshall Islands",
    operator: "BHP",
    status: "Moving",
    speed: 16.8,
    heading: 270,
    destination: "Karachi",
    lat: 13.0827,
    lng: 80.2707
  },
  {
    id: 5,
    name: "Arabian Sea Voyager",
    imo_number: "9567890",
    vessel_type: "Container Ship",
    cargo_type: "Electronics",
    flag: "UAE",
    operator: "COSCO",
    status: "Anchored",
    speed: 0,
    heading: 0,
    destination: "Mumbai",
    lat: 23.0225,
    lng: 72.5714
  },
  {
    id: 6,
    name: "Maldives Carrier",
    imo_number: "9678901",
    vessel_type: "Passenger Ferry",
    cargo_type: "Passengers",
    flag: "Maldives",
    operator: "Maldivian",
    status: "Moving",
    speed: 22.1,
    heading: 180,
    destination: "Male",
    lat: 4.1755,
    lng: 73.5093
  },
  {
    id: 7,
    name: "Bay of Bengal Explorer",
    imo_number: "9789012",
    vessel_type: "Research Vessel",
    cargo_type: "Scientific Equipment",
    flag: "Bangladesh",
    operator: "Research Institute",
    status: "Anchored",
    speed: 0,
    heading: 0,
    destination: "Chittagong",
    lat: 21.4272,
    lng: 92.0058
  },
  {
    id: 8,
    name: "Seychelles Navigator",
    imo_number: "9890123",
    vessel_type: "Cruise Ship",
    cargo_type: "Passengers",
    flag: "Seychelles",
    operator: "Royal Caribbean",
    status: "Moving",
    speed: 19.5,
    heading: 315,
    destination: "Victoria",
    lat: -4.6796,
    lng: 55.4920
  }
];

function Vessels() {
  const { token, user } = useAuth();
  const mapRef = useRef(null);

  const [vessels, setVessels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedVessel, setSelectedVessel] = useState(null);

  // Filters
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    const fetchVessels = async () => {
      setLoading(true);
      setError("");

      try {
        const res = await fetch("http://127.0.0.1:8000/api/vessels/", {
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        });

        if (!res.ok) {
          throw new Error("Failed to fetch vessels");
        }

        const data = await res.json();
        setVessels(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("API error:", err);
        // Use mock data on error
        setVessels(mockVessels);
        setError("");
      } finally {
        setLoading(false);
      }
    };

    fetchVessels();
  }, [token]);

  // Compute filter options from data
  const vesselTypes = useMemo(() => {
    const types = new Set();
    vessels.forEach((v) => v.vessel_type && types.add(v.vessel_type));
    return Array.from(types);
  }, [vessels]);

  // Apply search and filters
  const filteredVessels = useMemo(() => {
    const s = search.toLowerCase().trim();

    return vessels.filter((v) => {
      const matchesSearch =
        !s ||
        v.name?.toLowerCase().includes(s) ||
        v.imo_number?.toString().includes(s) ||
        v.operator?.toLowerCase().includes(s) ||
        v.flag?.toLowerCase().includes(s);

      const matchesType =
        typeFilter === "ALL" || v.vessel_type === typeFilter;

      const matchesStatus =
        statusFilter === "ALL" || v.status === statusFilter;

      return matchesSearch && matchesType && matchesStatus;
    });
  }, [vessels, search, typeFilter, statusFilter]);

  const handleVesselSelect = (vessel) => {
    setSelectedVessel(vessel);
    // Zoom map to vessel if map ref is available
    if (mapRef.current) {
      mapRef.current.zoomToVessel(vessel);
    }
  };

  const handleMapVesselClick = (vessel) => {
    setSelectedVessel(vessel);
  };

  // Get status badge color
  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'Moving':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'Anchored':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'Waiting':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Vessel Tracking</h1>
            <p className="text-gray-400 text-sm">
              Live maritime vessel monitoring • {filteredVessels.length} vessels
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400">User: {user.username}</div>
            <div className="text-xs text-gray-500">Role: {user.role}</div>
          </div>
        </div>
      </div>

      {/* Main Content - Split Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Vessel List (30%) */}
        <div className="w-[30%] bg-gray-800 border-r border-gray-700 flex flex-col">
          {/* Search and Filters */}
          <div className="p-4 border-b border-gray-700 flex-shrink-0">
            <div className="space-y-3">
              {/* Search Bar */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search vessels by name, IMO..."
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
              </div>

              {/* Filters Row */}
              <div className="flex gap-2">
                <select
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                >
                  <option value="ALL">All Types</option>
                  {vesselTypes.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>

                <select
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="ALL">All Status</option>
                  <option value="Moving">Moving</option>
                  <option value="Anchored">Anchored</option>
                  <option value="Waiting">Waiting</option>
                </select>
              </div>
            </div>
          </div>

          {/* Vessel List */}
          <div className="flex-1 overflow-y-auto">
            {loading && (
              <div className="flex justify-center items-center h-32">
                <div className="text-gray-400">Loading vessels...</div>
              </div>
            )}

            {!loading && error && (
              <div className="p-4">
                <div className="bg-red-900/30 border border-red-600 rounded-lg p-3 text-red-300 text-sm">
                  {error}
                </div>
              </div>
            )}

            {!loading && !error && filteredVessels.length === 0 && (
              <div className="p-4 text-center text-gray-400">
                No vessels found matching your criteria.
              </div>
            )}

            {!loading && !error && filteredVessels.length > 0 && (
              <div className="space-y-1 p-2">
                {filteredVessels.map((vessel) => (
                  <div
                    key={vessel.id}
                    onClick={() => handleVesselSelect(vessel)}
                    className={`p-3 rounded-lg cursor-pointer transition-all duration-200 border ${
                      selectedVessel?.id === vessel.id
                        ? 'bg-blue-900/50 border-blue-500 shadow-lg'
                        : 'bg-gray-700 border-gray-600 hover:bg-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-white text-sm truncate">
                          {vessel.name}
                        </h3>
                        <p className="text-xs text-gray-400 font-mono">
                          IMO: {vessel.imo_number || "N/A"}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusBadgeColor(vessel.status)}`}>
                        {vessel.status || "Unknown"}
                      </span>
                    </div>
                    
                    <div className="space-y-1 text-xs text-gray-300">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Type:</span>
                        <span className="truncate ml-2">{vessel.vessel_type || "N/A"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Flag:</span>
                        <span className="truncate ml-2">{vessel.flag || "N/A"}</span>
                      </div>
                      {vessel.speed !== undefined && (
                        <div className="flex justify-between">
                          <span className="text-gray-400">Speed:</span>
                          <span className="font-mono">{vessel.speed} kts</span>
                        </div>
                      )}
                      {vessel.destination && (
                        <div className="flex justify-between">
                          <span className="text-gray-400">Dest:</span>
                          <span className="truncate ml-2">{vessel.destination}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Map (70%) */}
        <div className="flex-1 relative">
          <VesselMap
            ref={mapRef}
            vessels={filteredVessels}
            onVesselClick={handleMapVesselClick}
            selectedVessel={selectedVessel}
          />
        </div>
      </div>
    </div>
  );
}

export default Vessels;
