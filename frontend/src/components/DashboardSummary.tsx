import React from 'react';
import type { AnalysisResponse } from '../types/analysis';

interface DashboardSummaryProps {
  analysis: AnalysisResponse;
}

export const DashboardSummary: React.FC<DashboardSummaryProps> = ({ analysis }) => {
  const stats = [
    { label: 'Document', value: analysis.document.filename },
    { label: 'Requirements', value: analysis.requirements.technical_requirements.length },
    { label: 'Recommendations', value: analysis.recommendations.length },
    { label: 'Compliance Issues', value: analysis.compliance.length },
  ];
  return (
    <div className="grid-4" style={{ marginBottom: '20px' }}>
      {stats.map((stat, i) => (
        <div className="card" key={i} style={{ padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', marginBottom: '0.5rem', fontWeight: 600 }}>{stat.label}</div>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--color-primary)' }}>{stat.value}</div>
        </div>
      ))}
    </div>
  );
};
