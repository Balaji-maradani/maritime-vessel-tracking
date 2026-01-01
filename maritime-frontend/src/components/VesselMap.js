import React, { useState, useEffect, useRef, useImperativeHandle, forwardRef, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

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

// Mock NOAA-style safety data
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
const SafetyLayers = ({ layerVisibility }) => {
  return (
    <>
      {/* Storm Zones */}
      {layerVisibility.stormZones && mockSafetyData.stormZones.map((storm) => (
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
              </div>
            </div>
          </Popup>
        </Polygon>
      ))}

      {/* High Risk Waters */}
      {layerVisibility.highRiskWaters && mockSafetyData.highRiskWaters.map((risk) => (
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
              </div>
            </div>
          </Popup>
        </Circle>
      ))}

      {/* Restricted Zones */}
      {layerVisibility.restrictedZones && mockSafetyData.restrictedZones.map((zone) => (
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
              </div>
            </div>
          </Popup>
        </Polygon>
      ))}

      {/* Accident Locations */}
      {layerVisibility.accidentLocations && mockSafetyData.accidentLocations.map((accident) => {
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
                </div>
              </div>
            </Popup>
          </Marker>
        );
      })}
    </>
  );
};

// Mock WebSocket simulation class
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
    
    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 100);
  }
  
  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) this.onclose();
  }
  
  send(data) {
    // Mock send - in real implementation this would send to server
    console.log('Mock WebSocket send:', data);
  }
}

