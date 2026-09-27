import React from 'react';
import type { VersionAlert } from '../types/analysis';

interface VersionAlertsPanelProps {
  alerts: VersionAlert[];
}

export const VersionAlertsPanel: React.FC<VersionAlertsPanelProps> = ({ alerts }) => {
  if (alerts.length === 0) return null;
  return (
    <div className="card">
      <h3>Version Alerts</h3>
      <ul>
        {alerts.map((alert, i) => (
          <li key={i}>
            <strong>{alert.standard_id}:</strong> {alert.message} ({alert.status})
          </li>
        ))}
      </ul>
    </div>
  );
};
