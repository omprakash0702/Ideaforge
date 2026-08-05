'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus, Flame, User, Mail, ArrowRight, Clock,
  Trash2, Loader2, AlertTriangle, LayoutGrid, List,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { api, type Project } from '@/lib/api'
import { useUser } from '@/hooks/useUser'
import { StatusBadge } from '@/components/project/StatusBadge'
import { formatRelative, formatDate } from '@/lib/utils'

/* ── User gate ────────────────────────────────────────────────────────────── */

type LoginFn = (name: string, email: string) => Promise<unknown>

function UserGate({ login, onLogin }: { login: LoginFn; onLogin: () => void }) {
  const [name, setName]     = useState('')
  const [email, setEmail]   = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !email.trim()) return
    setLoading(true)
    try {
      await login(name.trim(), email.trim())
      toast.success('Welcome to the Family.')
      onLogin()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to sign in')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-sm rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8"
      >
        <div className="flex items-center gap-2 mb-6">
          <Flame className="w-5 h-5 text-[var(--accent)]" />
          <h1 className="font-serif font-bold text-white">Enter the Room</h1>
        </div>
        <p className="text-xs text-[var(--muted)] mb-8 leading-relaxed">
          Introduce yourself to the Council. Your name and email identify your projects — no password required.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="text-[10px] text-[var(--muted)] tracking-widest uppercase">Name</span>
            <div className="mt-1.5 flex items-center gap-2 bg-[var(--elevated)] border border-[var(--border)] rounded-lg px-3 py-2.5 focus-within:border-[var(--accent)] transition-colors">
              <User className="w-3.5 h-3.5 text-[var(--muted)]" />
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Don Corleone"
                className="flex-1 bg-transparent text-sm text-white placeholder-[var(--muted)] outline-none"
                required
              />
            </div>
          </label>
          <label className="block">
            <span className="text-[10px] text-[var(--muted)] tracking-widest uppercase">Email</span>
            <div className="mt-1.5 flex items-center gap-2 bg-[var(--elevated)] border border-[var(--border)] rounded-lg px-3 py-2.5 focus-within:border-[var(--accent)] transition-colors">
              <Mail className="w-3.5 h-3.5 text-[var(--muted)]" />
              <input
                value={email}
                onChange={e => setEmail(e.target.value)}
                type="email"
                placeholder="don@corleone.com"
                className="flex-1 bg-transparent text-sm text-white placeholder-[var(--muted)] outline-none"
                required
              />
            </div>
          </label>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2"
          >
            {loading ? 'Signing in…' : 'Make Your Entrance'}
            {!loading && <ArrowRight className="w-4 h-4" />}
          </button>
        </form>
      </motion.div>
    </div>
  )
}

/* ── Status dot colour ────────────────────────────────────────────────────── */

function statusColor(s: Project['status']) {
  if (s === 'COMPLETED') return '#22c55e'
  if (s === 'FAILED')    return '#ef4444'
  if (s === 'CREATED')   return '#6366f1'
  return '#f59e0b'
}

/* ── Grid card ────────────────────────────────────────────────────────────── */

function GridCard({
  project, index, onDelete, deleting, confirmId, setConfirmId,
}: {
  project: Project
  index: number
  onDelete: (id: string) => void
  deleting: string | null
  confirmId: string | null
  setConfirmId: (id: string | null) => void
}) {
  const isConfirming = confirmId === project.id
  const isDeleting   = deleting === project.id

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ delay: index * 0.04, duration: 0.35 }}
      className="group relative rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 hover:border-[var(--accent)] transition-colors duration-300"
    >
      {/* Delete button */}
      {!isConfirming ? (
        <button
          onClick={e => { e.preventDefault(); setConfirmId(project.id) }}
          className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-[var(--muted)] hover:text-red-400 hover:bg-red-950/30 transition-all"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      ) : (
        <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-[var(--elevated)] border border-red-900/50 rounded-lg px-2 py-1">
          <span className="text-[10px] text-red-400">Delete?</span>
          <button
            onClick={e => { e.preventDefault(); onDelete(project.id) }}
            disabled={isDeleting}
            className="text-[10px] text-white bg-red-700 hover:bg-red-600 px-1.5 py-0.5 rounded disabled:opacity-50"
          >
            {isDeleting ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Yes'}
          </button>
          <button
            onClick={e => { e.preventDefault(); setConfirmId(null) }}
            className="text-[10px] text-[var(--muted)] hover:text-white px-1 py-0.5"
          >
            No
          </button>
        </div>
      )}

      <Link href={`/projects/${project.id}`} className="block">
        <div className="flex items-start gap-3 mb-3 pr-20">
          <h3 className="font-semibold text-white text-sm leading-tight group-hover:text-[var(--accent)] transition-colors line-clamp-1">
            {project.title}
          </h3>
        </div>
        <StatusBadge status={project.status} size="sm" />
        <p className="text-[var(--muted)] text-xs line-clamp-2 leading-relaxed mt-3 mb-4">
          {project.problem_statement}
        </p>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1 text-[10px] text-[var(--muted)]">
            <Clock className="w-3 h-3" />
            {formatRelative(project.created_at)}
          </span>
          <span className="text-[var(--accent)] text-xs flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            Open <ArrowRight className="w-3 h-3" />
          </span>
        </div>
      </Link>
    </motion.div>
  )
}

