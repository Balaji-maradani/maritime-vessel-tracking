@echo off
echo 🚢 Maritime Frontend Demo Startup
echo ==================================

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ and try again.
    pause
    exit /b 1
)

echo ✅ Node.js version:
node --version

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not installed. Please install npm and try again.
    pause
    exit /b 1
)

echo ✅ npm version:
npm --version

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ Dependencies already installed
)

REM Check if .env file exists
if not exist ".env" (
    echo 📝 Creating .env file from .env.example...
    copy .env.example .env >nul
    echo ✅ .env file created
) else (
    echo ✅ .env file exists
)

REM Display demo information
echo.
echo 🎬 DEMO INFORMATION
echo ===================
echo Demo URL: http://localhost:3000
echo.
echo Demo Accounts:
echo OPERATOR - Username: operator_demo, Password: demo123
echo ANALYST  - Username: analyst_demo,  Password: demo123
echo ADMIN    - Username: admin_demo,    Password: demo123
echo.
echo Features to Demo:
echo • Real-time vessel tracking with interactive map
echo • Safety overlays (storms, piracy, accidents)
echo • Role-based dashboards and analytics
echo • Advanced charts and visualizations
echo • Real-time notifications and alerts
echo • Mobile responsive design
echo.

REM Start the development server
echo 🚀 Starting development server...
echo Press Ctrl+C to stop the server
echo.

npm start