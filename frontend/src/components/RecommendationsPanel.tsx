import React from 'react';
import type { RecommendedStandard } from '../types/analysis';
import { RecommendationCard } from './RecommendationCard';

interface RecommendationsPanelProps {
  recommendations: RecommendedStandard[];
}

export const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({ recommendations }) => {
  return (
    <div style={{ marginTop: '2rem' }}>
      <h2 style={{ fontSize: '1.25rem', color: 'var(--color-primary)', marginBottom: '1rem' }}>Recommended Standards</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {recommendations.map((std, i) => (
          <RecommendationCard key={std.standard_id} standard={std} isTop={i === 0} />
        ))}
      </div>
    </div>
  );
};
