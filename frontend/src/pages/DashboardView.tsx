import React from 'react'
import { motion } from 'framer-motion'
import { Activity, AlertTriangle, CheckCircle2, DollarSign, Layers, ShieldAlert, Sparkles, TrendingUp, Users } from 'lucide-react'
import { ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts'
import { AnalyticsSummary } from '../lib/api'

interface DashboardViewProps {
  summary: AnalyticsSummary | null
  loading: boolean
}

export const DashboardView: React.FC<DashboardViewProps> = ({ summary, loading }) => {
  if (loading || !summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] space-y-4">
        <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
        <p className="text-sm text-slate-400">Loading live analytics telemetry...</p>
      </div>
    )
  }

  // Category Donut Chart Data
  const categoryData = Object.entries(summary.categories).map(([name, value]) => ({
    name,
    value,
  }))
  const CATEGORY_COLORS = ['#6366F1', '#38BDF8', '#F59E0B', '#EC4899', '#10B981']

  // Priority Chart Data
  const priorityData = [
    { name: 'Critical', count: summary.priorities['Critical'] || 0, fill: '#EF4444' },
    { name: 'High', count: summary.priorities['High'] || 0, fill: '#F59E0B' },
    { name: 'Medium', count: summary.priorities['Medium'] || 0, fill: '#3B82F6' },
    { name: 'Low', count: summary.priorities['Low'] || 0, fill: '#10B981' },
  ]

  // Department Chart Data
  const departmentData = Object.entries(summary.departments).map(([name, count]) => ({
    name,
    count,
  }))

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* KPI 1: Total Volume */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="glass-card rounded-2xl p-5 border border-white/10 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Tickets</span>
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-3xl font-extrabold text-white tracking-tight font-['Outfit']">
              {summary.total_tickets.toLocaleString()}
            </h3>
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
              <span className="text-emerald-400 font-medium">100% telemetry coverage</span>
            </p>
          </div>
        </motion.div>

        {/* KPI 2: Auto-Routed */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="glass-card rounded-2xl p-5 border border-white/10 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Auto-Routed</span>
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-3xl font-extrabold text-emerald-400 tracking-tight font-['Outfit']">
              {summary.auto_routed_count.toLocaleString()}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              <span className="font-semibold text-emerald-300">{summary.auto_routing_rate}%</span> of total volume
            </p>
          </div>
        </motion.div>

        {/* KPI 3: Human Review Queue */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="glass-card rounded-2xl p-5 border border-white/10 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Human Review</span>
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-3xl font-extrabold text-amber-400 tracking-tight font-['Outfit']">
              {summary.human_review_count.toLocaleString()}
            </h3>
            <p className="text-xs text-slate-400 mt-1">Low confidence or safety flagged</p>
          </div>
        </motion.div>

        {/* KPI 4: Mean Confidence */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
          className="glass-card rounded-2xl p-5 border border-white/10 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Confidence</span>
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-3xl font-extrabold text-purple-300 tracking-tight font-['Outfit']">
              {(summary.avg_confidence * 100).toFixed(1)}%
            </h3>
            <p className="text-xs text-slate-400 mt-1">Calibrated token logprob score</p>
          </div>
        </motion.div>
      </div>

      {/* Visual Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Category Breakdown Donut */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="lg:col-span-5 glass-card rounded-2xl p-6 border border-white/10 space-y-4 flex flex-col justify-between"
        >
          <div>
            <h4 className="text-base font-semibold text-white font-['Outfit']">Ticket Category Distribution</h4>
            <p className="text-xs text-slate-400">Billing, Technical, Account, Refund & General</p>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {categoryData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#12141A',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Priority Severity Breakdown */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="lg:col-span-7 glass-card rounded-2xl p-6 border border-white/10 space-y-4 flex flex-col justify-between"
        >
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-base font-semibold text-white font-['Outfit']">Priority Severity Spectrum</h4>
              <p className="text-xs text-slate-400">Critical, High, Medium & Low workload</p>
            </div>
            {summary.critical_count > 0 && (
              <span className="px-3 py-1 text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/30 rounded-full glow-critical flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                {summary.critical_count} Critical Active
              </span>
            )}
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={priorityData}>
                <XAxis dataKey="name" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                  contentStyle={{
                    backgroundColor: '#12141A',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {priorityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Department Workload Horizontal Bar */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="lg:col-span-12 glass-card rounded-2xl p-6 border border-white/10 space-y-4"
        >
          <div>
            <h4 className="text-base font-semibold text-white font-['Outfit']">Department Routing Allocation</h4>
            <p className="text-xs text-slate-400">Finance, Technical, Account, Refunds & General Support</p>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={departmentData} layout="vertical" margin={{ left: 30, right: 30 }}>
                <XAxis type="number" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#94A3B8" fontSize={12} tickLine={false} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                  contentStyle={{
                    backgroundColor: '#12141A',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" fill="#8B5CF6" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
