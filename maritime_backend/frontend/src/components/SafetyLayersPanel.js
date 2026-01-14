import React from 'react';

const SafetyLayersPanel = ({ layers, onToggleLayer }) => {
  const layerConfig = [
    {
      key: 'stormZones',
      label: 'Storm Zones',
      icon: '⛈️',
      color: 'text-orange-600',
      description: 'Active storm and severe weather areas'
    },
    {
      key: 'piracyZones',
      label: 'Piracy Risk Zones',
      icon: '🏴‍☠️',
      color: 'text-red-600',
      description: 'High-risk piracy areas'
    },
    {
      key: 'accidents',
      label: 'Accident Locations',
      icon: '⚠️',
      color: 'text-red-500',
      description: 'Recent maritime accidents'
    }
  ];

  return (
    <div className="w-80 bg-white shadow-lg border-r border-gray-200 p-4 overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-800 mb-2">Safety Layers</h2>
        <p className="text-sm text-gray-600">Toggle safety overlays on the map</p>
      </div>

      <div className="space-y-4">
        {layerConfig.map((layer) => (
          <div key={layer.key} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{layer.icon}</span>
                <div>
                  <h3 className={`font-semibold ${layer.color}`}>
                    {layer.label}
                  </h3>
                  <p className="text-xs text-gray-500">{layer.description}</p>
                </div>
              </div>
              
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={layers[layer.key]}
                  onChange={() => onToggleLayer(layer.key)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
            
            {layers[layer.key] && (
              <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                Layer is currently visible on the map
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-blue-800 mb-2">Legend</h3>
        <div className="space-y-2 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-orange-500 opacity-30 border border-orange-600"></div>
            <span>Storm zones</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-600 opacity-20 border border-red-600 border-dashed"></div>
            <span>Piracy risk areas</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-500 rounded-full"></div>
            <span>Accident locations</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
            <span>Active vessels</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SafetyLayersPanel;