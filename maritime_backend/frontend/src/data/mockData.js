// Mock vessel data for testing
export const mockVesselData = [
  {
    imo: 'IMO9234567',
    name: 'Ocean Explorer',
    vessel_type: 'Container Ship',
    latitude: 25.2048,
    longitude: 55.2708,
    speed: 12.5,
    heading: 045,
    timestamp: '2024-01-07T10:30:00Z'
  },
  {
    imo: 'IMO9876543',
    name: 'Maritime Pioneer',
    vessel_type: 'Bulk Carrier',
    latitude: 26.0667,
    longitude: 50.5577,
    speed: 8.2,
    heading: 180,
    timestamp: '2024-01-07T10:25:00Z'
  },
  {
    imo: 'IMO9345678',
    name: 'Gulf Trader',
    vessel_type: 'Tanker',
    latitude: 24.4539,
    longitude: 54.3773,
    speed: 15.1,
    heading: 270,
    timestamp: '2024-01-07T10:20:00Z'
  },
  {
    imo: 'IMO9456789',
    name: 'Red Sea Navigator',
    vessel_type: 'General Cargo',
    latitude: 20.0000,
    longitude: 40.0000,
    speed: 10.8,
    heading: 090,
    timestamp: '2024-01-07T10:15:00Z'
  }
];

// Mock safety data
export const mockSafetyData = {
  stormZones: [
    {
      coordinates: [
        [23.0, 58.0],
        [23.0, 60.0],
        [25.0, 60.0],
        [25.0, 58.0]
      ],
      severity: 'High',
      windSpeed: 85,
      description: 'Tropical cyclone with strong winds and heavy rainfall'
    },
    {
      coordinates: [
        [18.0, 42.0],
        [18.0, 45.0],
        [21.0, 45.0],
        [21.0, 42.0]
      ],
      severity: 'Medium',
      windSpeed: 65,
      description: 'Severe thunderstorms with gusty winds'
    }
  ],
  
  piracyZones: [
    {
      coordinates: [
        [12.0, 43.0],
        [12.0, 51.0],
        [18.0, 51.0],
        [18.0, 43.0]
      ],
      riskLevel: 'High',
      lastIncident: '2024-01-05',
      description: 'Gulf of Aden - High piracy activity reported'
    },
    {
      coordinates: [
        [1.0, 40.0],
        [1.0, 48.0],
        [8.0, 48.0],
        [8.0, 40.0]
      ],
      riskLevel: 'Medium',
      lastIncident: '2023-12-20',
      description: 'Somali Basin - Moderate piracy risk'
    }
  ],
  
  accidents: [
    {
      latitude: 25.7617,
      longitude: 55.9657,
      type: 'Collision',
      date: '2024-01-06',
      vesselName: 'MV Atlantic Star',
      description: 'Minor collision between two cargo vessels, no injuries reported'
    },
    {
      latitude: 22.3964,
      longitude: 51.5321,
      type: 'Grounding',
      date: '2024-01-04',
      vesselName: 'Bulk Carrier Neptune',
      description: 'Vessel ran aground due to navigation error, refloated successfully'
    },
    {
      latitude: 26.2041,
      longitude: 50.0659,
      type: 'Engine Failure',
      date: '2024-01-03',
      vesselName: 'Tanker Gulf Pride',
      description: 'Engine failure resulted in temporary anchoring, repairs completed'
    },
    {
      latitude: 19.0760,
      longitude: 42.6526,
      type: 'Fire',
      date: '2024-01-02',
      vesselName: 'Container Ship Horizon',
      description: 'Small fire in engine room, quickly extinguished by crew'
    }
  ]
};