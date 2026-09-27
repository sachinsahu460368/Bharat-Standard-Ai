import React from 'react';
import type { StandardExplanation } from '../types/analysis';

interface ExplanationPanelProps {
  explanation?: StandardExplanation;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ explanation }) => {
  if (!explanation) return null;
  return (
    <div className="card">
      <h3>AI Rationale</h3>
      <p>{explanation.explanation}</p>
      <p><strong>Confidence:</strong> {explanation.confidence}</p>
    </div>
  );
};
