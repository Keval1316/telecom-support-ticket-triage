import React from 'react'
import { Activity, Cpu, Database, FileSpreadsheet, Filter, Inbox, LayoutDashboard, ShieldCheck, Sparkles } from 'lucide-react'

interface NavbarProps {
  currentTab: string
  setCurrentTab: (tab: string) => void
  reviewCount: number
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, reviewCount }) => {
  const tabs = [
    { id: 'input', label: 'Triage Playground & CSV', icon: FileSpreadsheet },
    { id: 'dashboard', label: 'Analytics Dashboard', icon: LayoutDashboard },
    { id: 'trends', label: 'Filters & Trends', icon: Filter },
    { id: 'review', label: 'Human Review Queue', icon: Inbox, badge: reviewCount },
  ]

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-white/10 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & Logo */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 p-0.5 shadow-lg shadow-indigo-500/20">
          <div className="w-full h-full bg-[#0D0F14] rounded-[10px] flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-indigo-400" />
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight text-white font-['Outfit']">TelecomAI Triage</h1>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              ₹0 Runtime Local LLM
            </span>
          </div>
          <p className="text-xs text-slate-400">Qwen2.5-3B QLoRA • Structured Classification & Safety Layer</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1.5 bg-[#0D0F14]/90 p-1.5 rounded-xl border border-white/5 shadow-inner">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = currentTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              className={`relative flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-500/25'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.badge !== undefined && tab.badge > 0 && (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                    isActive ? 'bg-white text-indigo-700' : 'bg-red-500/20 text-red-400 border border-red-500/30'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* System Status Pill */}
      <div className="hidden lg:flex items-center gap-3 text-xs text-slate-400 border-l border-white/10 pl-4">
        <div className="flex items-center gap-1.5">
          <Cpu className="w-4 h-4 text-indigo-400" />
          <span>Qwen2.5-3B 4-bit</span>
        </div>
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Safety Active</span>
        </div>
      </div>
    </header>
  )
}
