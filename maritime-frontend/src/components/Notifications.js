import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useAuth } from "../context/AuthContext";

// API base URL from environment variable
const API_BASE_URL = process.env.REACT_APP_API_BASE || 'https://maritime-backend-q150.onrender.com';

/**
 * Enhanced Real-time Notifications panel
 *
 * Fetches alerts from backend and highlights critical safety events.
 * Features:
 * - Real-time auto-refresh
 * - Acknowledge notifications
 * - Visual severity indicators
 * - Sound alerts for critical notifications
 * 
 * Expected alert shape (example):
 * {
 *   id,
 *   title,
 *   message,
 *   severity: "CRITICAL" | "HIGH" | "MEDIUM" | "INFO",
 *   category,
 *   vessel_name,
 *   port_name,
 *   created_at,
 *   acknowledged: boolean,
 *   acknowledged_at: timestamp,
 *   acknowledged_by: user_id
 * }
 */
export default function Notifications({ limit = 10, autoRefresh = true, refreshInterval = 30000 }) {
  const { token, user } = useAuth();

  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [acknowledging, setAcknowledging] = useState(new Set());
  
  // Refs for cleanup and sound
  const intervalRef = useRef(null);
  const audioRef = useRef(null);

  // Mock data fallback for development (memoized to prevent re-renders)
  const mockAlerts = useMemo(() => [
    {
      id: 1,
      title: "Storm Entry Alert",
      message: "Vessel entering severe weather zone with 120 km/h winds",
      severity: "CRITICAL",
      category: "weather",
      vessel_name: "MV Cargo Express",
      port_name: null,
      created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
      acknowledged: false,
      acknowledged_at: null,
      acknowledged_by: null
    },
    {
      id: 2,
      title: "Piracy Risk Warning",
      message: "High piracy risk area detected in Gulf of Aden",
      severity: "HIGH",
      category: "security",
      vessel_name: "MS Pacific Wave",
      port_name: null,
      created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutes ago
      acknowledged: true,
      acknowledged_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
      acknowledged_by: user?.id || 1
    },
    {
      id: 3,
      title: "Port Congestion Alert",
      message: "Destination port experiencing 4+ hour delays",
      severity: "MEDIUM",
      category: "port",
      vessel_name: "LNG Explorer",
      port_name: "Singapore",
      created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
      acknowledged: false,
      acknowledged_at: null,
      acknowledged_by: null
    },
    {
      id: 4,
      title: "Route Deviation",
      message: "Minor course correction detected due to traffic",
      severity: "INFO",
      category: "navigation",
      vessel_name: "MV Atlantic Star",
      port_name: null,
      created_at: new Date(Date.now() - 45 * 60 * 1000).toISOString(), // 45 minutes ago
      acknowledged: true,
      acknowledged_at: new Date(Date.now() - 40 * 60 * 1000).toISOString(),
      acknowledged_by: user?.id || 1
    },
    {
      id: 5,
      title: "Collision Risk",
      message: "Two vessels on collision course - immediate action required",
      severity: "CRITICAL",
      category: "safety",
      vessel_name: "MV Ocean Breeze",
      port_name: null,
      created_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(), // 2 minutes ago
      acknowledged: false,
      acknowledged_at: null,
      acknowledged_by: null
    }
  ], [user?.id]);

  // Play alert sound for critical notifications
  const playAlertSound = useCallback(() => {
    try {
      // Create audio context for alert sound (simple beep)
      if (!audioRef.current) {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        
        oscillator.start();
        oscillator.stop(audioContext.currentTime + 0.2);
        
        audioRef.current = audioContext;
      }
    } catch (error) {
      console.warn('Could not play alert sound:', error);
    }
  }, []);

  // Fetch alerts from backend
  const fetchAlerts = useCallback(async () => {
    if (!autoRefresh && alerts.length > 0) return; // Skip if not auto-refreshing and we have data
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/notifications/`, {
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      const list = Array.isArray(data) ? data : data.results || data.notifications || [];

      // Sort by created_at descending and severity priority
      const sortedAlerts = list.sort((a, b) => {
        // First sort by severity (Critical > High > Medium > Info)
        const severityOrder = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'INFO': 1 };
        const severityDiff = (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0);
        if (severityDiff !== 0) return severityDiff;
        
        // Then by created_at descending
        const da = a.created_at ? new Date(a.created_at).getTime() : 0;
        const db = b.created_at ? new Date(b.created_at).getTime() : 0;
        return db - da;
      });

      // Check for new critical alerts for sound notification
      if (alerts.length > 0) {
        const newCriticalAlerts = sortedAlerts.filter(alert => 
          alert.severity === 'CRITICAL' && 
          !alert.acknowledged &&
          !alerts.some(existing => existing.id === alert.id)
        );
        
        if (newCriticalAlerts.length > 0) {
          playAlertSound();
        }
      }

      setAlerts(sortedAlerts);
      setLastUpdate(new Date());
      setError("");
      
      console.log(`Fetched ${sortedAlerts.length} notifications from API`);
      
    } catch (err) {
      console.warn("Failed to fetch notifications, using mock data:", err.message);
      setError("");
      // Fallback to mock data if API fails
      if (alerts.length === 0) {
        setAlerts(mockAlerts);
        setLastUpdate(new Date());
      }
    }
  }, [token, alerts, autoRefresh, playAlertSound, mockAlerts]);

  // Acknowledge notification
  const acknowledgeAlert = useCallback(async (alertId) => {
    if (acknowledging.has(alertId)) return; // Prevent double-clicking
    
    setAcknowledging(prev => new Set([...prev, alertId]));
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/notifications/${alertId}/acknowledge/`, {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      // Update local state immediately for better UX
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId 
          ? { 
              ...alert, 
              acknowledged: true, 
              acknowledged_at: new Date().toISOString(),
              acknowledged_by: user?.id || 1
            }
          : alert
      ));
      
      console.log(`Acknowledged notification ${alertId}`);
      
    } catch (err) {
      console.error("Failed to acknowledge notification:", err.message);
      // For mock data, still update locally
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId 
          ? { 
              ...alert, 
              acknowledged: true, 
              acknowledged_at: new Date().toISOString(),
              acknowledged_by: user?.id || 1
            }
          : alert
      ));
    } finally {
      setAcknowledging(prev => {
        const newSet = new Set(prev);
        newSet.delete(alertId);
        return newSet;
      });
    }
  }, [token, user?.id, acknowledging]);

  // Initial fetch and setup auto-refresh
  useEffect(() => {
    let mounted = true;
    
    const initializeAlerts = async () => {
      setLoading(true);
      
      try {
        await fetchAlerts();
        
        if (!mounted) return;
        
        setLoading(false);
        
        // Set up auto-refresh if enabled
        if (autoRefresh && refreshInterval > 0) {
          intervalRef.current = setInterval(async () => {
            if (!mounted) return;
            
            try {
              await fetchAlerts();
            } catch (error) {
              console.error('Error in periodic alerts update:', error);
            }
          }, refreshInterval);
        }
        
      } catch (error) {
        console.error('Error initializing alerts:', error);
        setError(`Initialization error: ${error.message}`);
        setLoading(false);
      }
    };
    
    initializeAlerts();
    
    // Cleanup function
    return () => {
      mounted = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (audioRef.current) {
        audioRef.current.close();
      }
    };
  }, [fetchAlerts, autoRefresh, refreshInterval]);

  // Get visible alerts (limited by prop)
  const visibleAlerts = alerts.slice(0, limit);
  const unacknowledgedCount = alerts.filter(alert => !alert.acknowledged).length;
  const criticalCount = alerts.filter(alert => alert.severity === 'CRITICAL' && !alert.acknowledged).length;

  // Get severity configuration
  const getSeverityConfig = (severityRaw) => {
    const s = (severityRaw || "").toString().toUpperCase();
    switch (s) {
      case "CRITICAL":
        return {
          label: "Critical",
          badgeClass: "bg-red-600 text-white animate-pulse",
          borderClass: "border-red-500",
          bgClass: "bg-red-900/30",
          icon: "🚨"
        };
      case "HIGH":
        return {
          label: "High",
          badgeClass: "bg-orange-600 text-white",
          borderClass: "border-orange-500",
          bgClass: "bg-orange-900/30",
          icon: "⚠️"
        };
      case "MEDIUM":
        return {
          label: "Medium",
          badgeClass: "bg-yellow-600 text-black",
          borderClass: "border-yellow-500",
          bgClass: "bg-yellow-900/30",
          icon: "⚡"
        };
      case "INFO":
      default:
        return {
          label: "Info",
          badgeClass: "bg-blue-600 text-white",
          borderClass: "border-blue-500",
          bgClass: "bg-blue-900/30",
          icon: "ℹ️"
        };
    }
  };

  // Format time ago
  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Unknown';
    
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-600">
        <div className="flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-3"></div>
          <span className="text-gray-300">Loading alerts...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-600">
        <div className="text-center">
          <div className="text-red-400 text-lg font-semibold mb-2">⚠️ Alert System Error</div>
          <p className="text-sm text-red-300 mb-4">{error}</p>
          <button
            onClick={() => {
              setError("");
              setLoading(true);
              fetchAlerts();
            }}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (visibleAlerts.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-600">
        <div className="text-center">
          <div className="text-green-400 text-lg font-semibold mb-2">✅ All Clear</div>
          <p className="text-sm text-gray-400">No active alerts at this time.</p>
          <div className="text-xs text-gray-500 mt-2">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-600">
      {/* Header */}
      <div className="p-4 border-b border-gray-600">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-bold text-blue-400">Real-time Alerts</h3>
            {criticalCount > 0 && (
              <div className="bg-red-600 text-white px-2 py-1 rounded-full text-xs font-bold animate-pulse">
                {criticalCount} Critical
              </div>
            )}
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400">
              {unacknowledgedCount} unacknowledged
            </div>
            <div className="text-xs text-gray-500">
              Updated: {lastUpdate.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="max-h-96 overflow-y-auto">
        <div className="p-4 space-y-3">
          {visibleAlerts.map((alert) => {
            const { label, badgeClass, borderClass, bgClass, icon } = getSeverityConfig(alert.severity);
            const isAcknowledging = acknowledging.has(alert.id);

            return (
              <div
                key={alert.id}
                className={`relative border-l-4 pl-4 pr-3 py-3 rounded-r-lg transition-all duration-300 ${borderClass} ${bgClass} ${
                  alert.acknowledged ? 'opacity-60' : ''
                }`}
              >
                {/* Severity Badge and Status */}
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{icon}</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${badgeClass}`}>
                      {label}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {alert.acknowledged ? (
                      <div className="flex items-center gap-1 text-xs text-green-400">
                        <span>✓</span>
                        <span>Acknowledged</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => acknowledgeAlert(alert.id)}
                        disabled={isAcknowledging}
                        className="px-2 py-1 bg-gray-600 hover:bg-gray-500 text-white text-xs rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isAcknowledging ? (
                          <div className="flex items-center gap-1">
                            <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>
                            <span>...</span>
                          </div>
                        ) : (
                          'Acknowledge'
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {/* Alert Content */}
                <div className="space-y-1">
                  <div className="font-medium text-sm text-white">
                    {alert.title || "Safety Alert"}
                  </div>
                  {alert.message && (
                    <div className="text-sm text-gray-300">
                      {alert.message}
                    </div>
                  )}
                  
                  {/* Metadata */}
                  <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-gray-400">
                    {alert.vessel_name && (
                      <span className="flex items-center gap-1">
                        <span>🚢</span>
                        <span>{alert.vessel_name}</span>
                      </span>
                    )}
                    {alert.port_name && (
                      <span className="flex items-center gap-1">
                        <span>🏭</span>
                        <span>{alert.port_name}</span>
                      </span>
                    )}
                    {alert.category && (
                      <span className="flex items-center gap-1">
                        <span>📂</span>
                        <span className="capitalize">{alert.category}</span>
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <span>🕒</span>
                      <span>{formatTimeAgo(alert.created_at)}</span>
                    </span>
                  </div>

                  {/* Acknowledgment Info */}
                  {alert.acknowledged && alert.acknowledged_at && (
                    <div className="text-xs text-gray-500 mt-1 pt-1 border-t border-gray-600">
                      Acknowledged {formatTimeAgo(alert.acknowledged_at)}
                      {alert.acknowledged_by && ` by user ${alert.acknowledged_by}`}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      {alerts.length > limit && (
        <div className="p-3 border-t border-gray-600 text-center">
          <div className="text-xs text-gray-400">
            Showing {limit} of {alerts.length} alerts
          </div>
        </div>
      )}
    </div>
  );
}


