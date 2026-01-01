import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

// API base URL from environment variable
const API_BASE_URL = process.env.REACT_APP_API_BASE || 'https://maritime-backend-q150.onrender.com';

/**
 * Notifications panel
 *
 * Fetches alerts from backend and highlights critical safety events.
 * Expected alert shape (example):
 * {
 *   id,
 *   title,
 *   message,
 *   severity: "CRITICAL" | "HIGH" | "MEDIUM" | "INFO",
 *   category,
 *   vessel_name,
 *   port_name,
 *   created_at
 * }
 */
export default function Notifications({ limit = 5 }) {
  const { token } = useAuth();

  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAlerts = async () => {
      setLoading(true);
      setError("");

      try {
        const res = await fetch(`${API_BASE_URL}/api/alerts/`, {
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        });

        if (!res.ok) {
          throw new Error("Failed to fetch alerts");
        }

        const data = await res.json();
        const list = Array.isArray(data) ? data : [];

        // Sort by created_at descending if present
        list.sort((a, b) => {
          const da = a.created_at ? new Date(a.created_at).getTime() : 0;
          const db = b.created_at ? new Date(b.created_at).getTime() : 0;
          return db - da;
        });

        setAlerts(list);
      } catch (err) {
        console.error("Alerts API error:", err);
        setError(err.message || "Failed to load alerts");
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, [token]);

  const visibleAlerts = alerts.slice(0, limit);

  const getSeverityConfig = (severityRaw) => {
    const s = (severityRaw || "").toString().toUpperCase();
    switch (s) {
      case "CRITICAL":
      case "HIGH":
        return {
          label: "Critical",
          badgeClass: "badge-error",
          borderClass: "border-error",
        };
      case "MEDIUM":
      case "WARN":
      case "WARNING":
        return {
          label: "Warning",
          badgeClass: "badge-warning",
          borderClass: "border-warning",
        };
      case "INFO":
      default:
        return {
          label: "Info",
          badgeClass: "badge-info",
          borderClass: "border-base-300",
        };
    }
  };

  if (loading) {
    return (
      <div className="bg-base-200 p-6 rounded-xl flex items-center justify-center">
        <span className="loading loading-spinner loading-md"></span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-base-200 p-6 rounded-xl">
        <p className="text-sm text-error">{error}</p>
      </div>
    );
  }

  if (visibleAlerts.length === 0) {
    return (
      <div className="bg-base-200 p-6 rounded-xl">
        <p className="text-sm text-white/70">No active alerts.</p>
      </div>
    );
  }

  return (
    <div className="bg-base-200 p-6 rounded-xl space-y-3 max-h-80 overflow-y-auto">
      {visibleAlerts.map((alert) => {
        const { label, badgeClass, borderClass } = getSeverityConfig(
          alert.severity
        );

        return (
          <div
            key={alert.id || `${alert.title}-${alert.created_at}`}
            className={`flex items-start gap-3 border-l-4 pl-3 py-1 ${borderClass}`}
          >
            <span className={`badge ${badgeClass} mt-1`}>{label}</span>
            <div>
              <p className="text-sm text-white">
                {alert.title || "Safety alert"}
              </p>
              {alert.message && (
                <p className="text-xs text-white/60 mt-0.5">{alert.message}</p>
              )}
              <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1 text-[11px] text-white/50">
                {alert.vessel_name && <span>Vessel: {alert.vessel_name}</span>}
                {alert.port_name && <span>Port: {alert.port_name}</span>}
                {alert.category && <span>Category: {alert.category}</span>}
                {alert.created_at && (
                  <span>
                    Time: {new Date(alert.created_at).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}


