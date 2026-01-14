#!/bin/bash

# Maritime Frontend Demo Startup Script
echo "🚢 Maritime Frontend Demo Startup"
echo "=================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm and try again."
    exit 1
fi

echo "✅ npm version: $(npm -v)"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ Dependencies already installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "✅ .env file exists"
fi

# Display demo information
echo ""
echo "🎬 DEMO INFORMATION"
echo "==================="
echo "Demo URL: http://localhost:3000"
echo ""
echo "Demo Accounts:"
echo "OPERATOR - Username: operator_demo, Password: demo123"
echo "ANALYST  - Username: analyst_demo,  Password: demo123"
echo "ADMIN    - Username: admin_demo,    Password: demo123"
echo ""
echo "Features to Demo:"
echo "• Real-time vessel tracking with interactive map"
echo "• Safety overlays (storms, piracy, accidents)"
echo "• Role-based dashboards and analytics"
echo "• Advanced charts and visualizations"
echo "• Real-time notifications and alerts"
echo "• Mobile responsive design"
echo ""

# Start the development server
echo "🚀 Starting development server..."
echo "Press Ctrl+C to stop the server"
echo ""

npm start