import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, LayersControl } from 'react-leaflet';
import L from 'leaflet';
import SafetyLayersPanel from '../components/SafetyLayersPanel';
import { mockVesselData, mockSafetyData } from '../data/mockData';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons for different safety zones
const stormIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBmaWxsPSIjRkY2QjAwIi8+Cjwvc3ZnPgo=',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

const piracyIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyUzYuNDggMjIgMTIgMjJTMjIgMTcuNTIgMjIgMTJTMTcuNTIgMiAxMiAyWk0xMiAyMEM3LjU5IDIwIDQgMTYuNDEgNCA1MlM3LjU5IDQgMTIgNFMxNiA3LjU5IDE2IDEyUzE2LjQxIDIwIDEyIDIwWiIgZmlsbD0iI0RDMjYyNiIvPgo8L3N2Zz4K',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

const accidentIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEgMjFIMjNMMTIgMkwxIDIxWk0xMyAxOEgxMVYxNkgxM1YxOFpNMTMgMTRIMTFWMTBIMTNWMTRaIiBmaWxsPSIjRUY0NDQ0Ii8+Cjwvc3ZnPgo=',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

const MaritimeMap = () => {
  const [vessels, setVessels] = useState([]);
  const [safetyLayers, setSafetyLayers] = useState({
    stormZones: true,
    piracyZones: true,
    accidents: true,
  });

  useEffect(() => {
    // Simulate fetching vessel data
    setVessels(mockVesselData);
  }, []);

  const toggleSafetyLayer = (layerName) => {
    setSafetyLayers(prev => ({
      ...prev,
      [layerName]: !prev[layerName]
    }));
  };

  return (
    <div className="h-screen flex">
      {/* Safety Layers Panel */}
      <SafetyLayersPanel 
        layers={safetyLayers}
        onToggleLayer={toggleSafetyLayer}
      />
      
      {/* Map Container */}
      <div className="flex-1">
        <MapContainer
          center={[25.0, 55.0]} // Dubai coordinates as center
          zoom={6}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {/* Vessel Markers */}
          {vessels.map((vessel) => (
            <Marker
              key={vessel.imo}
              position={[vessel.latitude, vessel.longitude]}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold text-lg">{vessel.name}</h3>
                  <p><strong>IMO:</strong> {vessel.imo}</p>
                  <p><strong>Type:</strong> {vessel.vessel_type}</p>
                  <p><strong>Speed:</strong> {vessel.speed} knots</p>
                  <p><strong>Heading:</strong> {vessel.heading}°</p>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Storm Zones */}
          {safetyLayers.stormZones && mockSafetyData.stormZones.map((zone, index) => (
            <Polygon
              key={`storm-${index}`}
              positions={zone.coordinates}
              pathOptions={{
                color: '#FF6B00',
                fillColor: '#FF6B00',
                fillOpacity: 0.3,
                weight: 2,
              }}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold text-orange-600">⛈️ Storm Zone</h3>
                  <p><strong>Severity:</strong> {zone.severity}</p>
                  <p><strong>Wind Speed:</strong> {zone.windSpeed} km/h</p>
                  <p><strong>Description:</strong> {zone.description}</p>
                </div>
              </Popup>
            </Polygon>
          ))}

          {/* Piracy Zones */}
          {safetyLayers.piracyZones && mockSafetyData.piracyZones.map((zone, index) => (
            <Polygon
              key={`piracy-${index}`}
              positions={zone.coordinates}
              pathOptions={{
                color: '#DC2626',
                fillColor: '#DC2626',
                fillOpacity: 0.2,
                weight: 2,
                dashArray: '5, 5',
              }}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold text-red-600">🏴‍☠️ Piracy Risk Zone</h3>
                  <p><strong>Risk Level:</strong> {zone.riskLevel}</p>
                  <p><strong>Last Incident:</strong> {zone.lastIncident}</p>
                  <p><strong>Description:</strong> {zone.description}</p>
                </div>
              </Popup>
            </Polygon>
          ))}

          {/* Accident Locations */}
          {safetyLayers.accidents && mockSafetyData.accidents.map((accident, index) => (
            <Marker
              key={`accident-${index}`}
              position={[accident.latitude, accident.longitude]}
              icon={accidentIcon}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold text-red-600">⚠️ Accident Location</h3>
                  <p><strong>Type:</strong> {accident.type}</p>
                  <p><strong>Date:</strong> {accident.date}</p>
                  <p><strong>Vessel:</strong> {accident.vesselName}</p>
                  <p><strong>Description:</strong> {accident.description}</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};

export default MaritimeMap;