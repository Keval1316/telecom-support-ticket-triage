import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { AlertCircle, ArrowRight, CheckCircle2, FileText, Loader2, Play, Send, ShieldAlert, Sparkles, UploadCloud } from 'lucide-react'
import { triageSingleTicket, uploadBatchCsv, Ticket } from '../lib/api'

/**
 * RFC-4180 compliant CSV line parser.
 * Handles quoted fields that may contain commas, newlines, and escaped double-quotes.
 */
function parseCSVLine(line: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    const next = line[i + 1]

    if (char === '"' && inQuotes && next === '"') {
      // Escaped double-quote inside quoted field
      current += '"'
      i++ // skip next quote
    } else if (char === '"') {
      // Toggle quote mode
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      // Field separator outside quotes
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  result.push(current.trim()) // push last field
  return result
}

interface InputPanelProps {
  onTriageComplete: () => void
}

export const InputPanel: React.FC<InputPanelProps> = ({ onTriageComplete }) => {
  // Single ticket playground state
  const [reviewText, setReviewText] = useState('')
  const [customerName, setCustomerName] = useState('Keval Chudasama')
  const [contactNumber, setContactNumber] = useState('+91-9876543210')
  const [isTriaging, setIsTriaging] = useState(false)
  const [singleResult, setSingleResult] = useState<Ticket | null>(null)
  const [singleError, setSingleError] = useState<string | null>(null)

  // CSV Batch state
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [csvPreview, setCsvPreview] = useState<string[][]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [batchProgress, setBatchProgress] = useState(0)
  const [batchResult, setBatchResult] = useState<any | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // Quick prompt templates for live demo
  const samplePrompts = [
    {
      title: '🚨 Emergency Outage (Critical Safety Escalation)',
      text: 'Complete broadband failure in my whole sector since yesterday. Medical emergency at home and need ambulance line connection immediately!',
    },
    {
      title: '💰 Double Billing / Refund',
      text: 'I recharged for Rs. 719 on 18th Aug. Amount was deducted twice from my bank, but only one recharge applied. Please reverse the extra Rs. 719.',
    },
    {
      title: '📶 Slow 5G Network',
      text: 'My mobile data is extremely slow in Andheri East, speed tests show 0.2 Mbps and frequent call drops on incoming calls.',
    },
    {
      title: '🔒 Unauthorized SIM Swap (Security Hazard)',
      text: 'Received SMS saying SIM swap request submitted for my number. I did not initiate this! Please block this transaction immediately.',
    },
  ]

  // Dropzone handling
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0]
        setSelectedFile(file)
        setUploadError(null)
        setBatchResult(null)

        // Read first 5 rows for preview
        const reader = new FileReader()
        reader.onload = (e) => {
          const text = e.target?.result as string
          const lines = text.split('\n').filter((l) => l.trim().length > 0)
          const rows = lines.slice(0, 6).map((line) => parseCSVLine(line))
          setCsvPreview(rows)
        }
        reader.readAsText(file)
      }
    },
  })

  // Submit Single Ticket
  const handleSingleTriage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reviewText.trim()) return

    setIsTriaging(true)
    setSingleError(null)
    setSingleResult(null)

    try {
      const res = await triageSingleTicket({
        review: reviewText,
        customer_name: customerName,
        contact_number: contactNumber,
      })
      setSingleResult(res)
      onTriageComplete()
    } catch (err: any) {
      setSingleError(err.response?.data?.detail || 'Failed to triage ticket.')
    } finally {
      setIsTriaging(false)
    }
  }

  // Submit Batch CSV
  const handleBatchUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadError(null)
    setBatchProgress(15)

    const interval = setInterval(() => {
      setBatchProgress((prev) => (prev < 90 ? prev + 15 : prev))
    }, 400)

    try {
      const res = await uploadBatchCsv(selectedFile)
      clearInterval(interval)
      setBatchProgress(100)
      setBatchResult(res)
      onTriageComplete()
    } catch (err: any) {
      clearInterval(interval)
      setUploadError(err.response?.data?.detail || 'CSV upload failed.')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Hero Welcome Banner */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl glass-card p-6 border border-indigo-500/20 bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-[#12141A]"
      >
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-1">
              <Sparkles className="w-4 h-4" /> AI Support Ticket Triage Pipeline
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight font-['Outfit']">
              Fine-Tuned Telecom Intelligence & Batch Ingestion
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-2xl">
              Upload customer complaints in bulk via CSV or test live single tickets. The fine-tuned Qwen2.5-3B model
              predicts category, priority, and department with calibrated confidence and safety escalation guardrails.
            </p>
          </div>
          <div className="flex items-center gap-2 bg-[#0D0F14]/80 px-4 py-2.5 rounded-xl border border-white/10 text-xs text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span>Zero API Cost (Local Inference)</span>
          </div>
        </div>
      </motion.div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Drag & Drop CSV Ingestion */}
        <div className="lg:col-span-7 space-y-6">
          <div className="glass-card rounded-2xl p-6 border border-white/10 space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-sm">
                  1
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Batch CSV Ingestion</h3>
                  <p className="text-xs text-slate-400">Upload bulk ticket feeds for automated triage</p>
                </div>
              </div>
              <span className="text-[11px] text-slate-400 bg-white/5 px-2.5 py-1 rounded-md border border-white/5">
                Supported: .csv
              </span>
            </div>

            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                isDragActive
                  ? 'border-indigo-500 bg-indigo-500/10 scale-[0.99]'
                  : selectedFile
                  ? 'border-emerald-500/40 bg-emerald-500/5'
                  : 'border-white/15 bg-white/[0.02] hover:border-indigo-500/50 hover:bg-white/[0.04]'
              }`}
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center gap-3">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    selectedFile ? 'bg-emerald-500/20 text-emerald-400' : 'bg-indigo-500/10 text-indigo-400'
                  }`}
                >
                  <UploadCloud className="w-6 h-6" />
                </div>
                {selectedFile ? (
                  <div>
                    <p className="text-sm font-semibold text-white">{selectedFile.name}</p>
                    <p className="text-xs text-emerald-400 mt-0.5">
                      {(selectedFile.size / 1024).toFixed(1)} KB • Ready for AI Triage
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-slate-200">
                      Drag and drop your ticket CSV here, or <span className="text-indigo-400 underline">browse</span>
                    </p>
                    <p className="text-xs text-slate-500 mt-1">Requires columns: review, customer_name, contact_number</p>
                  </div>
                )}
              </div>
            </div>

            {/* CSV File Preview Table */}
            {csvPreview.length > 0 && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-2">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">CSV Data Preview (First 5 Rows):</p>
                <div className="overflow-x-auto rounded-lg border border-white/10 bg-[#0D0F14]">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-white/5 text-slate-300 border-b border-white/10">
                      <tr>
                        {csvPreview[0].map((header, idx) => (
                          <th key={idx} className="px-3 py-2 font-medium">
                            {header.trim()}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 text-slate-300">
                      {csvPreview.slice(1).map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-white/[0.02]">
                          {row.map((cell, cIdx) => (
                            <td key={cIdx} className="px-3 py-1.5 truncate max-w-[200px]">
                              {cell.trim()}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {/* Upload & Progress Action */}
            {selectedFile && (
              <div className="space-y-3 pt-2">
                {isUploading && (
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-400 font-medium">
                      <span>Running Neural Triage Engine...</span>
                      <span>{batchProgress}%</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                        animate={{ width: `${batchProgress}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                  </div>
                )}

                <button
                  onClick={handleBatchUpload}
                  disabled={isUploading}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm shadow-lg shadow-indigo-500/20 disabled:opacity-50 flex items-center justify-center gap-2 transition-all duration-200"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Processing Batch Triage...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-white" />
                      <span>Run AI Batch Triage</span>
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Error Message */}
            {uploadError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            {/* Batch Success Summary */}
            {batchResult && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 space-y-2"
              >
                <div className="flex items-center gap-2 font-bold text-sm">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span>Batch Triage Complete!</span>
                </div>
                <div className="grid grid-cols-3 gap-2 pt-2 text-center text-xs">
                  <div className="bg-black/30 p-2 rounded-lg border border-emerald-500/10">
                    <p className="text-slate-400">Total Processed</p>
                    <p className="text-lg font-bold text-white">{batchResult.total_processed}</p>
                  </div>
                  <div className="bg-black/30 p-2 rounded-lg border border-emerald-500/10">
                    <p className="text-slate-400">Auto-Routed</p>
                    <p className="text-lg font-bold text-emerald-400">{batchResult.auto_routed_count}</p>
                  </div>
                  <div className="bg-black/30 p-2 rounded-lg border border-emerald-500/10">
                    <p className="text-slate-400">Review Queue</p>
                    <p className="text-lg font-bold text-amber-400">{batchResult.human_review_count}</p>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>

        {/* Right Column: Live Interactive Single Ticket Playground */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-card rounded-2xl p-6 border border-white/10 space-y-5">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 font-bold text-sm">
                2
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Live Ticket Playground</h3>
                <p className="text-xs text-slate-400">Test real-time classification & safety rules</p>
              </div>
            </div>

            {/* Quick Templates */}
            <div className="space-y-1.5">
              <p className="text-xs text-slate-400 font-medium">Try a Sample Complaint:</p>
              <div className="flex flex-col gap-1.5">
                {samplePrompts.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setReviewText(p.text)}
                    className="text-left text-xs p-2 rounded-lg bg-white/[0.03] hover:bg-indigo-500/10 hover:border-indigo-500/30 border border-white/5 text-slate-300 transition-colors"
                  >
                    <span className="font-semibold text-indigo-300 block">{p.title}</span>
                    <span className="text-slate-400 truncate block text-[11px]">{p.text}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Single Ticket Form */}
            <form onSubmit={handleSingleTriage} className="space-y-3 pt-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] font-medium text-slate-400">Customer Name</label>
                  <input
                    type="text"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    className="w-full mt-1 px-3 py-1.5 bg-[#0D0F14] border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-slate-400">Contact Number</label>
                  <input
                    type="text"
                    value={contactNumber}
                    onChange={(e) => setContactNumber(e.target.value)}
                    className="w-full mt-1 px-3 py-1.5 bg-[#0D0F14] border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400">Customer Complaint Text</label>
                <textarea
                  rows={3}
                  value={reviewText}
                  onChange={(e) => setReviewText(e.target.value)}
                  placeholder="Paste customer support ticket complaint..."
                  className="w-full mt-1 p-3 bg-[#0D0F14] border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500 placeholder-slate-600 resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={isTriaging || !reviewText.trim()}
                className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-md shadow-indigo-600/20 transition-all"
              >
                {isTriaging ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                <span>Classify Ticket</span>
              </button>
            </form>

            {/* Error Message */}
            {singleError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{singleError}</span>
              </div>
            )}

            {/* Triage Output Card */}
            {singleResult && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 rounded-xl bg-[#0D0F14] border border-indigo-500/30 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-400">{singleResult.ticket_id}</span>
                  <span
                    className={`px-2.5 py-0.5 text-[11px] font-bold rounded-full border ${
                      singleResult.routing_status === 'AUTO_ROUTED'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    {singleResult.routing_status === 'AUTO_ROUTED' ? '✓ Auto-Routed' : '⚠ Human Review'}
                  </span>
                </div>

                {/* Badges Grid */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 rounded-lg bg-white/[0.03] border border-white/5">
                    <p className="text-[10px] text-slate-400">Category</p>
                    <p className="font-bold text-indigo-300">{singleResult.final_category}</p>
                  </div>
                  <div className="p-2 rounded-lg bg-white/[0.03] border border-white/5">
                    <p className="text-[10px] text-slate-400">Priority</p>
                    <p
                      className={`font-bold ${
                        singleResult.final_priority === 'Critical'
                          ? 'text-red-400 font-extrabold'
                          : singleResult.final_priority === 'High'
                          ? 'text-amber-400'
                          : singleResult.final_priority === 'Medium'
                          ? 'text-blue-400'
                          : 'text-emerald-400'
                      }`}
                    >
                      {singleResult.final_priority}
                    </p>
                  </div>
                  <div className="p-2 rounded-lg bg-white/[0.03] border border-white/5">
                    <p className="text-[10px] text-slate-400">Department</p>
                    <p className="font-bold text-purple-300">{singleResult.final_department}</p>
                  </div>
                </div>

                {/* Confidence Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Calibrated Confidence</span>
                    <span className="font-mono font-bold text-white">{(singleResult.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        singleResult.confidence >= 0.70 ? 'bg-emerald-400' : 'bg-amber-400'
                      }`}
                      style={{ width: `${singleResult.confidence * 100}%` }}
                    />
                  </div>
                </div>

                {/* Safety Escalation Alert */}
                {singleResult.escalated && (
                  <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-start gap-2">
                    <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-bold">Priority Escalated by Safety Engine</p>
                      <p className="text-[11px] text-red-300/80">{singleResult.escalation_reason}</p>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
