import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: 'Synthetic Generator', emoji: '🗂️' },
  { to: '/augmentation', label: 'Augmentation Lab', emoji: '🔬' },
  { to: '/ocr', label: 'OCR Engine', emoji: '🔍' },
  { to: '/batch', label: 'Batch Processing', emoji: '⚙️' },
  { to: '/evaluation', label: 'Evaluation', emoji: '📊' },
  { to: '/rl', label: 'RL Training', emoji: '🤖' },
  { to: '/schema-extraction', label: 'Schema Extraction', emoji: '🧩' },
]

const navStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 4,
  padding: '8px 24px',
  background: '#1a1a2e',
  borderBottom: '1px solid #2d2d44',
  flexWrap: 'wrap',
}

const linkStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 5,
  padding: '5px 12px',
  borderRadius: 6,
  fontSize: 13,
  fontWeight: 500,
  color: '#aab',
  textDecoration: 'none',
  transition: 'background 0.15s, color 0.15s',
}

const activeLinkStyle: React.CSSProperties = {
  ...linkStyle,
  background: '#2d2d55',
  color: '#fff',
}

export default function NavBar() {
  return (
    <nav style={navStyle} aria-label="Main navigation">
      <span style={{ fontSize: 13, fontWeight: 700, color: '#7b8cde', marginRight: 8, whiteSpace: 'nowrap' }}>
        DocSim
      </span>
      {NAV_ITEMS.map(({ to, label, emoji }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          style={({ isActive }) => (isActive ? activeLinkStyle : linkStyle)}
        >
          <span aria-hidden="true">{emoji}</span>
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
