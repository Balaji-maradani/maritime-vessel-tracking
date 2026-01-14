# Maritime Vessel Tracking Frontend

A comprehensive React-based maritime vessel tracking and analytics platform with real-time monitoring, safety overlays, and role-based dashboards.

## 🚢 Features

### Core Functionality
- **Real-time Vessel Tracking**: Live vessel positions with interactive map
- **Safety Overlays**: Storm zones, piracy areas, restricted waters, accident locations
- **Role-based Dashboards**: Customized views for Operators, Analysts, and Admins
- **Advanced Analytics**: KPIs, trends, charts, and predictive insights
- **Real-time Alerts**: Critical notifications with acknowledgment system
- **Port Congestion Monitoring**: Port performance and congestion analytics

### User Roles
- **OPERATOR**: Live vessel tracking, operational alerts, basic analytics
- **ANALYST**: Advanced analytics, route optimization, performance insights
- **ADMIN**: System administration, user management, audit logs

### Technical Features
- **Interactive Maps**: React Leaflet with safety overlays and vessel markers
- **Real-time Updates**: WebSocket-style updates every 30 seconds
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Chart Visualizations**: Interactive charts using Chart.js
- **Authentication**: JWT-based authentication with role management
- **API Integration**: RESTful API integration with fallback to mock data

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd maritime-frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your backend API URL:
   ```
   REACT_APP_API_BASE=https://your-backend-api.com
   ```

4. **Start development server**
   ```bash
   npm start
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🌐 Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Backend API Base URL (required)
REACT_APP_API_BASE=https://maritime-backend-q150.onrender.com

# Optional: Enable development features
REACT_APP_ENV=production

# Optional: Analytics tracking
REACT_APP_ANALYTICS_ID=your-analytics-id
```

### Environment Variable Details

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REACT_APP_API_BASE` | Backend API base URL | `https://maritime-backend-q150.onrender.com` | Yes |
| `REACT_APP_ENV` | Environment mode | `production` | No |
| `REACT_APP_ANALYTICS_ID` | Analytics tracking ID | - | No |

## 📱 Demo Instructions

### Demo Accounts
Use these accounts to explore different role capabilities:

```
OPERATOR Account:
Username: operator_demo
Password: demo123
Role: OPERATOR

ANALYST Account:
Username: analyst_demo  
Password: demo123
Role: ANALYST

ADMIN Account:
Username: admin_demo
Password: demo123
Role: ADMIN
```

### Demo Flow

1. **Login** with any demo account at `/login`
2. **Dashboard** - Role-specific dashboard with live data
3. **Vessels** - Interactive vessel tracking with FlightRadar24-style interface
4. **Analytics** - Comprehensive analytics with charts and KPIs
5. **Ports** - Port congestion monitoring and performance metrics

### Key Demo Features

#### For OPERATORS:
- Live vessel tracking on interactive map
- Real-time safety alerts and notifications
- Quick analytics widgets
- Safety overlay controls (storms, piracy, accidents)

#### For ANALYSTS:
- Advanced analytics dashboard with charts
- Route performance analysis
- Predictive insights and trends
- Port performance metrics
- Export capabilities

#### For ADMINS:
- System administration panel
- User management interface
- Audit logs and security events
- System performance monitoring

## 🏗️ Build & Deployment

### Production Build

```bash
# Create optimized production build
npm run build

# Serve locally for testing
npx serve -s build
```

### Deployment to Render

1. **Connect Repository**: Link your GitHub repository to Render
2. **Configure Build Settings**:
   - Build Command: `npm run build`
   - Publish Directory: `build`
   - Node Version: `16+`

3. **Environment Variables**: Set in Render dashboard:
   ```
   REACT_APP_API_BASE=https://your-backend-api.com
   ```

4. **Deploy**: Render will automatically build and deploy

### Build Optimization

The production build includes:
- Code splitting and lazy loading
- Asset optimization and compression
- Tree shaking for smaller bundle size
- Service worker for caching (optional)

## 🛠️ Development

