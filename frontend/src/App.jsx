import { NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Decisions from './pages/Decisions'
import Jobs from './pages/Jobs'
import Patterns from './pages/Patterns'

const NAV = [
  { to: '/', label: 'Dashboard', exact: true },
  { to: '/decisions', label: 'Decisions' },
  { to: '/patterns', label: 'Patterns' },
  { to: '/jobs', label: 'Autonomous Jobs' },
]

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950">
      <nav className="border-b border-slate-800 px-6">
        <div className="max-w-7xl mx-auto flex gap-6">
          {NAV.map(({ to, label, exact }) => (
            <NavLink
              key={to}
              to={to}
              end={exact}
              className={({ isActive }) =>
                `py-3.5 text-sm font-medium border-b-2 transition-colors ${
                  isActive
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-slate-500 hover:text-slate-300'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/decisions" element={<Decisions />} />
        <Route path="/patterns" element={<Patterns />} />
        <Route path="/jobs" element={<Jobs />} />
      </Routes>
    </div>
  )
}
