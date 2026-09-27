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
    { label: 'Compliance', value: `${analysis.compliance.length} issues` },
  ];
  return (
    <div className="grid-4">
      {stats.map((stat, i) => (
        <div className="card" key={i} style={{ padding: '1rem', border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>{stat.label}</div>
          <div style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--color-primary)' }}>{stat.value}</div>
        </div>
      ))}
    </div>
  );
};
