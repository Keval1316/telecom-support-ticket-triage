import React, { useState, useEffect } from 'react'
import { Navbar } from './components/Navbar'
import { InputPanel } from './pages/InputPanel'
import { DashboardView } from './pages/DashboardView'
import { FilterTrendsView } from './pages/FilterTrendsView'
import { ReviewQueueView } from './pages/ReviewQueueView'
import { fetchAnalyticsSummary, AnalyticsSummary } from './lib/api'

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('input')
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [reviewCount, setReviewCount] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)

  const refreshGlobalTelemetry = async () => {
    try {
      const sum = await fetchAnalyticsSummary()
      setSummary(sum)
      // Use the analytics summary's pending review count (unresolved HUMAN_REVIEW tickets only)
      setReviewCount(sum.human_review_count)
    } catch (e) {
      console.error('Error updating telemetry:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refreshGlobalTelemetry()
    // Auto-refresh telemetry every 15 seconds
    const interval = setInterval(refreshGlobalTelemetry, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-slate-100 flex flex-col font-sans">
      <Navbar currentTab={currentTab} setCurrentTab={setCurrentTab} reviewCount={reviewCount} />

      <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
        {currentTab === 'input' && <InputPanel onTriageComplete={refreshGlobalTelemetry} />}
        {currentTab === 'dashboard' && <DashboardView summary={summary} loading={loading} />}
        {currentTab === 'trends' && <FilterTrendsView />}
        {currentTab === 'review' && <ReviewQueueView onResolved={refreshGlobalTelemetry} totalReviewCount={reviewCount} />}
      </main>

      <footer className="glass-panel border-t border-white/5 py-4 px-6 text-center text-xs text-slate-500">
        <p>
          AI-Powered Support Ticket Triage System • Fine-Tuned Qwen2.5-3B • Zero Paid API Runtime Cost • Fast, Secure & Local
        </p>
      </footer>
    </div>
  )
}

export default App
