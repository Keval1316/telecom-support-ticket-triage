import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertCircle, Check, CheckCircle2, CornerDownRight, Inbox, Loader2, ShieldAlert, Sparkles, UserCheck, CheckCheck, Trash2, RefreshCw } from 'lucide-react'
import {
  fetchReviewQueue,
  resolveReviewTicket,
  resolveAllReviewTickets,
  clearReviewQueue,
  recalculateConfidenceScores,
  Ticket,
} from '../lib/api'

interface ReviewQueueViewProps {
  onResolved: () => void
  totalReviewCount: number
}

export const ReviewQueueView: React.FC<ReviewQueueViewProps> = ({ onResolved, totalReviewCount }) => {
  const [queue, setQueue] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [resolvingId, setResolvingId] = useState<number | null>(null)
  const [bulkLoading, setBulkLoading] = useState<string | null>(null)
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  // Local editing states per ticket
  const [edits, setEdits] = useState<
    Record<number, { category: string; priority: string; department: string; notes: string }>
  >({})

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type })
    setTimeout(() => setToastMessage(null), 4000)
  }

  const loadQueue = async () => {
    setLoading(true)
    try {
      const tickets = await fetchReviewQueue()
      setQueue(tickets)

      // Initialize edit fields
      const initialEdits: Record<number, any> = {}
      tickets.forEach((t) => {
        initialEdits[t.id] = {
          category: t.final_category,
          priority: t.final_priority,
          department: t.final_department,
          notes: '',
        }
      })
      setEdits(initialEdits)
    } catch (e) {
      console.error('Failed to load review queue:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadQueue()
  }, [])

  const handleFieldChange = (ticketId: number, field: string, value: string) => {
    setEdits((prev) => ({
      ...prev,
      [ticketId]: {
        ...prev[ticketId],
        [field]: value,
      },
    }))
  }

  const handleResolve = async (ticket: Ticket) => {
    const ticketEdit = edits[ticket.id]
    if (!ticketEdit) return

    setResolvingId(ticket.id)
    try {
      await resolveReviewTicket(ticket.id, {
        final_category: ticketEdit.category,
        final_priority: ticketEdit.priority,
        final_department: ticketEdit.department,
        reviewer_notes: ticketEdit.notes || undefined,
      })

      // Optimistically remove from queue
      setQueue((prev) => prev.filter((t) => t.id !== ticket.id))
      showToast(`✓ Ticket #${ticket.ticket_id} resolved and logged for active learning!`)
      onResolved()
    } catch (e) {
      console.error('Failed to resolve ticket:', e)
      showToast('Failed to resolve ticket', 'error')
    } finally {
      setResolvingId(null)
    }
  }

  const handlePassAll = async () => {
    if (!window.confirm(`Are you sure you want to approve and pass all ${totalReviewCount} pending review tickets?`)) {
      return
    }
    setBulkLoading('pass-all')
    try {
      const res = await resolveAllReviewTickets()
      setQueue([])
      showToast(`✓ ${res.resolved_count} ticket(s) approved and marked as resolved!`)
      onResolved()
    } catch (e) {
      console.error('Failed to pass all tickets:', e)
      showToast('Failed to pass all tickets', 'error')
    } finally {
      setBulkLoading(null)
    }
  }

  const handleDeletePendingQueue = async () => {
    if (!window.confirm(`Warning: Permanently delete all ${totalReviewCount} pending review tickets from the database?`)) {
      return
    }
    setBulkLoading('delete-pending')
    try {
      const res = await clearReviewQueue()
      setQueue([])
      showToast(`✓ ${res.deleted_count} pending ticket(s) permanently deleted.`)
      onResolved()
    } catch (e) {
      console.error('Failed to clear queue:', e)
      showToast('Failed to delete pending queue', 'error')
    } finally {
      setBulkLoading(null)
    }
  }

  const handleRecalculateConfidence = async () => {
    setBulkLoading('recalc-conf')
    try {
      const res = await recalculateConfidenceScores()
      showToast(`✓ Confidence scores recalculated for ${res.updated_count} ticket(s)!`)
      await loadQueue()
      onResolved()
    } catch (e) {
      console.error('Failed to recalculate confidence:', e)
      showToast('Failed to recalculate confidence', 'error')
    } finally {
      setBulkLoading(null)
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
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

      {/* Header Banner with Bulk Action Buttons */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 glass-card p-6 rounded-2xl border border-white/10">
        <div>
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs uppercase tracking-wider mb-1">
            <Inbox className="w-4 h-4" /> Human-in-the-Loop Oversight
          </div>
          <h2 className="text-xl font-bold text-white font-['Outfit']">Pending Review Queue ({totalReviewCount})</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Tickets flagged due to confidence below threshold (&lt;0.70) or safety guardrail escalation.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Recalculate Confidence Button */}
          <button
            onClick={handleRecalculateConfidence}
            disabled={bulkLoading !== null}
            title="Recalculates dynamic confidence for all tickets to replace old legacy scores"
            className="px-3 py-2 text-xs font-semibold rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            {bulkLoading === 'recalc-conf' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            <span>Recalculate Confidence</span>
          </button>

          {/* Pass All Tickets Button */}
          <button
            onClick={handlePassAll}
            disabled={bulkLoading !== null || queue.length === 0}
            className="px-3 py-2 text-xs font-semibold rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            {bulkLoading === 'pass-all' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCheck className="w-3.5 h-3.5" />}
            <span>Pass / Approve All</span>
          </button>

          {/* Delete All Pending Button */}
          <button
            onClick={handleDeletePendingQueue}
            disabled={bulkLoading !== null || queue.length === 0}
            className="px-3 py-2 text-xs font-semibold rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            {bulkLoading === 'delete-pending' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
            <span>Delete All Pending</span>
          </button>

          {/* Refresh Queue Button */}
          <button
            onClick={loadQueue}
            disabled={bulkLoading !== null}
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 transition-colors disabled:opacity-50"
          >
            Refresh Queue
          </button>
        </div>
      </div>


      {/* Cards List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16 space-y-3">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
          <p className="text-xs text-slate-500">Loading pending reviews...</p>
        </div>
      ) : queue.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center border border-white/10 space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 mx-auto flex items-center justify-center">
            <Check className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-white">Review Queue is Clear!</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            All low-confidence tickets have been safely resolved and audited.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <AnimatePresence>
            {queue.map((ticket) => {
              const edit = edits[ticket.id] || {
                category: ticket.final_category,
                priority: ticket.final_priority,
                department: ticket.final_department,
                notes: '',
              }

              return (
                <motion.div
                  key={ticket.id}
                  layout
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="glass-card rounded-2xl p-6 border border-white/10 space-y-4"
                >
                  {/* Top Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 pb-3">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-md border border-indigo-500/20">
                        {ticket.ticket_id}
                      </span>
                      <span className="text-xs text-slate-300 font-medium">{ticket.customer_name}</span>
                      <span className="text-xs text-slate-500">{ticket.contact_number}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-400">
                        Confidence: <strong className="text-white">{(ticket.confidence * 100).toFixed(1)}%</strong>
                      </span>
                      {ticket.escalated && (
                        <span className="px-2.5 py-0.5 text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30 rounded-full flex items-center gap-1">
                          <ShieldAlert className="w-3 h-3 text-red-400" />
                          Safety Escalated
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Complaint Text */}
                  <div className="bg-[#0D0F14] p-3.5 rounded-xl border border-white/5">
                    <p className="text-xs text-slate-200 leading-relaxed font-sans">{ticket.review}</p>
                    {ticket.escalation_reason && (
                      <p className="text-[11px] text-red-400 mt-2 flex items-center gap-1.5 font-medium">
                        <CornerDownRight className="w-3 h-3 flex-shrink-0" />
                        Trigger Reason: {ticket.escalation_reason}
                      </p>
                    )}
                  </div>

                  {/* Inline Correction Form */}
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-1">
                    {/* Category */}
                    <div>
                      <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                        Category
                      </label>
                      <select
                        value={edit.category}
                        onChange={(e) => handleFieldChange(ticket.id, 'category', e.target.value)}
                        className="w-full h-9 mt-1 px-3.5 bg-[#0D0F14] border border-white/10 hover:border-white/20 rounded-lg text-xs font-medium text-white focus:outline-none focus:border-indigo-500 transition-colors"
                      >
                        <option value="Billing">Billing</option>
                        <option value="Technical">Technical</option>
                        <option value="Account">Account</option>
                        <option value="Refund">Refund</option>
                        <option value="General">General</option>
                      </select>
                    </div>

                    {/* Priority */}
                    <div>
                      <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                        Priority
                      </label>
                      <select
                        value={edit.priority}
                        onChange={(e) => handleFieldChange(ticket.id, 'priority', e.target.value)}
                        className="w-full h-9 mt-1 px-3.5 bg-[#0D0F14] border border-white/10 hover:border-white/20 rounded-lg text-xs font-medium text-white focus:outline-none focus:border-indigo-500 transition-colors"
                      >
                        <option value="Critical">Critical</option>
                        <option value="High">High</option>
                        <option value="Medium">Medium</option>
                        <option value="Low">Low</option>
                      </select>
                    </div>

                    {/* Department */}
                    <div>
                      <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                        Department
                      </label>
                      <select
                        value={edit.department}
                        onChange={(e) => handleFieldChange(ticket.id, 'department', e.target.value)}
                        className="w-full h-9 mt-1 px-3.5 bg-[#0D0F14] border border-white/10 hover:border-white/20 rounded-lg text-xs font-medium text-white focus:outline-none focus:border-indigo-500 transition-colors"
                      >
                        <option value="Finance">Finance</option>
                        <option value="Technical">Technical</option>
                        <option value="Account">Account</option>
                        <option value="Refunds">Refunds</option>
                        <option value="General Support">General Support</option>
                      </select>
                    </div>

                    {/* Action Button */}
                    <div className="flex items-end">
                      <button
                        onClick={() => handleResolve(ticket)}
                        disabled={resolvingId === ticket.id}
                        className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-md shadow-emerald-600/20 disabled:opacity-50 transition-all"
                      >
                        {resolvingId === ticket.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <UserCheck className="w-3.5 h-3.5" />
                        )}
                        <span>Confirm & Resolve</span>
                      </button>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
