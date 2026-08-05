'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Trophy, GitBranch, Cpu, Users, DollarSign, Star, Zap, Loader2, FlaskConical } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Idea, Evaluation } from '@/lib/api'

const FRONTIER_KEYWORDS = [
  "doesn't exist", "does not exist", "not yet invented", "not currently possible",
  "currently not possible", "requires breakthrough", "fundamental research",
  "decades away", "no proven", "no existing technology", "science fiction",
  "unsolved problem", "technically infeasible", "not technically feasible",
  "cannot be built", "not buildable", "requires agi", "general artificial intelligence",
]

function detectFrontier(evaluations: Evaluation[], ideaId: string): string | null {
  const engineerEvals = evaluations.filter(
    e => e.idea_id === ideaId && e.judge_type === 'ENGINEER',
  )
  for (const ev of engineerEvals) {
    for (const w of ev.weaknesses ?? []) {
      const lower = w.toLowerCase()
      if (FRONTIER_KEYWORDS.some(k => lower.includes(k))) {
        return w
      }
    }
  }
  return null
}

const generatorColors: Record<string, { badge: string; label: string }> = {
  CREATIVE: { badge: 'bg-violet-900/50 text-violet-300 border-violet-700',   label: 'Creative' },
  MARKET:   { badge: 'bg-amber-900/50 text-amber-300 border-amber-700',      label: 'Market'   },
  BUILDER:  { badge: 'bg-emerald-900/50 text-emerald-300 border-emerald-700', label: 'Builder' },
  ANALYST:  { badge: 'bg-sky-900/50 text-sky-300 border-sky-700',            label: 'Analyst'  },
  USER:     { badge: 'bg-pink-900/50 text-pink-300 border-pink-700',         label: 'Your Idea' },
}

function ScoreBar({ score }: { score: number }) {
  const pct = (score / 10) * 100
  const color = score >= 8 ? '#22C55E' : score >= 6 ? '#F59E0B' : '#EF4444'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-[var(--elevated)] rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
        />
      </div>
      <span className="text-xs font-bold tabular-nums" style={{ color }}>
        {score.toFixed(1)}
      </span>
    </div>
  )
}

interface Props {
  idea: Idea
  index: number
  evaluations?: Evaluation[]
  onEvolve?: () => Promise<Idea[]>
}

export function IdeaCard({ idea, index, evaluations, onEvolve }: Props) {
  const [evolving, setEvolving] = useState(false)
  const gen = idea.generator_type
    ? (generatorColors[idea.generator_type] ?? null)
    : generatorColors['USER']
  const frontierNote = evaluations ? detectFrontier(evaluations, idea.id) : null

  async function handleEvolve() {
    if (!onEvolve || evolving) return
    setEvolving(true)
    try { await onEvolve() } finally { setEvolving(false) }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
      className={cn(
        'relative rounded-xl border p-5 flex flex-col gap-4',
        'bg-[var(--surface)] border-[var(--border)]',
        'hover:border-[var(--accent)] transition-colors duration-300',
        idea.is_winner && 'border-yellow-500/60 bg-yellow-950/10',
      )}
    >
      {/* Winner crown */}
      {idea.is_winner && (
        <div className="absolute -top-3 left-4 flex items-center gap-1 bg-yellow-500 text-black px-2.5 py-0.5 rounded-full text-[11px] font-bold">
          <Trophy className="w-3 h-3" />
          Winner
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between gap-3 pt-1">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white text-sm leading-tight line-clamp-2">
            {idea.title}
          </h3>
          <div className="flex items-center gap-2 mt-1.5">
            {gen && (
              <span className={cn('text-[10px] px-2 py-0.5 rounded border font-medium', gen.badge)}>
                {gen.label}
              </span>
            )}
            {idea.version > 1 && (
              <span className="flex items-center gap-1 text-[10px] text-cyan-400 border border-cyan-800 bg-cyan-950/40 px-2 py-0.5 rounded">
                <GitBranch className="w-2.5 h-2.5" /> v{idea.version}
              </span>
            )}
          </div>
        </div>
        {idea.score != null && (
          <div className="flex items-center gap-1 shrink-0">
            <Star className="w-3 h-3 text-amber-400" />
            <span className="text-xs font-bold text-amber-300">{idea.score.toFixed(1)}</span>
          </div>
        )}
      </div>

      {/* Score bar */}
      {idea.score != null && <ScoreBar score={idea.score} />}

      {/* Sections */}
      <div className="space-y-2.5 text-xs text-[var(--muted)]">
        <Row icon={<Users className="w-3.5 h-3.5 shrink-0 text-violet-400 mt-0.5" />} label={idea.target_audience} />
        <Row icon={<DollarSign className="w-3.5 h-3.5 shrink-0 text-green-400 mt-0.5" />} label={idea.business_model} />
        <Row icon={<Cpu className="w-3.5 h-3.5 shrink-0 text-blue-400 mt-0.5" />} label={idea.tech_stack} />
      </div>

      {/* Key features */}
      {idea.key_features && idea.key_features.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1 border-t border-[var(--border)]">
          {idea.key_features.slice(0, 4).map((f, i) => (
            <span key={i} className="text-[10px] bg-[var(--elevated)] text-[var(--muted)] px-2 py-0.5 rounded">
              {f}
            </span>
          ))}
        </div>
      )}

      {/* Frontier badge */}
      {frontierNote && (
        <div className="flex items-start gap-2 rounded-lg border border-orange-700/50 bg-orange-950/20 px-3 py-2 text-[10px] text-orange-300 leading-relaxed">
          <FlaskConical className="w-3 h-3 shrink-0 mt-0.5 text-orange-400" />
          <div>
            <span className="font-bold text-orange-400 block mb-0.5">Frontier Challenge</span>
            Only viable if someone first solves: {frontierNote}
          </div>
        </div>
      )}

      {/* Evolve button */}
      {onEvolve && (
        <button
          onClick={handleEvolve}
          disabled={evolving}
          className={cn(
            'w-full flex items-center justify-center gap-2 py-2 rounded-lg border text-[11px] font-medium transition-all mt-1',
            evolving
              ? 'border-violet-700/40 bg-violet-950/20 text-violet-400 cursor-not-allowed'
              : 'border-violet-800/40 bg-violet-950/10 text-violet-400 hover:border-violet-600 hover:bg-violet-900/20 hover:text-violet-300',
          )}
        >
          {evolving
            ? <><Loader2 className="w-3 h-3 animate-spin" /> Evolving — judging 3 variants…</>
            : <><Zap className="w-3 h-3" /> Evolve This Idea</>
          }
        </button>
      )}
    </motion.div>
  )
}

function Row({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-start gap-2">
      {icon}
      <p className="line-clamp-2 leading-relaxed">{label}</p>
    </div>
  )
}
