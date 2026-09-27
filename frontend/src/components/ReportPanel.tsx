import React from 'react';
import type { ReportResponse } from '../types/reports';

interface ReportPanelProps {
  report: ReportResponse;
  onReset: () => void;
}

export const ReportPanel: React.FC<ReportPanelProps> = ({ report, onReset }) => {
  return (
    <div className="results">
      <h2>Official Report</h2>
      <p>Report ID: {report.report_id} | Generated: {report.generated_at}</p>
      <div className="card">
        <h3>Summary</h3>
        <p>{report.summary}</p>
      </div>
      {report.sections.map((section, i) => (
        <div key={i} className="card" style={{ marginTop: '10px' }}>
          <h3>{section.title}</h3>
          <p>{section.content}</p>
        </div>
      ))}
      <div className="card" style={{ marginTop: '10px', fontSize: '0.8rem', color: '#666' }}>
        <p><strong>Disclaimer:</strong> {report.disclaimer}</p>
      </div>
      <button className="secondary-btn" onClick={onReset}>Analyze New Document</button>
    </div>
  );
};
