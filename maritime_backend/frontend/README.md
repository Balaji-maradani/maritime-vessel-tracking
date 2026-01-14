# Maritime Analytics Frontend

A React-based frontend for the maritime analytics platform with interactive maps and safety overlays.

## Features

- **Interactive Maritime Map**: Real-time vessel tracking with Leaflet
- **Safety Overlays**: Storm zones, piracy risk areas, and accident locations
- **Port Congestion Dashboard**: Monitor port traffic and congestion levels
- **Responsive Design**: Built with Tailwind CSS

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

The app will run on `http://localhost:3000` and proxy API requests to the Django backend on `http://localhost:8000`.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Navbar.js              # Navigation bar
│   │   └── SafetyLayersPanel.js   # Safety layers control panel
│   ├── pages/
│   │   ├── Dashboard.js           # Main dashboard
│   │   ├── MaritimeMap.js         # Interactive map with safety overlays
│   │   └── PortCongestionDashboard.js # Port congestion monitoring
│   ├── data/
│   │   └── mockData.js            # Mock data for development
│   ├── App.js                     # Main app component
│   └── index.js                   # Entry point
├── public/
└── package.json
```

## Safety Overlays

The maritime map includes three types of safety overlays:

1. **Storm Zones** (Orange polygons)
   - Active storm and severe weather areas
   - Shows severity level and wind speed

2. **Piracy Risk Zones** (Red dashed polygons)
   - High-risk piracy areas
   - Shows risk level and last incident date

3. **Accident Locations** (Red markers)
   - Recent maritime accidents
   - Shows accident type, date, and vessel information

## API Integration

The frontend is configured to work with the Django backend API:

- Vessel data: `GET /api/live-vessels/`
- Port congestion: `GET /api/ports/congestion/`
- Authentication: JWT tokens via `/api/token/`

## Development

- Uses React 18 with functional components and hooks
- Leaflet for interactive maps via react-leaflet
- Tailwind CSS for styling
- Axios for API requests
- React Router for navigation

## Mock Data

When the backend API is not available, the app falls back to mock data defined in `src/data/mockData.js`. This includes sample vessel positions and safety zone information for development and testing.