/* ── History row ──────────────────────────────────────────────────────────── */

function HistoryRow({
  project, index, onDelete, deleting, confirmId, setConfirmId,
}: {
  project: Project
  index: number
  onDelete: (id: string) => void
  deleting: string | null
  confirmId: string | null
  setConfirmId: (id: string | null) => void
}) {
  const isConfirming = confirmId === project.id
  const isDeleting   = deleting === project.id
  const color        = statusColor(project.status)

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 12 }}
      transition={{ delay: index * 0.04, duration: 0.3 }}
      className="flex gap-4 group"
    >
      {/* timeline line + dot */}
      <div className="flex flex-col items-center shrink-0 pt-1">
        <div
          className="w-2.5 h-2.5 rounded-full border-2 shrink-0"
          style={{ borderColor: color, background: color + '33' }}
        />
        {index < 999 && (
          <div className="w-px flex-1 bg-[var(--border)] mt-1" style={{ minHeight: 28 }} />
        )}
      </div>

      {/* content */}
      <div className="flex-1 pb-6 min-w-0">
        <div className="flex items-start justify-between gap-3">
          <Link
            href={`/projects/${project.id}`}
            className="group/link flex-1 min-w-0"
          >
            <p className="text-sm font-medium text-white group-hover/link:text-[var(--accent)] transition-colors truncate">
              {project.title}
            </p>
            <p className="text-xs text-[var(--muted)] mt-0.5 line-clamp-1">
              {project.problem_statement}
            </p>
            <div className="flex items-center gap-3 mt-2">
              <StatusBadge status={project.status} size="sm" />
              <span className="text-[10px] text-[var(--muted)]/60">
                {formatRelative(project.created_at)} · {formatDate(project.created_at)}
              </span>
            </div>
          </Link>

          {/* delete */}
          <div className="shrink-0">
            {!isConfirming ? (
              <button
                onClick={() => setConfirmId(project.id)}
                className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-[var(--muted)] hover:text-red-400 hover:bg-red-950/30 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            ) : (
              <div className="flex items-center gap-1.5 bg-[var(--elevated)] border border-red-900/50 rounded-lg px-2 py-1">
                <span className="text-[10px] text-red-400">Delete?</span>
                <button
                  onClick={() => onDelete(project.id)}
                  disabled={isDeleting}
                  className="text-[10px] text-white bg-red-700 hover:bg-red-600 px-1.5 py-0.5 rounded disabled:opacity-50"
                >
                  {isDeleting ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Yes'}
                </button>
                <button
                  onClick={() => setConfirmId(null)}
                  className="text-[10px] text-[var(--muted)] hover:text-white px-1 py-0.5"
                >
                  No
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

/* ── Page ─────────────────────────────────────────────────────────────────── */

export default function ProjectsPage() {
  const { user, loading: userLoading, login } = useUser()
  const [projects, setProjects]       = useState<Project[]>([])
  const [loading, setLoading]         = useState(true)
  const [refreshKey, setRefreshKey]   = useState(0)
  const [view, setView]               = useState<'grid' | 'history'>('grid')

  const [confirmId, setConfirmId]     = useState<string | null>(null)
  const [deleting, setDeleting]       = useState<string | null>(null)
  const [cleanConfirm, setCleanConfirm] = useState(false)
  const [cleaning, setCleaning]       = useState(false)

  useEffect(() => {
    if (!user) { setLoading(false); return }
    api.users.projects(user.id)
      .then(ps => setProjects(ps.sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )))
      .catch(() => toast.error('Failed to load projects'))
      .finally(() => setLoading(false))
  }, [user, refreshKey])

  async function handleDelete(id: string) {
    setDeleting(id)
    try {
      await api.projects.delete(id)
      setProjects(prev => prev.filter(p => p.id !== id))
      setConfirmId(null)
      toast.success('Project deleted')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Delete failed')
    } finally {
      setDeleting(null)
    }
  }

  async function handleCleanAll() {
    setCleaning(true)
    try {
      await Promise.all(projects.map(p => api.projects.delete(p.id)))
      setProjects([])
      setCleanConfirm(false)
      toast.success('All projects deleted')
    } catch {
      toast.error('Some projects could not be deleted')
      setRefreshKey(k => k + 1)
    } finally {
      setCleaning(false)
    }
  }

  if (userLoading) return null
  if (!user) return <UserGate login={login} onLogin={() => setRefreshKey(k => k + 1)} />

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between gap-4 flex-wrap"
      >
        <div>
          <h1 className="text-2xl font-bold text-white font-serif">Work History</h1>
          <p className="text-[var(--muted)] text-sm mt-1">
            {projects.length} {projects.length === 1 ? 'project' : 'projects'} · {user.name}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex items-center border border-[var(--border)] rounded-lg overflow-hidden">
            <button
              onClick={() => setView('grid')}
              className={`p-2 transition-colors ${view === 'grid' ? 'bg-[var(--elevated)] text-white' : 'text-[var(--muted)] hover:text-white'}`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setView('history')}
              className={`p-2 transition-colors ${view === 'history' ? 'bg-[var(--elevated)] text-white' : 'text-[var(--muted)] hover:text-white'}`}
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Clean history */}
          {projects.length > 0 && (
            !cleanConfirm ? (
              <button
                onClick={() => setCleanConfirm(true)}
                className="flex items-center gap-1.5 px-3 py-2 border border-red-800/40 text-red-500 text-xs rounded-lg hover:border-red-600 hover:bg-red-950/20 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Clean History
              </button>
            ) : (
              <div className="flex items-center gap-2 bg-[var(--elevated)] border border-red-900/50 rounded-lg px-3 py-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                <span className="text-[10px] text-red-400">Delete all {projects.length} projects?</span>
                <button
                  onClick={handleCleanAll}
                  disabled={cleaning}
                  className="flex items-center gap-1 text-[10px] bg-red-700 hover:bg-red-600 text-white px-2 py-1 rounded disabled:opacity-50"
                >
                  {cleaning ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                  Confirm
                </button>
                <button
                  onClick={() => setCleanConfirm(false)}
                  disabled={cleaning}
                  className="text-[10px] text-[var(--muted)] hover:text-white"
                >
                  Cancel
                </button>
              </div>
            )
          )}

          <Link
            href="/projects/new"
            className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
          >
            <Plus className="w-4 h-4" />
            New
          </Link>
        </div>
      </motion.div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-36 rounded-xl bg-[var(--surface)] border border-[var(--border)] animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-24 text-[var(--muted)]"
        >
          <Flame className="w-12 h-12 mb-4 opacity-20" />
          <p className="text-sm mb-6">No projects yet. Make your first move.</p>
          <Link
            href="/projects/new"
            className="px-6 py-2.5 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Create Your First Project
          </Link>
        </motion.div>
      ) : (
        <AnimatePresence mode="wait">
          {view === 'grid' ? (
            <motion.div
              key="grid"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            >
              <AnimatePresence>
                {projects.map((p, i) => (
                  <GridCard
                    key={p.id}
                    project={p}
                    index={i}
                    onDelete={handleDelete}
                    deleting={deleting}
                    confirmId={confirmId}
                    setConfirmId={setConfirmId}
                  />
                ))}
              </AnimatePresence>
            </motion.div>
          ) : (
            <motion.div
              key="history"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="max-w-2xl"
            >
              <AnimatePresence>
                {projects.map((p, i) => (
                  <HistoryRow
                    key={p.id}
                    project={p}
                    index={i}
                    onDelete={handleDelete}
                    deleting={deleting}
                    confirmId={confirmId}
                    setConfirmId={setConfirmId}
                  />
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  )
}
