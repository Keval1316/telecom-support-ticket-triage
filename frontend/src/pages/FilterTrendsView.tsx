import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ChevronLeft, ChevronRight, Filter, Search, TrendingDown, TrendingUp, Minus, ShieldAlert } from 'lucide-react'
import { fetchTickets, fetchAnalyticsTrends, Ticket, AnalyticsTrends } from '../lib/api'

export const FilterTrendsView: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)

  // Filters
  const [category, setCategory] = useState<string>('')
  const [priority, setPriority] = useState<string>('')
  const [department, setDepartment] = useState<string>('')
  const [routingStatus, setRoutingStatus] = useState<string>('')
  const [search, setSearch] = useState<string>('')

  // Trends
  const [trends, setTrends] = useState<AnalyticsTrends | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [ticketRes, trendRes] = await Promise.all([
        fetchTickets({
          page,
          page_size: 15,
          category: category || undefined,
          priority: priority || undefined,
          department: department || undefined,
          routing_status: routingStatus || undefined,
          search: search || undefined,
        }),
        fetchAnalyticsTrends(7),
      ])

      setTickets(ticketRes.tickets)
      setTotal(ticketRes.total)
      setTotalPages(ticketRes.total_pages)
      setTrends(trendRes)
    } catch (e) {
      console.error('Error fetching filtered data:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [page, category, priority, department, routingStatus])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    loadData()
  }

  const renderTrendIcon = (direction: string, pct: number) => {
    if (direction === 'UP') {
      return (
        <span className="flex items-center text-xs font-bold text-emerald-400">
          <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> +{pct}%
        </span>
      )
    } else if (direction === 'DOWN') {
      return (
        <span className="flex items-center text-xs font-bold text-red-400">
          <TrendingDown className="w-3.5 h-3.5 mr-0.5" /> {pct}%
        </span>
      )
    }
    return (
      <span className="flex items-center text-xs font-bold text-slate-400">
        <Minus className="w-3.5 h-3.5 mr-0.5" /> 0%
      </span>
    )
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Trend Indicator Cards Grid */}
      {trends && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-['Outfit']">
              📈 7-Day Period-over-Period Trends
            </h3>
            <span className="text-xs text-slate-500">Comparing current 7 days vs previous 7 days</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {trends.summary_trends.concat(trends.category_trends.slice(0, 3)).map((item, idx) => (
              <div key={idx} className="glass-card rounded-xl p-3.5 border border-white/5 space-y-1">
                <p className="text-[11px] text-slate-400 font-medium truncate">{item.name}</p>
                <div className="flex items-center justify-between">
                  <span className="text-base font-bold text-white font-['Outfit']">{item.current}</span>
                  {renderTrendIcon(item.direction, item.percentage_change)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="glass-card rounded-2xl p-5 border border-white/10 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Filter className="w-4 h-4 text-indigo-400" />
            <span>Search & Filter Tickets</span>
          </div>
          <span className="text-xs text-slate-400 font-medium">Found {total.toLocaleString()} records</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="relative sm:col-span-2 md:col-span-1">
            <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              placeholder="Search keyword/ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-2 bg-[#0D0F14] border border-white/10 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </form>

          {/* Category Dropdown */}
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value)
              setPage(1)
            }}
            className="px-3 py-2 bg-[#0D0F14] border border-white/10 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Categories</option>
            <option value="Billing">Billing</option>
            <option value="Technical">Technical</option>
            <option value="Account">Account</option>
            <option value="Refund">Refund</option>
            <option value="General">General</option>
          </select>

          {/* Priority Dropdown */}
          <select
            value={priority}
            onChange={(e) => {
              setPriority(e.target.value)
              setPage(1)
            }}
            className="px-3 py-2 bg-[#0D0F14] border border-white/10 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          {/* Department Dropdown */}
          <select
            value={department}
            onChange={(e) => {
              setDepartment(e.target.value)
              setPage(1)
            }}
            className="px-3 py-2 bg-[#0D0F14] border border-white/10 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Departments</option>
            <option value="Finance">Finance</option>
            <option value="Technical">Technical</option>
            <option value="Account">Account</option>
            <option value="Refunds">Refunds</option>
            <option value="General Support">General Support</option>
          </select>

          {/* Routing Status */}
          <select
            value={routingStatus}
            onChange={(e) => {
              setRoutingStatus(e.target.value)
              setPage(1)
            }}
            className="px-3 py-2 bg-[#0D0F14] border border-white/10 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Routing</option>
            <option value="AUTO_ROUTED">Auto-Routed</option>
            <option value="HUMAN_REVIEW">Human Review</option>
          </select>
        </div>
      </div>

      {/* Ticket Table */}
      <div className="glass-card rounded-2xl border border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-[#0D0F14] text-slate-400 border-b border-white/10 uppercase tracking-wider font-semibold text-[10px]">
              <tr>
                <th className="px-4 py-3">Ticket ID</th>
                <th className="px-4 py-3">Customer</th>
                <th className="px-4 py-3">Complaint Text</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Department</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 bg-[#12141A]/50">
              {loading ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-slate-500">
                    Loading tickets...
                  </td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-slate-500">
                    No tickets found matching filters.
                  </td>
                </tr>
              ) : (
                tickets.map((t) => (
                  <tr key={t.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-slate-300">{t.ticket_id}</td>
                    <td className="px-4 py-3 font-medium text-white">{t.customer_name}</td>
                    <td className="px-4 py-3 max-w-xs truncate text-slate-300" title={t.review}>
                      {t.review}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
                        {t.final_category}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-md font-bold text-[11px] ${
                          t.final_priority === 'Critical'
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : t.final_priority === 'High'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : t.final_priority === 'Medium'
                            ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}
                      >
                        {t.final_priority}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-purple-300 font-medium">{t.final_department}</td>
                    <td className="px-4 py-3 font-mono font-semibold text-slate-200">
                      {(t.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          t.routing_status === 'AUTO_ROUTED'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        }`}
                      >
                        {t.routing_status === 'AUTO_ROUTED' ? '✓ Auto' : '⚠ Review'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#0D0F14] border-t border-white/10 text-xs text-slate-400">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded-lg border border-white/10 hover:bg-white/5 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg border border-white/10 hover:bg-white/5 disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