### Project Structure

```
src/
├── components/          # Reusable components
│   ├── AnalyticsDashboard.js   # Analytics charts and KPIs
│   ├── Notifications.js       # Real-time alerts system
│   ├── VesselMap.js           # Interactive map with overlays
│   └── Navbar.js              # Navigation component
├── pages/              # Page components
│   ├── Dashboard.js           # Role-based main dashboard
│   ├── Analytics.js           # Dedicated analytics page
│   ├── Vessels.js             # Vessel tracking page
│   ├── Login.js               # Authentication
│   └── Register.js            # User registration
├── context/            # React context providers
│   └── AuthContext.js         # Authentication state
└── App.js              # Main application component
```

### Available Scripts

```bash
# Development
npm start              # Start development server
npm test               # Run test suite
npm run build          # Create production build

# Code Quality
npm run lint           # Run ESLint
npm run format         # Format code with Prettier

# Deployment
npm run deploy         # Deploy to production
```

### API Integration

The frontend integrates with the following backend endpoints:

```
Authentication:
POST /api/token/              # Login
POST /api/register/           # Registration
GET  /api/me/                 # User profile

Vessel Data:
GET  /api/vessels/            # Live vessel data
GET  /api/vessels/{id}/       # Vessel details

Analytics:
GET  /api/analytics/kpis/     # Key performance indicators
GET  /api/analytics/trends/   # Historical trends
GET  /api/analytics/routes/   # Route analysis

Safety Data:
GET  /api/safety/storms/      # Weather systems
GET  /api/safety/piracy-zones/ # Security threats
GET  /api/safety/accidents/   # Incident reports

Notifications:
GET  /api/notifications/      # User alerts
POST /api/notifications/{id}/acknowledge/ # Acknowledge alert

Port Data:
GET  /api/ports/congestion/   # Port performance
```

## 🔧 Configuration

### Map Configuration
- **Center**: Indian Ocean (-10.0, 75.0)
- **Zoom Levels**: 3-18
- **Tile Provider**: OpenStreetMap
- **Update Interval**: 30 seconds for vessels, 5 minutes for safety data

### Chart Configuration
- **Library**: Chart.js with react-chartjs-2
- **Theme**: Dark mode with maritime colors
- **Responsive**: Adapts to screen size
- **Animations**: Smooth transitions and hover effects

### Performance Settings
- **Bundle Size**: ~228KB gzipped
- **Load Time**: <3 seconds on 3G
- **Memory Usage**: <50MB typical
- **Update Frequency**: Configurable per data type

## 🐛 Troubleshooting

### Common Issues

**Build Fails**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

**API Connection Issues**
- Verify `REACT_APP_API_BASE` in `.env`
- Check backend API is running
- Verify CORS settings on backend

**Map Not Loading**
- Check internet connection
- Verify Leaflet CSS is loaded
- Check browser console for errors

**Charts Not Displaying**
- Verify Chart.js dependencies
- Check data format matches expected schema
- Ensure container has defined height

### Performance Optimization

```bash
# Analyze bundle size
npm run build
npx webpack-bundle-analyzer build/static/js/*.js

# Check for unused dependencies
npx depcheck

# Optimize images
npx imagemin-cli src/assets/* --out-dir=src/assets/optimized
```

## 📊 Monitoring

### Performance Metrics
- **First Contentful Paint**: <1.5s
- **Largest Contentful Paint**: <2.5s
- **Time to Interactive**: <3.5s
- **Cumulative Layout Shift**: <0.1

### Error Tracking
- Console errors logged and reported
- API failures gracefully handled with fallbacks
- User actions tracked for analytics

## 🔒 Security

### Authentication
- JWT tokens with expiration
- Role-based access control
- Secure token storage
- Automatic logout on token expiry

### Data Protection
- HTTPS enforcement
- XSS protection
- CSRF protection
- Input validation and sanitization

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Maritime Vessel Tracking Frontend** - Built with React, Leaflet, and Chart.js for comprehensive maritime operations management.
