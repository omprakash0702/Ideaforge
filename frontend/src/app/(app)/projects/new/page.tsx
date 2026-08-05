'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Flame, Upload, X, FileText, AlertCircle, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'
import { useUser } from '@/hooks/useUser'

const PLACEHOLDER =
  `Example: Small restaurants struggle to compete with delivery apps that charge 30%+ commission fees, eating into already thin margins. Many can't afford their own ordering infrastructure but desperately need direct customer relationships...`

export default function NewProjectPage() {
  const router = useRouter()
  const { user, loading } = useUser()
  const fileRef = useRef<HTMLInputElement>(null)

  const [title, setTitle] = useState('')
  const [problem, setProblem] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [charCount, setCharCount] = useState(0)

  useEffect(() => {
    if (!loading && !user) router.push('/projects')
  }, [loading, user, router])

  if (loading || !user) return null

  function handleFiles(incoming: FileList | null) {
    if (!incoming) return
    const allowed = ['pdf', 'txt', 'md', 'html']
    const valid = Array.from(incoming).filter(f => {
      const ext = f.name.split('.').pop()?.toLowerCase() ?? ''
      return allowed.includes(ext) && f.size <= 20 * 1024 * 1024
    })
    setFiles(prev => [...prev, ...valid])
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!user || !title.trim() || !problem.trim()) return
    setSubmitting(true)

    let projectId!: string
    try {
      const project = await api.projects.create({
        user_id: user.id,
        title: title.trim(),
        problem_statement: problem.trim(),
      })
      projectId = project.id

      // Upload documents (best-effort)
      for (const file of files) {
        try {
          await api.projects.uploadDocument(project.id, file)
        } catch {
          toast.error(`Failed to upload ${file.name} — continuing without it`)
        }
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create project')
      setSubmitting(false)
      return
    }

    try {
      await api.projects.run(projectId)
      toast.success('The Council has been summoned.')
      router.push(`/projects/${projectId}`)
    } catch (err) {
      toast.error('Project created but workflow failed to start — open the project to retry.')
      router.push(`/projects/${projectId}`)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="space-y-8"
      >
        {/* Header */}
        <div>
          <div className="flex items-center gap-2 text-[var(--muted)] text-xs mb-4">
            <span>Projects</span>
            <ChevronRight className="w-3 h-3" />
            <span className="text-white">New Project</span>
          </div>
          <h1 className="text-2xl font-bold text-white font-serif">Submit Your Pitch</h1>
          <p className="text-[var(--muted)] text-sm mt-2">
            Describe the problem clearly. The more context you provide, the sharper the ideas will be.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <label className="text-[10px] text-[var(--muted)] tracking-widest uppercase">
              Project Name
            </label>
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="e.g. Restaurant Delivery Platform"
              className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-3 text-sm text-white placeholder-[var(--muted)] outline-none focus:border-[var(--accent)] transition-colors"
              required
            />
          </div>

          {/* Problem statement */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[10px] text-[var(--muted)] tracking-widest uppercase">
                Problem Statement
              </label>
              <span className={`text-[10px] tabular-nums ${charCount > 2000 ? 'text-red-400' : 'text-[var(--muted)]'}`}>
                {charCount} chars
              </span>
            </div>
            <textarea
              value={problem}
              onChange={e => { setProblem(e.target.value); setCharCount(e.target.value.length) }}
              placeholder={PLACEHOLDER}
              rows={8}
              className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-3 text-sm text-white placeholder-[var(--muted)] outline-none focus:border-[var(--accent)] transition-colors resize-none leading-relaxed"
              required
            />
            <p className="text-[10px] text-[var(--muted)]">
              Tip: Include market size, who is affected, and what solutions already exist.
            </p>
          </div>

          {/* Document upload */}
          <div className="space-y-3">
            <label className="text-[10px] text-[var(--muted)] tracking-widest uppercase">
              Research Documents <span className="normal-case text-[var(--muted)]/60">(optional — PDF, TXT, MD, HTML · max 20 MB)</span>
            </label>

            <div
              className="rounded-xl border-2 border-dashed border-[var(--border)] hover:border-[var(--accent)] transition-colors p-6 text-center cursor-pointer"
              onClick={() => fileRef.current?.click()}
              onDragOver={e => e.preventDefault()}
              onDrop={e => { e.preventDefault(); handleFiles(e.dataTransfer.files) }}
            >
              <Upload className="w-8 h-8 text-[var(--muted)] mx-auto mb-2" />
              <p className="text-sm text-[var(--muted)]">Drop files or click to browse</p>
              <input
                ref={fileRef}
                type="file"
                multiple
                accept=".pdf,.txt,.md,.html"
                className="hidden"
                onChange={e => handleFiles(e.target.files)}
              />
            </div>

            <AnimatePresence>
              {files.map((file, i) => (
                <motion.div
                  key={`${file.name}-${i}`}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex items-center gap-3 bg-[var(--surface)] border border-[var(--border)] rounded-lg px-3 py-2.5"
                >
                  <FileText className="w-4 h-4 text-[var(--accent)] shrink-0" />
                  <span className="text-xs text-white flex-1 truncate">{file.name}</span>
                  <span className="text-[10px] text-[var(--muted)]">
                    {(file.size / 1024).toFixed(0)} KB
                  </span>
                  <button
                    type="button"
                    onClick={() => setFiles(fs => fs.filter((_, j) => j !== i))}
                    className="text-[var(--muted)] hover:text-white transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Warning */}
          <div className="flex items-start gap-2 p-3 bg-amber-950/30 border border-amber-800/40 rounded-lg">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
            <p className="text-xs text-amber-300/80 leading-relaxed">
              The AI workflow will start immediately. It typically takes 2–5 minutes to complete.
              You can close this tab and come back — the process continues in the background.
            </p>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting || !title.trim() || !problem.trim()}
            className="w-full py-3.5 bg-[var(--accent)] text-white rounded-xl text-sm font-semibold hover:opacity-90 disabled:opacity-40 transition-opacity flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                />
                Summoning the Council…
              </>
            ) : (
              <>
                <Flame className="w-4 h-4" />
                Submit &amp; Run Workflow
              </>
            )}
          </button>
        </form>
      </motion.div>
    </div>
  )
}
