import React from 'react';
import type { ExtractedRequirements } from '../types/analysis';

interface RequirementsPanelProps {
  requirements: ExtractedRequirements;
}

export const RequirementsPanel: React.FC<RequirementsPanelProps> = ({ requirements }) => {
  const metaFields = [
    { label: 'Product', value: requirements.product },
    { label: 'Category', value: requirements.category },
    { label: 'Quantity', value: requirements.quantity },
    { label: 'Application', value: requirements.application },
  ];

  return (
    <div className="card" style={{ marginTop: '2rem' }}>
      <h2 style={{ fontSize: '1.25rem', color: 'var(--color-primary)', marginBottom: '1rem' }}>Extracted Requirements</h2>
      <div className="grid-4">
        {metaFields.map((field, i) => (
          <div key={i} style={{ background: '#f9fafb', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '0.25rem' }}>{field.label}</div>
            <div style={{ fontWeight: '600' }}>{field.value || 'N/A'}</div>
          </div>
        ))}
      </div>

      <h3 style={{ fontSize: '1rem', marginTop: '1.5rem', marginBottom: '0.5rem' }}>Technical Specifications</h3>
      <div style={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
        {requirements.technical_requirements.length > 0 ? (
          <ul style={{ margin: 0, padding: '0.5rem 1.5rem' }}>
            {requirements.technical_requirements.map((req, i) => (
              <li key={i} style={{ padding: '0.5rem 0', borderBottom: i < requirements.technical_requirements.length -1 ? '1px solid var(--color-border)' : 'none' }}>
                {req}
              </li>
            ))}
          </ul>
        ) : (
          <div style={{ padding: '1rem', color: 'var(--color-text-secondary)' }}>No specifications extracted.</div>
        )}
      </div>
    </div>
  );
};
