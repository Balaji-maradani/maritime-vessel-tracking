import React, { useState, useEffect, useRef, useImperativeHandle, forwardRef, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// API base URL from environment variable (for WebSocket mock)
const API_BASE_URL = process.env.REACT_APP_API_BASE || 'https://maritime-backend-q150.onrender.com';

// Fix default icon issue with Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Utility function to validate latitude and longitude
const isValidLatLng = (lat, lng) => {
  // Check if both values exist and are numbers
  if (typeof lat !== 'number' || typeof lng !== 'number') {
    return false;
  }
  
  // Check for NaN values
  if (isNaN(lat) || isNaN(lng)) {
    return false;
  }
  
  // Check for valid latitude range (-90 to 90)
  if (lat < -90 || lat > 90) {
    return false;
  }
  
  // Check for valid longitude range (-180 to 180)
  if (lng < -180 || lng > 180) {
    return false;
  }
  
  // Check for infinite values
  if (!isFinite(lat) || !isFinite(lng)) {
    return false;
  }
  
  return true;
};

// Utility function to clamp values within valid ranges
const clampLatitude = (lat) => {
  if (typeof lat !== 'number' || isNaN(lat) || !isFinite(lat)) {
    return 0; // Default to equator if invalid
  }
  return Math.max(-90, Math.min(90, lat));
};

const clampLongitude = (lng) => {
  if (typeof lng !== 'number' || isNaN(lng) || !isFinite(lng)) {
    return 75; // Default to Indian Ocean longitude if invalid
  }
  return Math.max(-180, Math.min(180, lng));
};

// Safe default coordinates for vessels with invalid positions (Indian Ocean)
const SAFE_DEFAULT_COORDINATES = {
  lat: -10.0,  // Indian Ocean center
  lng: 75.0    // Indian Ocean center
};

// Enhanced vessel data sanitization with safe fallbacks
const sanitizeVesselDataWithFallback = (vessel) => {
  let lat = vessel.lat;
  let lng = vessel.lng;
  let needsReset = false;
  
  // Convert string coordinates to numbers if needed
  if (typeof lat === 'string') {
    lat = parseFloat(lat);
  }
  if (typeof lng === 'string') {
    lng = parseFloat(lng);
  }
  
  // Check if coordinates are invalid and need reset
  if (!isValidLatLng(lat, lng)) {
    console.warn(`Vessel ${vessel.id || vessel.name} has invalid coordinates (${vessel.lat}, ${vessel.lng}), resetting to safe default position`);
    lat = SAFE_DEFAULT_COORDINATES.lat;
    lng = SAFE_DEFAULT_COORDINATES.lng;
    needsReset = true;
  }
  
  // Clamp coordinates to valid ranges as additional safety
  lat = clampLatitude(lat);
  lng = clampLongitude(lng);
  
  return {
    ...vessel,
    lat,
    lng,
    _coordinatesReset: needsReset // Flag to track if coordinates were reset
  };
};

// Enhanced mock safety data with additional layers
const mockSafetyData = {
  stormZones: [
    {
      id: 'storm_001',
      name: 'Tropical Cyclone Belal',
      type: 'tropical_cyclone',
      severity: 'high',
      coordinates: [
        [15.0, 85.0],
        [18.0, 88.0],
        [20.0, 85.0],
        [17.0, 82.0],
        [15.0, 85.0]
      ],
      windSpeed: 120,
      description: 'Category 3 tropical cyclone moving northwest at 15 km/h'
    },
    {
      id: 'storm_002',
      name: 'Monsoon Depression',
      type: 'monsoon',
      severity: 'medium',
      coordinates: [
        [8.0, 75.0],
        [12.0, 78.0],
        [10.0, 80.0],
        [6.0, 77.0],
        [8.0, 75.0]
      ],
      windSpeed: 65,
      description: 'Monsoon depression with heavy rainfall and strong winds'
    },
    {
      id: 'storm_003',
      name: 'Severe Weather System',
      type: 'thunderstorm',
      severity: 'medium',
      coordinates: [
        [-5.0, 60.0],
        [-2.0, 63.0],
        [-7.0, 65.0],
        [-10.0, 62.0],
        [-5.0, 60.0]
      ],
      windSpeed: 85,
      description: 'Severe thunderstorm system with strong winds and heavy rain'
    }
  ],
  piracyZones: [
    {
      id: 'piracy_001',
      name: 'Gulf of Aden High Risk Area',
      type: 'piracy_hotspot',
      severity: 'critical',
      center: [12.0, 45.0],
      radius: 200000, // meters
      riskLevel: 'Very High',
      description: 'Active piracy area - armed guards recommended, avoid night transit'
    },
    {
      id: 'piracy_002',
      name: 'Somali Basin Risk Zone',
      type: 'piracy_patrol',
      severity: 'high',
      center: [5.0, 55.0],
      radius: 150000,
      riskLevel: 'High',
      description: 'Elevated piracy risk - maintain vigilance, report to naval forces'
    },
    {
      id: 'piracy_003',
      name: 'Nigerian Waters Risk Area',
      type: 'piracy_kidnapping',
      severity: 'high',
      center: [4.5, 6.0],
      radius: 120000,
      riskLevel: 'High',
      description: 'Kidnapping and robbery risk - enhanced security protocols required'
    },
    {
      id: 'piracy_004',
      name: 'Strait of Malacca Patrol Zone',
      type: 'piracy_robbery',
      severity: 'medium',
      center: [2.5, 102.0],
      radius: 80000,
      riskLevel: 'Medium',
      description: 'Robbery incidents reported - maintain watch and speed'
    }
  ],
  highRiskWaters: [
    {
      id: 'risk_001',
      name: 'Gulf of Aden High Risk Area',
      type: 'piracy',
      severity: 'critical',
      center: [12.0, 45.0],
      radius: 200000, // meters
      description: 'High piracy risk area - enhanced security measures required'
    },
    {
      id: 'risk_002',
      name: 'Somali Basin Risk Zone',
      type: 'piracy',
      severity: 'high',
      center: [5.0, 55.0],
      radius: 150000,
      description: 'Elevated piracy risk - maintain vigilance'
    },
    {
      id: 'risk_003',
      name: 'Strait of Hormuz Tension Zone',
      type: 'political',
      severity: 'high',
      center: [26.5, 56.0],
      radius: 100000,
      description: 'Political tensions - monitor security advisories'
    }
  ],
  restrictedZones: [
    {
      id: 'restricted_001',
      name: 'Naval Exercise Area',
      type: 'military',
      coordinates: [
        [22.0, 60.0],
        [25.0, 62.0],
        [24.0, 65.0],
        [21.0, 63.0],
        [22.0, 60.0]
      ],
      validUntil: '2025-01-15T23:59:59Z',
      description: 'Military naval exercises in progress - navigation prohibited'
    },
    {
      id: 'restricted_002',
      name: 'Marine Protected Area',
      type: 'environmental',
      coordinates: [
        [-8.0, 72.0],
        [-6.0, 74.0],
        [-10.0, 76.0],
        [-12.0, 74.0],
        [-8.0, 72.0]
      ],
      validUntil: 'permanent',
      description: 'Marine sanctuary - restricted access for conservation'
    }
  ],
  accidentLocations: [
    {
      id: 'accident_001',
      name: 'MV Cargo Collision',
      type: 'collision',
      severity: 'high',
      coordinates: [18.5, 70.2],
      date: '2025-01-01T14:30:00Z',
      description: 'Vessel collision reported - debris field present, avoid area'
    },
    {
      id: 'accident_002',
      name: 'Oil Spill Incident',
      type: 'environmental',
      severity: 'critical',
      coordinates: [10.2, 76.8],
      date: '2024-12-28T09:15:00Z',
      description: 'Oil spill cleanup in progress - navigation restricted'
    },
    {
      id: 'accident_003',
      name: 'Grounding Incident',
      type: 'grounding',
      severity: 'medium',
      coordinates: [-15.3, 60.1],
      date: '2024-12-30T16:45:00Z',
      description: 'Vessel aground - salvage operations underway'
    },
    {
      id: 'accident_004',
      name: 'Fire at Sea',
      type: 'fire',
      severity: 'high',
      coordinates: [8.7, 50.2],
      date: '2025-01-05T11:20:00Z',
      description: 'Vessel fire reported - emergency response in progress'
    },
    {
      id: 'accident_005',
      name: 'Man Overboard',
      type: 'rescue',
      severity: 'medium',
      coordinates: [1.2, 103.8],
      date: '2025-01-06T08:45:00Z',
      description: 'Search and rescue operation - vessels requested to assist'
    }
  ]
};

// Custom vessel icons based on status and selection
const createVesselIcon = (status, heading = 0, isSelected = false) => {
  const color = status === 'Moving' ? '#22c55e' : '#ef4444'; // Green for moving, red for anchored
  const size = isSelected ? 24 : 16;
  const borderWidth = isSelected ? 4 : 3;
  const borderColor = isSelected ? '#fbbf24' : 'white'; // Yellow border for selected
  
  return L.divIcon({
    className: 'custom-vessel-marker',
    html: `
      <div style="
        background-color: ${color};
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        border: ${borderWidth}px solid ${borderColor};
        box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        transform: rotate(${heading}deg);
        transition: all 0.3s ease;
        ${isSelected ? 'animation: pulse 2s infinite;' : ''}
      ">
        <div style="
          width: ${Math.round(size * 0.375)}px;
          height: ${Math.round(size * 0.375)}px;
          background-color: white;
          border-radius: 50%;
        "></div>
      </div>
      <style>
        @keyframes pulse {
          0%, 100% { transform: rotate(${heading}deg) scale(1); }
          50% { transform: rotate(${heading}deg) scale(1.1); }
        }
      </style>
    `,
    iconSize: [size + borderWidth * 2, size + borderWidth * 2],
    iconAnchor: [(size + borderWidth * 2) / 2, (size + borderWidth * 2) / 2],
    popupAnchor: [0, -(size + borderWidth * 2) / 2],
  });
};

// Create accident location markers
const createAccidentIcon = (type, severity) => {
  const colors = {
    collision: '#ef4444',
    environmental: '#f59e0b',
    grounding: '#8b5cf6'
  };
  
  const sizes = {
    critical: 20,
    high: 16,
    medium: 12
  };
  
  const color = colors[type] || '#ef4444';
  const size = sizes[severity] || 16;
  
  return L.divIcon({
    className: 'accident-marker',
    html: `
      <div style="
        background-color: ${color};
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: blink 2s infinite;
      ">
        <div style="
          width: 4px;
          height: 4px;
          background-color: white;
          border-radius: 50%;
        "></div>
      </div>
      <style>
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
      </style>
    `,
    iconSize: [size + 4, size + 4],
    iconAnchor: [(size + 4) / 2, (size + 4) / 2],
    popupAnchor: [0, -(size + 4) / 2],
  });
};

// Component to handle map interactions
const MapController = ({ selectedVessel, onMapReady }) => {
  const map = useMap();
  
  useEffect(() => {
    if (onMapReady) {
      onMapReady(map);
    }
  }, [map, onMapReady]);

  useEffect(() => {
    if (selectedVessel && map) {
      const sanitizedVessel = sanitizeVesselDataWithFallback(selectedVessel);
      // Only zoom if vessel has valid coordinates
      if (isValidLatLng(sanitizedVessel.lat, sanitizedVessel.lng)) {
        map.setView([sanitizedVessel.lat, sanitizedVessel.lng], 8, {
          animate: true,
          duration: 1.0
        });
      }
    }
  }, [selectedVessel, map]);

  return null;
};

// Safety Layers Component
const SafetyLayers = ({ layerVisibility, safetyData }) => {
  return (
    <>
      {/* Storm Zones */}
      {layerVisibility.stormZones && safetyData.stormZones.map((storm) => (
        <Polygon
          key={storm.id}
          positions={storm.coordinates}
          pathOptions={{
            color: storm.severity === 'high' ? '#dc2626' : '#f59e0b',
            fillColor: storm.severity === 'high' ? '#dc2626' : '#f59e0b',
            fillOpacity: 0.2,
            weight: 2,
            dashArray: '10, 5'
          }}
        >
          <Popup>
            <div className="safety-popup">
              <div className="font-bold text-lg mb-2 text-red-800">
                🌪️ {storm.name}
              </div>
              <div className="space-y-1 text-sm">
                <div><strong>Type:</strong> {storm.type.replace('_', ' ')}</div>
                <div><strong>Wind Speed:</strong> {storm.windSpeed} km/h</div>
                <div><strong>Severity:</strong> {storm.severity}</div>
                <div className="mt-2 text-xs text-gray-600">
                  {storm.description}
                </div>
                {storm.lastUpdated && (
                  <div className="text-xs text-gray-500 mt-1">
                    Updated: {new Date(storm.lastUpdated).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          </Popup>
        </Polygon>
      ))}

      {/* Piracy Zones */}
      {layerVisibility.piracyZones && safetyData.piracyZones.map((piracy) => (
        <Circle
          key={piracy.id}
          center={piracy.center}
          radius={piracy.radius}
          pathOptions={{
            color: piracy.severity === 'critical' ? '#991b1b' : piracy.severity === 'high' ? '#dc2626' : '#f59e0b',
            fillColor: piracy.severity === 'critical' ? '#991b1b' : piracy.severity === 'high' ? '#dc2626' : '#f59e0b',
            fillOpacity: 0.25,
            weight: 3,
            dashArray: '5, 5'
          }}
        >
          <Popup>
            <div className="safety-popup">
              <div className="font-bold text-lg mb-2 text-red-900">
                🏴‍☠️ {piracy.name}
              </div>
              <div className="space-y-1 text-sm">
                <div><strong>Type:</strong> {piracy.type.replace('_', ' ')}</div>
                <div><strong>Risk Level:</strong> {piracy.riskLevel}</div>
                <div><strong>Severity:</strong> {piracy.severity}</div>
                <div className="mt-2 text-xs text-gray-600">
                  {piracy.description}
                </div>
                {piracy.lastUpdated && (
                  <div className="text-xs text-gray-500 mt-1">
                    Updated: {new Date(piracy.lastUpdated).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          </Popup>
        </Circle>
      ))}

      {/* High Risk Waters */}
      {layerVisibility.highRiskWaters && safetyData.highRiskWaters.map((risk) => (
        <Circle
          key={risk.id}
          center={risk.center}
          radius={risk.radius}
          pathOptions={{
            color: risk.severity === 'critical' ? '#dc2626' : '#f59e0b',
            fillColor: risk.severity === 'critical' ? '#dc2626' : '#f59e0b',
            fillOpacity: 0.15,
            weight: 2
          }}
        >
          <Popup>
            <div className="safety-popup">
              <div className="font-bold text-lg mb-2 text-orange-800">
                ⚠️ {risk.name}
              </div>
              <div className="space-y-1 text-sm">
                <div><strong>Type:</strong> {risk.type}</div>
                <div><strong>Severity:</strong> {risk.severity}</div>
                <div className="mt-2 text-xs text-gray-600">
                  {risk.description}
                </div>
                {risk.lastUpdated && (
                  <div className="text-xs text-gray-500 mt-1">
                    Updated: {new Date(risk.lastUpdated).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          </Popup>
        </Circle>
      ))}

      {/* Restricted Zones */}
      {layerVisibility.restrictedZones && safetyData.restrictedZones.map((zone) => (
        <Polygon
          key={zone.id}
          positions={zone.coordinates}
          pathOptions={{
            color: zone.type === 'military' ? '#7c3aed' : '#059669',
            fillColor: zone.type === 'military' ? '#7c3aed' : '#059669',
            fillOpacity: 0.25,
            weight: 3
          }}
        >
          <Popup>
            <div className="safety-popup">
              <div className="font-bold text-lg mb-2 text-purple-800">
                🚫 {zone.name}
              </div>
              <div className="space-y-1 text-sm">
                <div><strong>Type:</strong> {zone.type}</div>
                <div><strong>Valid Until:</strong> {zone.validUntil === 'permanent' ? 'Permanent' : new Date(zone.validUntil).toLocaleDateString()}</div>
                <div className="mt-2 text-xs text-gray-600">
                  {zone.description}
                </div>
                {zone.lastUpdated && (
                  <div className="text-xs text-gray-500 mt-1">
                    Updated: {new Date(zone.lastUpdated).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          </Popup>
        </Polygon>
      ))}

      {/* Accident Locations */}
      {layerVisibility.accidentLocations && safetyData.accidentLocations.map((accident) => {
        // Validate accident coordinates before rendering
        if (!isValidLatLng(accident.coordinates[0], accident.coordinates[1])) {
          console.warn(`Invalid coordinates for accident ${accident.id}:`, accident.coordinates);
          return null;
        }
        
        return (
          <Marker
            key={accident.id}
            position={accident.coordinates}
            icon={createAccidentIcon(accident.type, accident.severity)}
          >
            <Popup>
              <div className="safety-popup">
                <div className="font-bold text-lg mb-2 text-red-800">
                  🚨 {accident.name}
                </div>
                <div className="space-y-1 text-sm">
                  <div><strong>Type:</strong> {accident.type}</div>
                  <div><strong>Severity:</strong> {accident.severity}</div>
                  <div><strong>Date:</strong> {new Date(accident.date).toLocaleDateString()}</div>
                  <div className="mt-2 text-xs text-gray-600">
                    {accident.description}
                  </div>
                  {accident.lastUpdated && (
                    <div className="text-xs text-gray-500 mt-1">
                      Updated: {new Date(accident.lastUpdated).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        );
      })}
    </>
  );
};

// Initial mock vessel data for the Indian Ocean region
// This data structure matches the expected AIS API schema for future backend integration
const initialMockVessels = [
  {
    // Unique vessel identifier (matches AIS API schema)
    id: 1,
    
    // Basic vessel information
    name: "MV Mumbai Express",
    imo_number: "9123456", // International Maritime Organization number
    mmsi: "356789012", // Maritime Mobile Service Identity
    call_sign: "VTMU123", // Radio call sign
    
    // Vessel classification
    type: "Container Ship",
    vessel_type: "Container Ship", // Alternative field name for compatibility
    cargo_type: "General Cargo",
    flag: "India",
    operator: "Maersk Line",
    
    // Position data (validated Indian Ocean coordinates)
    lat: 19.0760, // Mumbai port area - valid latitude
    lng: 72.8777, // Mumbai port area - valid longitude
    latitude: 19.0760, // Alternative field name for compatibility
    longitude: 72.8777, // Alternative field name for compatibility
    
    // Movement data
    speed: 18.5, // Speed over ground in knots
    heading: 45, // Course over ground in degrees (0-360)
    status: "Moving", // Vessel status: Moving, Anchored, Waiting
    
    // Voyage information
    destination: "Dubai",
    eta: "2025-01-02T14:30:00Z", // Estimated time of arrival (ISO format)
    
    // Additional metadata
    last_update: new Date().toISOString(),
    data_source: "mock" // Indicates this is mock data
  },
  {
    id: 2,
    name: "Colombo Trader",
    imo_number: "9234567",
    mmsi: "413456789",
    call_sign: "4PXY456",
    type: "Cargo Vessel",
    vessel_type: "Cargo Vessel",
    cargo_type: "Textiles",
    flag: "Sri Lanka",
    operator: "CMA CGM",
    
    // Colombo port area - valid coordinates
    lat: 6.9271,
    lng: 79.8612,
    latitude: 6.9271,
    longitude: 79.8612,
    
    speed: 0, // Anchored vessel
    heading: 0,
    status: "Anchored",
    destination: "Singapore",
    eta: "2025-01-03T08:00:00Z",
    last_update: new Date().toISOString(),
    data_source: "mock"
  },
  {
    id: 3,
    name: "Indian Ocean Pioneer",
    imo_number: "9345678",
    mmsi: "636123456",
    call_sign: "5LMN789",
    type: "Tanker",
    vessel_type: "Tanker",
    cargo_type: "Crude Oil",
    flag: "Liberia",
    operator: "Shell",
    
    // Mauritius area - valid coordinates
    lat: -20.1609,
    lng: 57.5012,
    latitude: -20.1609,
    longitude: 57.5012,
    
    speed: 14.2,
    heading: 120,
    status: "Moving",
    destination: "Port Louis",
    eta: "2025-01-04T12:00:00Z",
    last_update: new Date().toISOString(),
    data_source: "mock"
  },
  {
    id: 4,
    name: "Chennai Star",
    imo_number: "9456789",
    mmsi: "419876543",
    call_sign: "VTCH001",
    type: "Bulk Carrier",
    vessel_type: "Bulk Carrier",
    cargo_type: "Iron Ore",
    flag: "Marshall Islands",
    operator: "BHP",
    
    // Chennai port area - valid coordinates
    lat: 13.0827,
    lng: 80.2707,
    latitude: 13.0827,
    longitude: 80.2707,
    
    speed: 16.8,
    heading: 270,
    status: "Moving",
    destination: "Karachi",
    eta: "2025-01-05T18:30:00Z",
    last_update: new Date().toISOString(),
    data_source: "mock"
  },
  {
    id: 5,
    name: "Arabian Sea Voyager",
    imo_number: "9567890",
    mmsi: "470123789",
    call_sign: "A6ABC123",
    type: "Container Ship",
    vessel_type: "Container Ship",
    cargo_type: "Electronics",
    flag: "UAE",
    operator: "COSCO",
    
    // Arabian Sea - valid coordinates
    lat: 23.0225,
    lng: 72.5714,
    latitude: 23.0225,
    longitude: 72.5714,
    
    speed: 0, // Waiting vessel
    heading: 0,
    status: "Anchored",
    destination: "Mumbai",
    eta: "2025-01-06T06:00:00Z",
    last_update: new Date().toISOString(),
    data_source: "mock"
  },
  {
    id: 6,
    name: "Maldives Carrier",
    imo_number: "9678901",
    mmsi: "455234567",
    call_sign: "8QMV456",
    type: "Passenger Ferry",
    vessel_type: "Passenger Ferry",
    cargo_type: "Passengers",
    flag: "Maldives",
    operator: "Maldivian",
    
    // Maldives area - valid coordinates
    lat: 4.1755,
    lng: 73.5093,
    latitude: 4.1755,
    longitude: 73.5093,
    
    speed: 22.1,
    heading: 180,
    status: "Moving",
    destination: "Male",
    eta: "2025-01-02T20:15:00Z",
    last_update: new Date().toISOString(),
    data_source: "mock"
  },
  {
    id: 7,
    name: "Bay of Bengal Explorer",
    imo_number: "9789012",
    mmsi: "405345678",
    call_sign: "S2XYZ789",
    type: "Research Vessel",
    vessel_type: "Research Vessel",
    cargo_type: "Scientific Equipment",
    flag: "Bangladesh",
    operator: "Research Institute",
    
    // Bay of Bengal - valid coordinates
    lat: 21.4272,
    lng: 92.0058,
    latitude: 21.4272,
    longitude: 92.0058,
    
    speed: 0, // Research station keeping
    heading: 0,
    status: "Anchored",
    destination: "Chittagong",
    eta: "2025-01-07T14:00:00Z",
    last_update: new Date().toISOString(),
    data_source: "mock"
  },
  {
    id: 8,
    name: "Seychelles Navigator",
    imo_number: "9890123",
    mmsi: "664456789",
    call_sign: "S7NAV001",
    type: "Cruise Ship",
    vessel_type: "Cruise Ship",
    cargo_type: "Passengers",
    flag: "Seychelles",
    operator: "Royal Caribbean",
    
    // Seychelles area - valid coordinates
    lat: -4.6796,
    lng: 55.4920,
    latitude: -4.6796,
    longitude: 55.4920,
    
    speed: 19.5,
    heading: 315,
    status: "Moving",
    destination: "Victoria",
    eta: "2025-01-03T16:45:00Z",
    last_update: new Date().toISOString(),
    data_source: "mock"
  }
];

// Validation function for mock data integrity
const validateMockVesselData = () => {
  const invalidVessels = [];
  
  initialMockVessels.forEach(vessel => {
    // Check for required fields
    if (!vessel.id || !vessel.name) {
      invalidVessels.push(`${vessel.name || 'Unknown'}: Missing ID or name`);
    }
    
    // Validate coordinates
    if (!isValidLatLng(vessel.lat, vessel.lng)) {
      invalidVessels.push(`${vessel.name}: Invalid coordinates (${vessel.lat}, ${vessel.lng})`);
    }
    
    // Validate numeric fields
    if (typeof vessel.speed !== 'number' || isNaN(vessel.speed)) {
      invalidVessels.push(`${vessel.name}: Invalid speed value`);
    }
    
    if (typeof vessel.heading !== 'number' || isNaN(vessel.heading)) {
      invalidVessels.push(`${vessel.name}: Invalid heading value`);
    }
  });
  
  if (invalidVessels.length > 0) {
    console.error('Mock vessel data validation failed:', invalidVessels);
    return false;
  }
  
  console.log('Mock vessel data validation passed: All vessels have valid coordinates and data');
  return true;
};

// Run validation on module load (development only)
if (process.env.NODE_ENV === 'development') {
  validateMockVesselData();
}

const VesselMap = forwardRef(({ vessels: propVessels, onVesselClick, selectedVessel, showSafetyLayers = true }, ref) => {
  // State for real-time vessel data
  const [liveVessels, setLiveVessels] = useState(propVessels || initialMockVessels);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [mapInstance, setMapInstance] = useState(null);
  const [mapError, setMapError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Search and filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [vesselTypeFilter, setVesselTypeFilter] = useState('');
  const [flagFilter, setFlagFilter] = useState('');
  const [cargoFilter, setCargoFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  
  // Safety layer visibility state
  const [layerVisibility, setLayerVisibility] = useState({
    stormZones: true,
    piracyZones: true,
    highRiskWaters: true,
    restrictedZones: true,
    accidentLocations: true
  });

  // Safety data state
  const [safetyData, setSafetyData] = useState(mockSafetyData);
  const [safetyDataLoading, setSafetyDataLoading] = useState(false);
  const [safetyDataError, setSafetyDataError] = useState(null);
  const [lastSafetyUpdate, setLastSafetyUpdate] = useState(new Date());
  
  // Refs for cleanup
  const intervalRef = useRef(null);
  const safetyIntervalRef = useRef(null);
  
  // Indian Ocean center coordinates
  const mapCenter = [-10.0, 75.0];
  const mapZoom = 5;

  // Expose methods to parent component
  useImperativeHandle(ref, () => ({
    zoomToVessel: (vessel) => {
      if (mapInstance && vessel) {
        try {
          const sanitizedVessel = sanitizeVesselDataWithFallback(vessel);
          if (isValidLatLng(sanitizedVessel.lat, sanitizedVessel.lng)) {
            mapInstance.setView([sanitizedVessel.lat, sanitizedVessel.lng], 8, {
              animate: true,
              duration: 1.0
            });
          } else {
            console.warn(`Cannot zoom to vessel ${vessel.id || vessel.name} with invalid coordinates:`, vessel.lat, vessel.lng);
          }
        } catch (error) {
          console.error('Error zooming to vessel:', error);
          setMapError(`Failed to zoom to vessel: ${error.message}`);
        }
      }
    },
    getVessels: () => liveVessels
  }));

  // Fetch safety data from backend APIs
  const fetchSafetyData = useCallback(async () => {
    setSafetyDataLoading(true);
    setSafetyDataError(null);
    
    try {
      // Fetch all safety data in parallel
      const [stormResponse, piracyResponse, restrictedResponse, accidentResponse] = await Promise.allSettled([
        fetch(`${API_BASE_URL}/api/safety/storms/`, {
          headers: { 'Content-Type': 'application/json' }
        }),
        fetch(`${API_BASE_URL}/api/safety/piracy-zones/`, {
          headers: { 'Content-Type': 'application/json' }
        }),
        fetch(`${API_BASE_URL}/api/safety/restricted-zones/`, {
          headers: { 'Content-Type': 'application/json' }
        }),
        fetch(`${API_BASE_URL}/api/safety/accidents/`, {
          headers: { 'Content-Type': 'application/json' }
        })
      ]);

      const newSafetyData = { ...mockSafetyData }; // Start with mock data as fallback

      // Process storm zones
      if (stormResponse.status === 'fulfilled' && stormResponse.value.ok) {
        const stormData = await stormResponse.value.json();
        const storms = Array.isArray(stormData) ? stormData : stormData.results || stormData.storms || [];
        if (storms.length > 0) {
          newSafetyData.stormZones = storms.map(storm => ({
            id: storm.id || storm.storm_id,
            name: storm.name || storm.storm_name,
            type: storm.type || storm.storm_type || 'storm',
            severity: storm.severity || 'medium',
            coordinates: storm.coordinates || storm.polygon || [],
            windSpeed: storm.wind_speed || storm.windSpeed || 0,
            description: storm.description || `${storm.type || 'Storm'} system`,
            lastUpdated: storm.last_updated || storm.updated_at
          }));
          console.log(`Loaded ${storms.length} storm zones from API`);
        }
      } else {
        console.warn('Failed to fetch storm data, using mock data');
      }

      // Process piracy zones
      if (piracyResponse.status === 'fulfilled' && piracyResponse.value.ok) {
        const piracyData = await piracyResponse.value.json();
        const piracyZones = Array.isArray(piracyData) ? piracyData : piracyData.results || piracyData.piracy_zones || [];
        if (piracyZones.length > 0) {
          newSafetyData.piracyZones = piracyZones.map(zone => ({
            id: zone.id || zone.zone_id,
            name: zone.name || zone.zone_name,
            type: zone.type || zone.zone_type || 'piracy_risk',
            severity: zone.severity || zone.risk_level || 'medium',
            center: zone.center || [zone.latitude, zone.longitude] || [0, 0],
            radius: zone.radius || zone.radius_meters || 100000,
            riskLevel: zone.risk_level || zone.riskLevel || 'Medium',
            description: zone.description || `Piracy risk area - ${zone.risk_level || 'medium'} threat level`,
            lastUpdated: zone.last_updated || zone.updated_at
          }));
          console.log(`Loaded ${piracyZones.length} piracy zones from API`);
        }
      } else {
        console.warn('Failed to fetch piracy data, using mock data');
      }

      // Process restricted zones
      if (restrictedResponse.status === 'fulfilled' && restrictedResponse.value.ok) {
        const restrictedData = await restrictedResponse.value.json();
        const restrictedZones = Array.isArray(restrictedData) ? restrictedData : restrictedData.results || restrictedData.restricted_zones || [];
        if (restrictedZones.length > 0) {
          newSafetyData.restrictedZones = restrictedZones.map(zone => ({
            id: zone.id || zone.zone_id,
            name: zone.name || zone.zone_name,
            type: zone.type || zone.zone_type || 'restricted',
            coordinates: zone.coordinates || zone.polygon || [],
            validUntil: zone.valid_until || zone.expires_at || 'permanent',
            description: zone.description || `Restricted area - ${zone.type || 'navigation prohibited'}`,
            lastUpdated: zone.last_updated || zone.updated_at
          }));
          console.log(`Loaded ${restrictedZones.length} restricted zones from API`);
        }
      } else {
        console.warn('Failed to fetch restricted zones data, using mock data');
      }

      // Process accident locations
      if (accidentResponse.status === 'fulfilled' && accidentResponse.value.ok) {
        const accidentData = await accidentResponse.value.json();
        const accidents = Array.isArray(accidentData) ? accidentData : accidentData.results || accidentData.accidents || [];
        if (accidents.length > 0) {
          newSafetyData.accidentLocations = accidents.map(accident => ({
            id: accident.id || accident.incident_id,
            name: accident.name || accident.incident_name || accident.title,
            type: accident.type || accident.incident_type || 'accident',
            severity: accident.severity || accident.risk_level || 'medium',
            coordinates: accident.coordinates || [accident.latitude, accident.longitude] || [0, 0],
            date: accident.date || accident.incident_date || accident.created_at,
            description: accident.description || `${accident.type || 'Incident'} reported`,
            lastUpdated: accident.last_updated || accident.updated_at
          }));
          console.log(`Loaded ${accidents.length} accident locations from API`);
        }
      } else {
        console.warn('Failed to fetch accident data, using mock data');
      }

      // High risk waters can be derived from piracy zones or fetched separately
      newSafetyData.highRiskWaters = newSafetyData.piracyZones.filter(zone => 
        zone.severity === 'critical' || zone.severity === 'high'
      ).map(zone => ({
        ...zone,
        type: 'piracy' // Ensure consistent type for high risk waters
      }));

      setSafetyData(newSafetyData);
      setLastSafetyUpdate(new Date());
      setSafetyDataError(null);
      
      console.log('Safety data updated successfully');
      
    } catch (error) {
      console.error('Error fetching safety data:', error);
      setSafetyDataError(`Failed to load safety data: ${error.message}`);
      // Keep existing data (mock or previously loaded) on error
    } finally {
      setSafetyDataLoading(false);
    }
  }, []);

  // Toggle layer visibility
  const toggleLayer = (layerName) => {
    try {
      setLayerVisibility(prev => ({
        ...prev,
        [layerName]: !prev[layerName]
      }));
    } catch (error) {
      console.error('Error toggling layer:', error);
    }
  };

  // Fetch live vessel data from backend
  const fetchLiveVesselData = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/vessels/`, {
        headers: {
          'Content-Type': 'application/json',
          // Add authorization header if needed
          // 'Authorization': `Bearer ${token}`
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const vessels = Array.isArray(data) ? data : data.results || data.vessels || [];
      
      // Sanitize vessel data
      const sanitizedVessels = vessels.map(vessel => sanitizeVesselDataWithFallback(vessel));
      
      setLiveVessels(sanitizedVessels);
      setLastUpdate(new Date());
      setIsConnected(true);
      
      console.log(`Fetched ${sanitizedVessels.length} vessels from API`);
      
    } catch (error) {
      console.warn('Failed to fetch live vessel data, using mock data:', error.message);
      setIsConnected(false);
      // Fallback to mock data if API fails
      if (liveVessels.length === 0) {
        setLiveVessels(initialMockVessels);
      }
    }
  }, [liveVessels.length]); // Only depend on length to avoid unnecessary re-renders

  // Filter vessels based on search and filter criteria
  const filteredVessels = useMemo(() => {
    return liveVessels.filter(vessel => {
      // Search by name or IMO
      const matchesSearch = !searchTerm || 
        vessel.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        vessel.imo_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        vessel.mmsi?.includes(searchTerm);
      
      // Filter by vessel type
      const matchesType = !vesselTypeFilter || 
        vessel.type === vesselTypeFilter || 
        vessel.vessel_type === vesselTypeFilter;
      
      // Filter by flag
      const matchesFlag = !flagFilter || vessel.flag === flagFilter;
      
      // Filter by cargo
      const matchesCargo = !cargoFilter || 
        vessel.cargo_type === cargoFilter ||
        vessel.cargo === cargoFilter;
      
      return matchesSearch && matchesType && matchesFlag && matchesCargo;
    });
  }, [liveVessels, searchTerm, vesselTypeFilter, flagFilter, cargoFilter]);

  // Get unique values for filter dropdowns
  const vesselTypes = useMemo(() => {
    const types = [...new Set(liveVessels.map(v => v.type || v.vessel_type).filter(Boolean))];
    return types.sort();
  }, [liveVessels]);

  const flags = useMemo(() => {
    const flagList = [...new Set(liveVessels.map(v => v.flag).filter(Boolean))];
    return flagList.sort();
  }, [liveVessels]);

  const cargoTypes = useMemo(() => {
    const types = [...new Set(liveVessels.map(v => v.cargo_type || v.cargo).filter(Boolean))];
    return types.sort();
  }, [liveVessels]);

  // Initialize live data fetching and real-time updates
  useEffect(() => {
    let mounted = true;
    
    const initializeVesselData = async () => {
      setIsLoading(true);
      
      try {
        // Initial fetch of live vessel data
        await fetchLiveVesselData();
        
        if (!mounted) return;
        
        setIsLoading(false);
        
        // Set up periodic updates every 30 seconds for live data
        intervalRef.current = setInterval(async () => {
          if (!mounted) return;
          
          try {
            await fetchLiveVesselData();
          } catch (error) {
            console.error('Error in periodic vessel update:', error);
          }
        }, 30000); // Update every 30 seconds
        
      } catch (error) {
        console.error('Error initializing vessel data:', error);
        setMapError(`Initialization error: ${error.message}`);
        setIsLoading(false);
      }
    };
    
    initializeVesselData();
    
    // Cleanup function
    return () => {
      mounted = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchLiveVesselData]); // Include fetchLiveVesselData in dependencies

  // Initialize safety data fetching and periodic updates
  useEffect(() => {
    let mounted = true;
    
    const initializeSafetyData = async () => {
      try {
        // Initial fetch of safety data
        await fetchSafetyData();
        
        if (!mounted) return;
        
        // Set up periodic updates every 5 minutes for safety data (less frequent than vessel data)
        safetyIntervalRef.current = setInterval(async () => {
          if (!mounted) return;
          
          try {
            await fetchSafetyData();
          } catch (error) {
            console.error('Error in periodic safety data update:', error);
          }
        }, 300000); // Update every 5 minutes
        
      } catch (error) {
        console.error('Error initializing safety data:', error);
        setSafetyDataError(`Safety data initialization error: ${error.message}`);
      }
    };
    
    initializeSafetyData();
    
    // Cleanup function
    return () => {
      mounted = false;
      if (safetyIntervalRef.current) {
        clearInterval(safetyIntervalRef.current);
      }
    };
  }, [fetchSafetyData]);

  // Update vessels when props change
  useEffect(() => {
    try {
      if (propVessels && Array.isArray(propVessels) && propVessels.length > 0) {
        // Sanitize and validate incoming vessel data with safe fallbacks
        const sanitizedVessels = propVessels.map(vessel => {
          try {
            return sanitizeVesselDataWithFallback(vessel);
          } catch (error) {
            console.error(`Error sanitizing vessel ${vessel?.id || 'unknown'}:`, error);
            return null; // Will be filtered out
          }
        }).filter(Boolean); // Remove null entries
        
        if (sanitizedVessels.length > 0) {
          setLiveVessels(sanitizedVessels);
        } else {
          console.warn('No valid vessels after sanitization, keeping current vessels');
        }
      }
    } catch (error) {
      console.error('Error updating vessels from props:', error);
      setMapError(`Props update error: ${error.message}`);
    }
  }, [propVessels]);

  // Filter vessels to only include those with valid coordinates from filtered results
  const validVessels = useMemo(() => {
    try {
      if (!Array.isArray(filteredVessels)) {
        console.warn('filteredVessels is not an array, using empty array');
        return [];
      }
      
      return filteredVessels.filter(vessel => {
        try {
          if (!vessel || typeof vessel !== 'object') {
            console.warn('Invalid vessel object:', vessel);
            return false;
          }
          
          const sanitizedVessel = sanitizeVesselDataWithFallback(vessel);
          const isValid = isValidLatLng(sanitizedVessel.lat, sanitizedVessel.lng);
          
          if (!isValid) {
            console.warn(`Filtering out vessel ${vessel.id || vessel.name} with invalid coordinates:`, vessel.lat, vessel.lng);
          }
          
          return isValid;
        } catch (error) {
          console.error(`Error validating vessel ${vessel?.id || 'unknown'}:`, error);
          return false;
        }
      });
    } catch (error) {
      console.error('Error filtering valid vessels:', error);
      return [];
    }
  }, [filteredVessels]);

  // Error boundary-style error display
  if (mapError) {
    return (
      <div className="w-full h-full relative bg-gray-100 flex items-center justify-center">
        <div className="text-center p-8">
          <div className="text-red-600 text-lg font-semibold mb-2">
            ⚠️ Map Error
          </div>
          <div className="text-gray-700 text-sm mb-4">
            {mapError}
          </div>
          <button
            onClick={() => {
              setMapError(null);
              setIsLoading(true);
              // Trigger re-initialization
              window.location.reload();
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Reload Map
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="w-full h-full relative bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-gray-700 font-medium">Loading Maritime Map...</div>
          <div className="text-gray-500 text-sm mt-2">Initializing vessel tracking system</div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      {/* Connection Status Indicator */}
      <div className="absolute top-4 right-4 z-[1000] bg-white/90 backdrop-blur-sm p-2 rounded-lg shadow-lg">
        <div className="flex items-center gap-2 text-sm">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-gray-800 font-medium">
            {isConnected ? 'Live Data' : 'Mock Data'}
          </span>
        </div>
        <div className="text-xs text-gray-600 mt-1">
          Vessels: {lastUpdate.toLocaleTimeString()}
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-600">
          <div className={`w-2 h-2 rounded-full ${safetyDataError ? 'bg-red-400' : safetyDataLoading ? 'bg-yellow-400' : 'bg-green-400'}`}></div>
          <span>Safety: {lastSafetyUpdate.toLocaleTimeString()}</span>
        </div>
        <div className="text-xs text-blue-600 mt-1">
          {filteredVessels.length} of {liveVessels.length} vessels shown
        </div>
      </div>

      {/* Search and Filter Panel */}
      <div className="absolute top-4 right-48 z-[1000]">
        <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg">
          {/* Search Bar */}
          <div className="p-3 border-b border-gray-200">
            <div className="relative">
              <input
                type="text"
                placeholder="Search by name or IMO..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-64 px-3 py-2 pr-8 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <svg className="absolute right-2 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
          
          {/* Filter Toggle */}
          <div className="p-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 transition-colors"
            >
              <svg className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              Filters
            </button>
          </div>
          
          {/* Filter Options */}
          {showFilters && (
            <div className="p-3 border-t border-gray-200 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Vessel Type</label>
                <select
                  value={vesselTypeFilter}
                  onChange={(e) => setVesselTypeFilter(e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All Types</option>
                  {vesselTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Flag</label>
                <select
                  value={flagFilter}
                  onChange={(e) => setFlagFilter(e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All Flags</option>
                  {flags.map(flag => (
                    <option key={flag} value={flag}>{flag}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Cargo Type</label>
                <select
                  value={cargoFilter}
                  onChange={(e) => setCargoFilter(e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All Cargo</option>
                  {cargoTypes.map(cargo => (
                    <option key={cargo} value={cargo}>{cargo}</option>
                  ))}
                </select>
              </div>
              
              {/* Clear Filters */}
              {(searchTerm || vesselTypeFilter || flagFilter || cargoFilter) && (
                <button
                  onClick={() => {
                    setSearchTerm('');
                    setVesselTypeFilter('');
                    setFlagFilter('');
                    setCargoFilter('');
                  }}
                  className="w-full px-2 py-1 text-xs text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Clear All Filters
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Safety Layers Control Panel */}
      {showSafetyLayers && (
        <div className="absolute top-4 left-4 z-[1000] bg-white/95 backdrop-blur-sm p-4 rounded-lg shadow-lg max-w-xs">
          <div className="flex justify-between items-center mb-3">
            <div className="text-sm font-semibold text-gray-800">
              Safety Layers
            </div>
            {safetyDataLoading && (
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            )}
          </div>
          
          {safetyDataError && (
            <div className="mb-3 p-2 bg-red-100 border border-red-300 rounded text-xs text-red-700">
              {safetyDataError}
              <button
                onClick={fetchSafetyData}
                className="ml-2 text-red-800 hover:text-red-900 underline"
              >
                Retry
              </button>
            </div>
          )}
          
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility.stormZones}
                onChange={() => toggleLayer('stormZones')}
                className="rounded"
              />
              <div className="w-3 h-3 bg-red-500 rounded border border-white"></div>
              <span className="text-gray-700">Storm Zones ({safetyData.stormZones.length})</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility.piracyZones}
                onChange={() => toggleLayer('piracyZones')}
                className="rounded"
              />
              <div className="w-3 h-3 bg-red-700 rounded-full border border-white"></div>
              <span className="text-gray-700">Piracy Zones ({safetyData.piracyZones.length})</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility.highRiskWaters}
                onChange={() => toggleLayer('highRiskWaters')}
                className="rounded"
              />
              <div className="w-3 h-3 bg-orange-500 rounded-full border border-white"></div>
              <span className="text-gray-700">High Risk Waters ({safetyData.highRiskWaters.length})</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility.restrictedZones}
                onChange={() => toggleLayer('restrictedZones')}
                className="rounded"
              />
              <div className="w-3 h-3 bg-purple-500 rounded border border-white"></div>
              <span className="text-gray-700">Restricted Zones ({safetyData.restrictedZones.length})</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility.accidentLocations}
                onChange={() => toggleLayer('accidentLocations')}
                className="rounded"
              />
              <div className="w-3 h-3 bg-red-600 rounded-full border border-white animate-pulse"></div>
              <span className="text-gray-700">Accident Locations ({safetyData.accidentLocations.length})</span>
            </label>
          </div>
          
          <div className="mt-3 pt-2 border-t border-gray-300">
            <div className="text-xs text-gray-600">
              Safety data updated: {lastSafetyUpdate.toLocaleTimeString()}
            </div>
            <button
              onClick={fetchSafetyData}
              disabled={safetyDataLoading}
              className="mt-1 text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {safetyDataLoading ? 'Updating...' : 'Refresh Safety Data'}
            </button>
          </div>
        </div>
      )}

      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ width: '100%', height: '100%' }}
        className="vessel-tracking-map"
        whenCreated={(map) => {
          try {
            setMapInstance(map);
          } catch (error) {
            console.error('Error setting map instance:', error);
          }
        }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          errorTileUrl="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        />
        
        <MapController 
          selectedVessel={selectedVessel} 
          onMapReady={setMapInstance}
        />
        
        {/* Safety Layers */}
        {showSafetyLayers && (
          <SafetyLayers layerVisibility={layerVisibility} safetyData={safetyData} />
        )}
        
        {/* Vessel Markers - Only render vessels with valid coordinates */}
        {validVessels.length > 0 ? (
          validVessels.map((vessel) => {
            try {
              const sanitizedVessel = sanitizeVesselDataWithFallback(vessel);
              const isSelected = selectedVessel && selectedVessel.id === vessel.id;
              
              // Additional safety check before rendering marker
              if (!isValidLatLng(sanitizedVessel.lat, sanitizedVessel.lng)) {
                console.warn(`Skipping render for vessel ${vessel.id || vessel.name} with invalid coordinates`);
                return null;
              }
              
              return (
                <Marker
                  key={vessel.id || `vessel-${Math.random()}`}
                  position={[sanitizedVessel.lat, sanitizedVessel.lng]}
                  icon={createVesselIcon(vessel.status, vessel.heading, isSelected)}
                  eventHandlers={{
                    click: () => {
                      try {
                        if (onVesselClick) {
                          onVesselClick(vessel);
                        }
                      } catch (error) {
                        console.error('Error in vessel click handler:', error);
                      }
                    }
                  }}
                >
                  <Popup>
                    <div className="vessel-popup">
                      <div className="font-bold text-lg mb-2 text-gray-800">
                        {vessel.name || 'Unknown Vessel'}
                        {vessel._coordinatesReset && (
                          <span className="ml-2 text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
                            Position Reset
                          </span>
                        )}
                      </div>
                      <div className="space-y-1 text-sm text-gray-700">
                        <div className="flex justify-between">
                          <span className="font-medium">Type:</span>
                          <span>{vessel.type || vessel.vessel_type || 'Unknown'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Speed:</span>
                          <span className="font-mono">{(vessel.speed || 0).toFixed(1)} knots</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Heading:</span>
                          <span className="font-mono">{Math.round(vessel.heading || 0)}°</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Status:</span>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            vessel.status === 'Moving' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {vessel.status || 'Unknown'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Destination:</span>
                          <span>{vessel.destination || 'Unknown'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Position:</span>
                          <span className="font-mono text-xs">
                            {sanitizedVessel.lat.toFixed(4)}, {sanitizedVessel.lng.toFixed(4)}
                          </span>
                        </div>
                        {vessel.imo_number && (
                          <div className="flex justify-between">
                            <span className="font-medium">IMO:</span>
                            <span className="font-mono text-xs">{vessel.imo_number}</span>
                          </div>
                        )}
                      </div>
                      <div className="mt-2 text-xs text-gray-500 border-t pt-2">
                        🔴 Live tracking active
                        {vessel._coordinatesReset && (
                          <div className="text-orange-600 mt-1">
                            ⚠️ Coordinates were reset to safe default
                          </div>
                        )}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            } catch (error) {
              console.error(`Error rendering vessel ${vessel?.id || 'unknown'}:`, error);
              return null;
            }
          }).filter(Boolean) // Remove null entries
        ) : (
          // Fallback when no valid vessels exist
          <Marker
            position={mapCenter}
            icon={L.divIcon({
              className: 'no-vessels-marker',
              html: `
                <div style="
                  background-color: #6b7280;
                  color: white;
                  padding: 8px 12px;
                  border-radius: 8px;
                  font-size: 12px;
                  font-weight: 500;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                  white-space: nowrap;
                ">
                  📍 No vessels currently visible
                </div>
              `,
              iconSize: [200, 40],
              iconAnchor: [100, 20],
            })}
          >
            <Popup>
              <div className="text-center p-2">
                <div className="font-medium text-gray-800 mb-2">No Vessels Available</div>
                <div className="text-sm text-gray-600">
                  No valid vessel data is currently available for display.
                  This could be due to:
                </div>
                <ul className="text-xs text-gray-500 mt-2 text-left">
                  <li>• Data loading in progress</li>
                  <li>• Network connectivity issues</li>
                  <li>• Invalid coordinate data</li>
                </ul>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>
      
      {/* Enhanced Map Legend */}
      <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm p-3 rounded-lg shadow-lg z-[1000] max-w-xs">
        <div className="text-sm font-semibold text-gray-800 mb-2">
          Map Legend
        </div>
        
        {/* Vessel Status */}
        <div className="mb-3">
          <div className="text-xs font-medium text-gray-700 mb-1">Vessels ({validVessels.length})</div>
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded-full border-2 border-white shadow"></div>
              <span className="text-gray-700">Moving</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 rounded-full border-2 border-white shadow"></div>
              <span className="text-gray-700">Anchored</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded-full border-4 border-yellow-400 shadow"></div>
              <span className="text-gray-700">Selected</span>
            </div>
          </div>
        </div>

        {/* Safety Layers Legend */}
        {showSafetyLayers && (
          <div>
            <div className="text-xs font-medium text-gray-700 mb-1">Safety Layers</div>
            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 border border-red-600"></div>
                <span className="text-gray-700">Storm Zones</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-700 rounded-full border border-white"></div>
                <span className="text-gray-700">Piracy Zones</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-orange-500 rounded-full border border-white"></div>
                <span className="text-gray-700">High Risk Waters</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-500 border border-purple-600"></div>
                <span className="text-gray-700">Restricted Zones</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-600 rounded-full border border-white animate-pulse"></div>
                <span className="text-gray-700">Accidents</span>
              </div>
            </div>
          </div>
        )}
        
        <div className="mt-2 pt-2 border-t border-gray-300">
          <div className="text-xs text-gray-600">
            📡 Real-time updates every 2.5s
          </div>
        </div>
      </div>
    </div>
  );
});

VesselMap.displayName = 'VesselMap';

export default VesselMap;