// Generate realistic movement for vessels with enhanced safety
const generateVesselMovement = (vessel) => {
  // First, sanitize and validate the vessel data with safe fallbacks
  const sanitizedVessel = sanitizeVesselDataWithFallback(vessel);
  
  // Double-check that we have valid coordinates after sanitization
  if (!isValidLatLng(sanitizedVessel.lat, sanitizedVessel.lng)) {
    console.warn(`Critical: Vessel ${vessel.id || vessel.name} still has invalid coordinates after sanitization, skipping movement`);
    return vessel; // Return original vessel unchanged as last resort
  }
  
  // Ensure speed and heading are valid numbers
  let speed = sanitizedVessel.speed || 0;
  let heading = sanitizedVessel.heading || 0;
  
  if (typeof speed !== 'number' || isNaN(speed) || !isFinite(speed)) {
    speed = 0;
  }
  if (typeof heading !== 'number' || isNaN(heading) || !isFinite(heading)) {
    heading = 0;
  }
  
  // Clamp speed to reasonable range (0-50 knots)
  speed = Math.max(0, Math.min(50, speed));
  
  // Normalize heading to 0-360 degrees
  heading = ((heading % 360) + 360) % 360;
  
  if (sanitizedVessel.status !== 'Moving') {
    // Anchored vessels have minimal drift
    const driftLat = (Math.random() - 0.5) * 0.001;
    const driftLng = (Math.random() - 0.5) * 0.001;
    
    let newLat = sanitizedVessel.lat + driftLat;
    let newLng = sanitizedVessel.lng + driftLng;
    
    // Clamp the new coordinates to valid ranges
    newLat = clampLatitude(newLat);
    newLng = clampLongitude(newLng);
    
    // Validate the new coordinates before returning
    if (!isValidLatLng(newLat, newLng)) {
      console.warn(`Generated invalid drift coordinates for anchored vessel ${vessel.id || vessel.name}, using original position`);
      newLat = sanitizedVessel.lat;
      newLng = sanitizedVessel.lng;
    }
    
    return {
      ...sanitizedVessel,
      lat: newLat,
      lng: newLng,
      speed: Math.max(0, speed + (Math.random() - 0.5) * 0.5),
      heading: heading
    };
  }
  
  // Moving vessels follow their heading with some variation
  const headingRad = (heading * Math.PI) / 180;
  const speedKnots = speed;
  const distancePerUpdate = (speedKnots * 0.000154) / 120; // Approximate nautical miles to degrees per 2-3 seconds
  
  // Calculate movement with safety checks
  const latMovement = Math.cos(headingRad) * distancePerUpdate + (Math.random() - 0.5) * 0.002;
  const lngMovement = Math.sin(headingRad) * distancePerUpdate + (Math.random() - 0.5) * 0.002;
  
  // Validate movement calculations
  if (!isFinite(latMovement) || !isFinite(lngMovement) || isNaN(latMovement) || isNaN(lngMovement)) {
    console.warn(`Invalid movement calculation for vessel ${vessel.id || vessel.name}, using minimal drift instead`);
    const safeDriftLat = (Math.random() - 0.5) * 0.001;
    const safeDriftLng = (Math.random() - 0.5) * 0.001;
    
    return {
      ...sanitizedVessel,
      lat: clampLatitude(sanitizedVessel.lat + safeDriftLat),
      lng: clampLongitude(sanitizedVessel.lng + safeDriftLng),
      speed: speed,
      heading: heading
    };
  }
  
  let newLat = sanitizedVessel.lat + latMovement;
  let newLng = sanitizedVessel.lng + lngMovement;
  
  // Clamp coordinates to valid ranges
  newLat = clampLatitude(newLat);
  newLng = clampLongitude(newLng);
  
  // Final validation of new coordinates
  if (!isValidLatLng(newLat, newLng)) {
    console.warn(`Generated invalid coordinates for moving vessel ${vessel.id || vessel.name}, using clamped values`);
    newLat = clampLatitude(sanitizedVessel.lat);
    newLng = clampLongitude(sanitizedVessel.lng);
  }
  
  // Generate new speed and heading with variation
  const newSpeed = Math.max(0, Math.min(50, speedKnots + (Math.random() - 0.5) * 1.0));
  const headingVariation = (Math.random() - 0.5) * 10;
  const newHeading = ((heading + headingVariation) % 360 + 360) % 360;
  
  return {
    ...sanitizedVessel,
    lat: newLat,
    lng: newLng,
    speed: newSpeed,
    heading: newHeading
  };
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
  
  // Safety layer visibility state
  const [layerVisibility, setLayerVisibility] = useState({
    stormZones: true,
    highRiskWaters: true,
    restrictedZones: true,
    accidentLocations: true
  });
  
  // Refs for cleanup
  const wsRef = useRef(null);
  const intervalRef = useRef(null);
  
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

  // Initialize WebSocket connection and real-time updates
  useEffect(() => {
    let mounted = true;
    
    try {
      // Create mock WebSocket connection
      const ws = new MockWebSocket('ws://localhost:8080/vessel-tracking');
      wsRef.current = ws;
      
      ws.onopen = () => {
        if (!mounted) return;
        
        console.log('Mock WebSocket connected for vessel tracking');
        setIsConnected(true);
        setIsLoading(false);
        
        // Start real-time updates every 2.5 seconds
        intervalRef.current = setInterval(() => {
          if (!mounted) return;
          
          try {
            setLiveVessels(currentVessels => {
              // Defensive check for current vessels
              if (!Array.isArray(currentVessels) || currentVessels.length === 0) {
                console.warn('No valid vessels for movement update, using initial mock data');
                return initialMockVessels;
              }
              
              const updatedVessels = currentVessels.map(vessel => {
                try {
                  return generateVesselMovement(vessel);
                } catch (error) {
                  console.error(`Error updating vessel ${vessel.id || vessel.name}:`, error);
                  return vessel; // Return unchanged vessel on error
                }
              });
              
              // Simulate WebSocket message
              const updateMessage = {
                type: 'vessel_update',
                timestamp: new Date().toISOString(),
                vessels: updatedVessels
              };
              
              // Trigger onmessage handler
              if (ws.onmessage) {
                try {
                  ws.onmessage({
                    data: JSON.stringify(updateMessage)
                  });
                } catch (error) {
                  console.error('Error in WebSocket message handler:', error);
                }
              }
              
              setLastUpdate(new Date());
              return updatedVessels;
            });
          } catch (error) {
            console.error('Error in vessel update interval:', error);
            setMapError(`Update error: ${error.message}`);
          }
        }, 2500); // Update every 2.5 seconds
      };
      
      ws.onmessage = (event) => {
        if (!mounted) return;
        
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'vessel_update') {
            console.log('Received vessel update:', data.vessels?.length || 0, 'vessels');
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onclose = () => {
        if (!mounted) return;
        console.log('Mock WebSocket disconnected');
        setIsConnected(false);
      };
      
      ws.onerror = (error) => {
        if (!mounted) return;
        console.error('Mock WebSocket error:', error);
        setIsConnected(false);
        setMapError('WebSocket connection error');
      };
    } catch (error) {
      console.error('Error initializing WebSocket:', error);
      setMapError(`Initialization error: ${error.message}`);
      setIsLoading(false);
    }
    
    // Cleanup function
    return () => {
      mounted = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch (error) {
          console.error('Error closing WebSocket:', error);
        }
      }
    };
  }, []);

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

  // Filter vessels to only include those with valid coordinates
  const validVessels = useMemo(() => {
    try {
      if (!Array.isArray(liveVessels)) {
        console.warn('liveVessels is not an array, using empty array');
        return [];
      }
      
      return liveVessels.filter(vessel => {
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
  }, [liveVessels]);

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
            {isConnected ? 'Live Tracking' : 'Disconnected'}
          </span>
        </div>
        <div className="text-xs text-gray-600 mt-1">
          Last update: {lastUpdate.toLocaleTimeString()}
        </div>
        {validVessels.length !== liveVessels.length && (
          <div className="text-xs text-orange-600 mt-1">
            {liveVessels.length - validVessels.length} vessel(s) with invalid coordinates
          </div>
        )}
      </div>

      {/* Safety Layers Control Panel */}
      {showSafetyLayers && (
        <div className="absolute top-4 left-4 z-[1000] bg-white/95 backdrop-blur-sm p-4 rounded-lg shadow-lg max-w-xs">
          <div className="text-sm font-semibold text-gray-800 mb-3">
            Safety Layers
          </div>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility.stormZones}
                onChange={() => toggleLayer('stormZones')}
                className="rounded"
              />
              <div className="w-3 h-3 bg-red-500 rounded border border-white"></div>
              <span className="text-gray-700">Storm Zones</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility.highRiskWaters}
                onChange={() => toggleLayer('highRiskWaters')}
                className="rounded"
              />
              <div className="w-3 h-3 bg-orange-500 rounded-full border border-white"></div>
              <span className="text-gray-700">High Risk Waters</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility.restrictedZones}
                onChange={() => toggleLayer('restrictedZones')}
                className="rounded"
              />
              <div className="w-3 h-3 bg-purple-500 rounded border border-white"></div>
              <span className="text-gray-700">Restricted Zones</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility.accidentLocations}
                onChange={() => toggleLayer('accidentLocations')}
                className="rounded"
              />
              <div className="w-3 h-3 bg-red-600 rounded-full border border-white animate-pulse"></div>
              <span className="text-gray-700">Accident Locations</span>
            </label>
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
          <SafetyLayers layerVisibility={layerVisibility} />
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