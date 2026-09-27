import React from 'react';
import type { ComplianceResult } from '../types/analysis';

interface CompliancePanelProps {
  compliance: ComplianceResult[];
}

export const CompliancePanel: React.FC<CompliancePanelProps> = ({ compliance }) => {
  return (
    <div className="card">
      <h3>Compliance Status</h3>
      <table>
        <thead>
          <tr>
            <th>Standard</th>
            <th>Requirement</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {compliance.map((c, i) => (
            <tr key={i}>
              <td>{c.standard_id}</td>
              <td>{c.requirement}</td>
              <td><span className={`badge-status ${c.status}`}>{c.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
