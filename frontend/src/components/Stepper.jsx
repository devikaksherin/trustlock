export default function Stepper({ steps, activeIndex, staticMode }) {
  return (
    <div className="stepper" style={{ display: 'flex', gap: '8px', overflowX: 'auto', padding: '16px 0' }}>
      {steps.map((step, idx) => {
        const isPast = idx < activeIndex;
        const isActive = idx === activeIndex;
        const color = isActive ? 'var(--brand)' : isPast ? 'var(--ink)' : 'var(--ink-3)';
        
        return (
          <div key={idx} style={{ flex: '1', minWidth: '120px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ height: '4px', background: color, borderRadius: '2px', opacity: (isActive || isPast || staticMode) ? 1 : 0.3 }} />
            <div style={{ fontSize: 'var(--text-sm)', fontWeight: isActive ? '600' : '400', color: staticMode ? 'var(--ink)' : color }}>
              {step.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}
