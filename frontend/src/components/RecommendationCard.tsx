import React from 'react';
import type { RecommendedStandard } from '../types/analysis';

interface RecommendationCardProps {
  standard: RecommendedStandard;
  isTop?: boolean;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ standard, isTop }) => {
  return (
    <div className="card" style={{
      borderLeft: isTop ? '6px solid var(--color-primary)' : '1px solid var(--color-border)',
      padding: '1.5rem',
      borderRadius: 'var(--radius-md)',
      marginBottom: '1rem'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
        <span style={{ fontWeight: '800', fontSize: '1.1rem', color: 'var(--color-primary)' }}>{standard.standard_number}</span>
        <span style={{
          background: '#eff6ff',
          color: 'var(--color-primary)',
          padding: '0.25rem 0.75rem',
          borderRadius: '999px',
          fontSize: '0.75rem',
          fontWeight: '600'
        }}>{standard.relevance}% Match</span>
      </div>

      <h4 style={{ margin: '0.5rem 0', fontSize: '1.1rem' }}>{standard.title}</h4>
      <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>{standard.reason}</p>

      <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--color-border)', fontSize: '0.85rem' }}>
        <strong style={{ color: 'var(--color-text)' }}>Evidence: </strong>
        <a href={standard.evidence[0]?.source_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-accent)' }}>
          {standard.evidence[0]?.source_name || 'View Source'}
        </a>
      </div>
    </div>
  );
};
