import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronLeft,
  ChevronRight,
  Filter,
  Search,
  TrendingDown,
  TrendingUp,
  Minus,
  ShieldAlert,
  Trash2,
  Loader2,
  CheckCircle2,
  X,
  UserCheck,
  Sparkles,
  Edit3,
  CornerDownRight,
  Clock,
  Phone,
  User,
} from 'lucide-react'
import {
  fetchTickets,
  fetchAnalyticsTrends,
  clearAllTickets,
  updateTicketLabels,
  Ticket,
  AnalyticsTrends,
} from '../lib/api'

export const FilterTrendsView: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [deletingAll, setDeletingAll] = useState(false)
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  // Manager Dialog Modal State
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const [editCategory, setEditCategory] = useState<string>('')
  const [editPriority, setEditPriority] = useState<string>('')
  const [editDepartment, setEditDepartment] = useState<string>('')
  const [editNotes, setEditNotes] = useState<string>('')
  const [savingEdit, setSavingEdit] = useState<boolean>(false)

  // Filters
  const [category, setCategory] = useState<string>('')
  const [priority, setPriority] = useState<string>('')
  const [department, setDepartment] = useState<string>('')
  const [routingStatus, setRoutingStatus] = useState<string>('')
  const [search, setSearch] = useState<string>('')

  // Trends
  const [trends, setTrends] = useState<AnalyticsTrends | null>(null)

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type })
    setTimeout(() => setToastMessage(null), 4000)
  }

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

  const handleDeleteAllData = async () => {
    if (!window.confirm('⚠️ DANGER: Are you sure you want to permanently delete ALL tickets from the entire database? This action cannot be undone.')) {
      return
    }
    setDeletingAll(true)
    try {
      const res = await clearAllTickets()
      setTickets([])
      setTotal(0)
      setTotalPages(1)
      showToast(`✓ All ${res.deleted_count} tickets permanently deleted. Database is now empty.`)
      await loadData()
    } catch (e) {
      console.error('Failed to clear all data:', e)
      showToast('Failed to clear all data', 'error')
    } finally {
      setDeletingAll(false)
    }
  }

  const handleOpenTicketModal = (ticket: Ticket) => {
    setSelectedTicket(ticket)
    setEditCategory(ticket.final_category)
    setEditPriority(ticket.final_priority)
    setEditDepartment(ticket.final_department)
    setEditNotes(ticket.reviewer_notes || '')
  }

  const handleCloseModal = () => {
    setSelectedTicket(null)
  }

  const handleSaveTicketOverride = async () => {
    if (!selectedTicket) return
    setSavingEdit(true)
    try {
      const updated = await updateTicketLabels(selectedTicket.id, {
        final_category: editCategory,
        final_priority: editPriority,
        final_department: editDepartment,
        reviewer_notes: editNotes || 'Manager manual override from filter table',
      })

      // Optimistically update in table list
      setTickets((prev) => prev.map((t) => (t.id === selectedTicket.id ? { ...t, ...updated } : t)))
      showToast(`✓ Ticket #${selectedTicket.ticket_id} updated successfully!`)
      setSelectedTicket(null)
    } catch (e) {
      console.error('Failed to update ticket labels:', e)
      showToast('Failed to update ticket labels', 'error')
    } finally {
      setSavingEdit(false)
    }
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
      {/* Toast Notification */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`fixed top-20 right-8 z-50 p-4 rounded-xl text-white font-medium text-xs shadow-2xl flex items-center gap-2 border ${
              toastMessage.type === 'success'
                ? 'bg-emerald-600 border-emerald-400 shadow-emerald-500/30'
                : 'bg-rose-600 border-rose-400 shadow-rose-500/30'
            }`}
          >
            <CheckCircle2 className="w-5 h-5" />
            <span>{toastMessage.text}</span>
          </motion.div>
        )}
      </AnimatePresence>

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
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 font-medium">Found {total.toLocaleString()} records</span>
            <button
              onClick={handleDeleteAllData}
              disabled={deletingAll || total === 0}
              title="Permanently wipe all tickets from the database"
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 transition-colors flex items-center gap-1.5 disabled:opacity-40"
            >
              {deletingAll ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
              <span>Delete All Data</span>
            </button>
          </div>
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
            className="w-full h-9 px-3.5 bg-[#0D0F14] border border-white/10 hover:border-white/20 rounded-lg text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
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
            className="w-full h-9 px-3.5 bg-[#0D0F14] border border-white/10 hover:border-white/20 rounded-lg text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
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
            className="w-full h-9 px-3.5 bg-[#0D0F14] border border-white/10 hover:border-white/20 rounded-lg text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
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
            className="w-full h-9 px-3.5 bg-[#0D0F14] border border-white/10 hover:border-white/20 rounded-lg text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
          >
            <option value="">All Routing</option>
            <option value="AUTO_ROUTED">Auto-Routed</option>
            <option value="HUMAN_REVIEW">Pending Human Review</option>
            <option value="RESOLVED">Human Resolved</option>
          </select>
        </div>
      </div>

      {/* Ticket Table */}
      <div className="glass-card rounded-2xl border border-white/10 overflow-hidden">
        <div className="px-4 py-3 bg-[#0D0F14]/70 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Tickets Ledger</span>
            <span className="text-[11px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-md border border-indigo-500/20">
              Click any ticket row to view full details & override AI outcome
            </span>
          </div>
        </div>

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
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 bg-[#12141A]/50">
              {loading ? (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-slate-500">
                    Loading tickets...
                  </td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-slate-500">
                    No tickets found matching filters.
                  </td>
                </tr>
              ) : (
                tickets.map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => handleOpenTicketModal(t)}
                    className="hover:bg-white/[0.04] transition-colors cursor-pointer group"
                  >
                    <td className="px-4 py-3 font-mono font-bold text-indigo-300 group-hover:text-indigo-200">
                      {t.ticket_id}
                    </td>
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
                      {t.routing_status === 'RESOLVED' || t.is_reviewed ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold border bg-teal-500/10 text-teal-300 border-teal-500/30">
                          ✓ Resolved
                        </span>
                      ) : t.routing_status === 'AUTO_ROUTED' ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold border bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                          ✓ Auto
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold border bg-amber-500/10 text-amber-400 border-amber-500/30">
                          ⚠ Review
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-300 text-[11px] font-medium border border-white/10 inline-flex items-center gap-1">
                        <Edit3 className="w-3 h-3 text-indigo-400" />
                        Edit
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

      {/* Manager Ticket Detail & Override Dialog Modal */}
      <AnimatePresence>
        {selectedTicket && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="glass-card bg-[#0F1117] rounded-2xl border border-white/15 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl space-y-5 p-6"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                    <Edit3 className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-white font-['Outfit']">
                        Ticket Detail & Manager Override
                      </h3>
                      <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        {selectedTicket.ticket_id}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Review AI classification outcome and apply manual corrections if needed.
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleCloseModal}
                  className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Customer Metadata Pill Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 p-3 rounded-xl bg-[#0D0F14] border border-white/5 text-xs">
                <div className="flex items-center gap-2 text-slate-300">
                  <User className="w-3.5 h-3.5 text-slate-500" />
                  <span className="truncate">{selectedTicket.customer_name || 'Customer'}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Phone className="w-3.5 h-3.5 text-slate-500" />
                  <span>{selectedTicket.contact_number || 'N/A'}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  <span className="truncate">
                    {selectedTicket.timestamp ? new Date(selectedTicket.timestamp).toLocaleDateString() : 'Recent'}
                  </span>
                </div>
              </div>

              {/* Complaint Text Box */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Customer Complaint Text
                </label>
                <div className="p-3.5 rounded-xl bg-[#08090C] border border-white/10 text-xs text-slate-200 leading-relaxed font-sans max-h-36 overflow-y-auto">
                  {selectedTicket.review}
                </div>
              </div>

              {/* AI Prediction Outcome vs Current Assignment */}
              <div className="p-3.5 rounded-xl bg-indigo-500/5 border border-indigo-500/20 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-indigo-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Original AI Prediction
                  </span>
                  <span className="text-slate-400">
                    Confidence: <strong className="text-white">{(selectedTicket.confidence * 100).toFixed(1)}%</strong>
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-[#0D0F14] p-2 rounded-lg border border-white/5">
                    <p className="text-[10px] text-slate-400">Category</p>
                    <p className="font-bold text-white mt-0.5">{selectedTicket.predicted_category}</p>
                  </div>
                  <div className="bg-[#0D0F14] p-2 rounded-lg border border-white/5">
                    <p className="text-[10px] text-slate-400">Priority</p>
                    <p className="font-bold text-white mt-0.5">{selectedTicket.predicted_priority}</p>
                  </div>
                  <div className="bg-[#0D0F14] p-2 rounded-lg border border-white/5">
                    <p className="text-[10px] text-slate-400">Department</p>
                    <p className="font-bold text-purple-300 mt-0.5">{selectedTicket.predicted_department}</p>
                  </div>
                </div>

                {selectedTicket.escalated && (
                  <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-[11px] flex items-center gap-1.5 mt-2">
                    <ShieldAlert className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                    <span>Safety Escalation: {selectedTicket.escalation_reason || 'Critical hazard triggered'}</span>
                  </div>
                )}
              </div>

              {/* Manager Change Form */}
              <div className="space-y-3 pt-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                  <UserCheck className="w-4 h-4" />
                  <span>Manager Label Override</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* Category Selector */}
                  <div>
                    <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                      Target Category
                    </label>
                    <select
                      value={editCategory}
                      onChange={(e) => setEditCategory(e.target.value)}
                      className="w-full h-9 mt-1 px-3.5 bg-[#0D0F14] border border-white/15 hover:border-white/25 rounded-lg text-xs font-medium text-white focus:outline-none focus:border-indigo-500 transition-colors"
                    >
                      <option value="Billing">Billing</option>
                      <option value="Technical">Technical</option>
                      <option value="Account">Account</option>
                      <option value="Refund">Refund</option>
                      <option value="General">General</option>
                    </select>
                  </div>

                  {/* Priority Selector */}
                  <div>
                    <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                      Target Priority
                    </label>
                    <select
                      value={editPriority}
                      onChange={(e) => setEditPriority(e.target.value)}
                      className="w-full h-9 mt-1 px-3.5 bg-[#0D0F14] border border-white/15 hover:border-white/25 rounded-lg text-xs font-medium text-white focus:outline-none focus:border-indigo-500 transition-colors"
                    >
                      <option value="Critical">Critical</option>
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </select>
                  </div>

                  {/* Department Selector */}
                  <div>
                    <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                      Target Department
                    </label>
                    <select
                      value={editDepartment}
                      onChange={(e) => setEditDepartment(e.target.value)}
                      className="w-full h-9 mt-1 px-3.5 bg-[#0D0F14] border border-white/15 hover:border-white/25 rounded-lg text-xs font-medium text-white focus:outline-none focus:border-indigo-500 transition-colors"
                    >
                      <option value="Finance">Finance</option>
                      <option value="Technical">Technical</option>
                      <option value="Account">Account</option>
                      <option value="Refunds">Refunds</option>
                      <option value="General Support">General Support</option>
                    </select>
                  </div>
                </div>

                {/* Manager Notes */}
                <div>
                  <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    Manager Reviewer Notes (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Corrected misclassification to Finance department due to double billing..."
                    value={editNotes}
                    onChange={(e) => setEditNotes(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-[#0D0F14] border border-white/15 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Modal Footer Actions */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  disabled={savingEdit}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 transition-colors"
                >
                  Close / Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveTicketOverride}
                  disabled={savingEdit}
                  className="px-5 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-600/20 disabled:opacity-50 transition-all"
                >
                  {savingEdit ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <UserCheck className="w-3.5 h-3.5" />}
                  <span>Save & Change Ticket</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}

