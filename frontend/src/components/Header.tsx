import React from 'react';

export const Header: React.FC = () => (
  <header style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem 2rem',
    background: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    marginBottom: '2rem'
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <div style={{ fontWeight: '800', fontSize: '1.5rem', color: 'var(--color-primary)', letterSpacing: '-0.025em' }}>
        Bharat Standards AI
      </div>
      <span style={{
        background: 'var(--color-secondary)',
        color: 'white',
        fontSize: '0.65rem',
        padding: '0.2rem 0.5rem',
        borderRadius: '999px',
        fontWeight: 'bold',
        textTransform: 'uppercase'
      }}>SIH 2026</span>
    </div>
    <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#16a34a' }}></span>
      System Operational
    </div>
  </header>
);
