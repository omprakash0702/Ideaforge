'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { motion } from 'framer-motion'
import { Download } from 'lucide-react'
import type { Report } from '@/lib/api'

interface Props { report: Report }

export function ReportView({ report }: Props) {
  function downloadMd() {
    const blob = new Blob([report.markdown_report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ideaforge-report-${report.project_id.slice(0, 8)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white font-serif">Final Report</h2>
        <button
          onClick={downloadMd}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border)] text-xs text-[var(--muted)] hover:text-white hover:border-[var(--accent)] transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Download .md
        </button>
      </div>

      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8">
        <div className="prose-cinema">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {report.markdown_report}
          </ReactMarkdown>
        </div>
      </div>
    </motion.div>
  )
}
