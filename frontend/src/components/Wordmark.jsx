export function Wordmark({ size = 24, showText = true }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'inherit' }}>
      <svg width={size} height={size} viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="32" cy="32" r="24" />
        <circle cx="32" cy="32" r="12" />
        <circle cx="32" cy="32" r="2" fill="currentColor" />
        <path d="M32 8 L32 12 M32 20 L32 20" />
        {Array.from({ length: 24 }).map((_, i) => {
          const angle = (i * 15 * Math.PI) / 180;
          const isLong = i % 6 === 0;
          const outerR = 24;
          const innerR = isLong ? 18 : 20;
          const x1 = 32 + Math.sin(angle) * outerR;
          const y1 = 32 - Math.cos(angle) * outerR;
          const x2 = 32 + Math.sin(angle) * innerR;
          const y2 = 32 - Math.cos(angle) * innerR;
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} />;
        })}
        <polygon points="28,2 36,2 32,10" fill="currentColor" stroke="none" />
      </svg>
      {showText && (
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, letterSpacing: '.08em', fontSize: size * 0.75 }}>
          TRUSTLOCK
        </span>
      )}
    </div>
  );
}
