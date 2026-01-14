import React from 'react';
import { useAuth } from '../context/AuthContext';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

export default function Analytics() {
  const { user } = useAuth();

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  // Get user role for analytics customization
  const userRole = user.role?.toUpperCase() || "OPERATOR";

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">
              Maritime Analytics
            </h1>
            <p className="text-gray-400">
              Comprehensive analytics and insights for {user.username} ({userRole})
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400">Analytics Dashboard</div>
            <div className="text-lg font-mono">{new Date().toLocaleDateString()}</div>
          </div>
        </div>
      </div>

      {/* Analytics Content */}
      <div className="p-6">
        <AnalyticsDashboard userRole={userRole} />
      </div>
    </div>
  );
}