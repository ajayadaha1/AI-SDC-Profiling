interface LogoProps {
  size?: number;
}

export default function Logo({ size = 28 }: LogoProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      fill="none"
      width={size}
      height={size}
      style={{ borderRadius: size > 40 ? 12 : 4, flexShrink: 0 }}
    >
      <defs>
        <linearGradient id="logo-bg" x1="0" y1="0" x2="512" y2="512" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0d1b2a"/>
          <stop offset="100%" stopColor="#1b2d4a"/>
        </linearGradient>
        <linearGradient id="logo-accent" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#00bfa5"/>
          <stop offset="100%" stopColor="#00e5ff"/>
        </linearGradient>
        <linearGradient id="logo-pulse" x1="0" y1="0.5" x2="1" y2="0.5">
          <stop offset="0%" stopColor="#00bfa5"/>
          <stop offset="40%" stopColor="#00e5ff"/>
          <stop offset="60%" stopColor="#ff5252"/>
          <stop offset="100%" stopColor="#ff1744"/>
        </linearGradient>
      </defs>

      {/* Background rounded square */}
      <rect x="16" y="16" width="480" height="480" rx="96" fill="url(#logo-bg)"/>
      <rect x="16" y="16" width="480" height="480" rx="96" stroke="url(#logo-accent)" strokeWidth="3" fill="none" opacity="0.3"/>

      {/* CPU chip outline */}
      <rect x="140" y="140" width="232" height="232" rx="24" stroke="url(#logo-accent)" strokeWidth="6" fill="none" opacity="0.5"/>

      {/* CPU pins - top */}
      <line x1="200" y1="116" x2="200" y2="140" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="240" y1="116" x2="240" y2="140" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="280" y1="116" x2="280" y2="140" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="320" y1="116" x2="320" y2="140" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>

      {/* CPU pins - bottom */}
      <line x1="200" y1="372" x2="200" y2="396" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="240" y1="372" x2="240" y2="396" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="280" y1="372" x2="280" y2="396" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="320" y1="372" x2="320" y2="396" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>

      {/* CPU pins - left */}
      <line x1="116" y1="200" x2="140" y2="200" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="116" y1="240" x2="140" y2="240" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="116" y1="280" x2="140" y2="280" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="116" y1="320" x2="140" y2="320" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>

      {/* CPU pins - right */}
      <line x1="372" y1="200" x2="396" y2="200" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="372" y1="240" x2="396" y2="240" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="372" y1="280" x2="396" y2="280" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>
      <line x1="372" y1="320" x2="396" y2="320" stroke="#00bfa5" strokeWidth="4" strokeLinecap="round" opacity="0.4"/>

      {/* Heartbeat / fault pulse line */}
      <polyline
        points="160,256 200,256 215,256 225,210 240,302 255,218 270,290 285,230 300,256 320,256 352,256"
        stroke="url(#logo-pulse)" strokeWidth="5" fill="none" strokeLinecap="round" strokeLinejoin="round"/>

      {/* Fault marker (red dot) */}
      <circle cx="255" cy="218" r="8" fill="#ff1744" opacity="0.9"/>
      <circle cx="255" cy="218" r="14" fill="none" stroke="#ff1744" strokeWidth="2" opacity="0.4"/>

      {/* Neural network nodes */}
      <circle cx="196" cy="180" r="5" fill="#00bfa5" opacity="0.6"/>
      <circle cx="316" cy="180" r="5" fill="#00bfa5" opacity="0.6"/>
      <circle cx="196" cy="332" r="5" fill="#00bfa5" opacity="0.6"/>
      <circle cx="316" cy="332" r="5" fill="#00bfa5" opacity="0.6"/>
      <line x1="196" y1="185" x2="225" y2="210" stroke="#00bfa5" strokeWidth="1.5" opacity="0.3"/>
      <line x1="316" y1="185" x2="285" y2="230" stroke="#00bfa5" strokeWidth="1.5" opacity="0.3"/>
      <line x1="196" y1="327" x2="240" y2="302" stroke="#00bfa5" strokeWidth="1.5" opacity="0.3"/>
      <line x1="316" y1="327" x2="270" y2="290" stroke="#00bfa5" strokeWidth="1.5" opacity="0.3"/>

      {/* "AI" badge */}
      <rect x="340" y="100" width="56" height="28" rx="8" fill="#00bfa5"/>
      <text x="368" y="120" fontFamily="system-ui, -apple-system, sans-serif" fontSize="16" fontWeight="700" fill="#0d1b2a" textAnchor="middle">AI</text>

      {/* "FP" text */}
      <text x="256" y="394" fontFamily="ui-monospace, monospace" fontSize="14" fontWeight="600" fill="#00bfa5" textAnchor="middle" opacity="0.5">FP</text>
    </svg>
  );
}
