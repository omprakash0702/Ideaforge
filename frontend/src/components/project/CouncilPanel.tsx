'use client'

import { motion } from 'framer-motion'
import { Lightbulb, BarChart2, Code2, TrendingUp, Wrench, AlertTriangle, Database } from 'lucide-react'
import type { Idea, EvaluationEdge } from '@/lib/api'

// ── Static agent definitions ──────────────────────────────────────────────────

const GENERATORS = [
  {
    type: 'CREATIVE',
    name: 'The Visionary',
    role: 'Creative Founder',
    tagline: 'Moonshot thinking. Category-creating concepts that defy convention.',
    Icon: Lightbulb,
    accent: '#A78BFA',
    border: 'border-violet-700/40',
    bg: 'bg-violet-950/30',
    pulse: '#7C3AED',
  },
  {
    type: 'MARKET',
    name: 'The Strategist',
    role: 'Market Founder',
    tagline: 'Market-first. Spots underserved niches and exploits timing advantages.',
    Icon: BarChart2,
    accent: '#FCD34D',
    border: 'border-amber-700/40',
    bg: 'bg-amber-950/30',
    pulse: '#D97706',
  },
  {
    type: 'BUILDER',
    name: 'The Architect',
    role: 'Builder Founder',
    tagline: 'Ships fast. Technical feasibility and engineering excellence first.',
    Icon: Code2,
    accent: '#34D399',
    border: 'border-emerald-700/40',
    bg: 'bg-emerald-950/30',
    pulse: '#059669',
  },
  {
    type: 'ANALYST',
    name: 'The Data Analyst',
    role: 'Analyst Founder',
    tagline: 'Evidence-driven. Builds from measurable pain points and unit economics.',
    Icon: Database,
    accent: '#FB923C',
    border: 'border-orange-700/40',
    bg: 'bg-orange-950/30',
    pulse: '#EA580C',
  },
] as const

const JUDGES = [
  {
    type: 'INVESTOR',
    name: 'The Venture Capitalist',
    focus: 'Market size · Revenue model · Scalability path · Return on investment',
    Icon: TrendingUp,
    criticality: 3,
    accent: '#FCD34D',
    border: 'border-amber-700/30',
    bg: 'bg-amber-950/20',
    critLabel: 'Pragmatic',
  },
  {
    type: 'ENGINEER',
    name: 'The Lead Engineer',
    focus: 'Technical feasibility · Architecture · Engineering debt · Build complexity',
    Icon: Wrench,
    criticality: 4,
    accent: '#60A5FA',
    border: 'border-blue-700/30',
    bg: 'bg-blue-950/20',
    critLabel: 'Rigorous',
  },
  {
    type: 'SKEPTIC',
    name: "The Devil's Advocate",
    focus: 'Hidden assumptions · Competitive threats · Execution risks · Blind spots',
    Icon: AlertTriangle,
    criticality: 5,
    accent: '#F87171',
    border: 'border-red-700/30',
    bg: 'bg-red-950/20',
    critLabel: 'Ruthless',
  },
] as const

// ── Sub-components ─────────────────────────────────────────────────────────────

function CriticalityBar({ level, accent }: { level: number; accent: string }) {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: 5 }, (_, i) => (
        <motion.div
          key={i}
          className="h-1.5 w-5 rounded-full"
          style={{ background: i < level ? accent : 'var(--border)' }}
          initial={{ scaleX: 0, opacity: 0 }}
          animate={{ scaleX: 1, opacity: 1 }}
          transition={{ duration: 0.25, delay: 0.6 + i * 0.07 }}
        />
      ))}
    </div>
  )
}

function PulsingDot({ color, delay = 0 }: { color: string; delay?: number }) {
  return (
    <motion.span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: color }}
      animate={{ opacity: [1, 0.15, 1], scale: [1, 1.4, 1] }}
      transition={{ duration: 1.4, repeat: Infinity, delay }}
    />
  )
}

function ScorePill({ score, accent }: { score: number; accent: string }) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.7 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="text-[11px] font-bold tabular-nums px-2 py-0.5 rounded-full border"
      style={{ color: accent, borderColor: `${accent}40`, background: `${accent}14` }}
    >
      avg {score.toFixed(1)}/10
    </motion.span>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

interface Props {
  ideas: Idea[]
  evaluationEdges: EvaluationEdge[]
  isRunning: boolean
}

export function CouncilPanel({ ideas, evaluationEdges, isRunning }: Props) {
  const countByGen = ideas.reduce<Record<string, number>>((acc, idea) => {
    if (idea.generator_type) acc[idea.generator_type] = (acc[idea.generator_type] ?? 0) + 1
    return acc
  }, {})

  // judge node id format: "{TYPE}_{project_uuid}" — extract type from prefix
  const scoreByJudge = evaluationEdges.reduce<Record<string, { total: number; n: number }>>(
    (acc, ev) => {
      const jtype = ev.source.split('_')[0]
      if (!acc[jtype]) acc[jtype] = { total: 0, n: 0 }
      acc[jtype].total += ev.score
      acc[jtype].n += 1
      return acc
    },
    {}
  )

  return (
    <div className="space-y-8">

      {/* ── Generator Agents ──────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--muted)]">
            Idea Generators
          </span>
          <div className="flex-1 h-px bg-[var(--border)]" />
          <span className="text-[10px] text-[var(--muted)]">The Founders</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {GENERATORS.map((g, i) => {
            const count = countByGen[g.type] ?? 0
            return (
              <motion.div
                key={g.type}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.12, ease: 'easeOut' }}
                className={`relative rounded-xl border p-4 flex flex-col gap-3 overflow-hidden ${g.bg} ${g.border}`}
              >
                {/* Background glow */}
                <motion.div
                  className="absolute inset-0 rounded-xl opacity-0"
                  style={{ background: `radial-gradient(circle at 50% 0%, ${g.accent}18, transparent 70%)` }}
                  animate={isRunning ? { opacity: [0, 1, 0] } : { opacity: 0.6 }}
                  transition={{ duration: 2, repeat: isRunning ? Infinity : 0, delay: i * 0.4 }}
                />

                <div className="relative flex items-start justify-between">
                  <motion.div
                    animate={isRunning
                      ? { rotate: [0, 8, -8, 0], scale: [1, 1.1, 1] }
                      : {}}
                    transition={{ duration: 2.5, repeat: Infinity, delay: i * 0.5 }}
                    className="p-2 rounded-lg"
                    style={{ background: `${g.accent}18` }}
                  >
                    <g.Icon className="w-4 h-4" style={{ color: g.accent }} />
                  </motion.div>

                  {count > 0 ? (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                      style={{ color: g.accent, background: `${g.accent}18` }}
                    >
                      {count} ideas
                    </motion.span>
                  ) : isRunning ? (
                    <PulsingDot color={g.pulse} delay={i * 0.3} />
                  ) : null}
                </div>

                <div className="relative">
                  <p className="text-xs font-semibold text-white">{g.name}</p>
                  <p className="text-[10px]" style={{ color: g.accent }}>{g.role}</p>
                </div>

                <p className="relative text-[10px] text-[var(--muted)] leading-relaxed">
                  {g.tagline}
                </p>

                {/* Animated bottom accent line */}
                <motion.div
                  className="absolute bottom-0 left-0 h-0.5 rounded-full"
                  style={{ background: g.accent }}
                  initial={{ width: 0 }}
                  animate={{ width: count > 0 ? '100%' : isRunning ? '40%' : '0%' }}
                  transition={{ duration: 0.8, delay: 0.4 + i * 0.1 }}
                />
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* ── Judge Council ─────────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--muted)]">
            The Council
          </span>
          <div className="flex-1 h-px bg-[var(--border)]" />
          <span className="text-[10px] text-[var(--muted)]">Judges · Criticality</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {JUDGES.map((j, i) => {
            const stats = scoreByJudge[j.type]
            const avg = stats ? stats.total / stats.n : null
            return (
              <motion.div
                key={j.type}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.35 + i * 0.12, ease: 'easeOut' }}
                className={`relative rounded-xl border p-4 flex flex-col gap-3 overflow-hidden ${j.bg} ${j.border}`}
              >
                {/* Background pulse when running */}
                {isRunning && (
                  <motion.div
                    className="absolute inset-0 rounded-xl"
                    style={{ background: `radial-gradient(circle at 50% 100%, ${j.accent}12, transparent 70%)` }}
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 2, repeat: Infinity, delay: i * 0.6 }}
                  />
                )}

                <div className="relative flex items-start justify-between">
                  <motion.div
                    animate={isRunning
                      ? { scale: [1, 1.15, 1], rotate: [0, -5, 5, 0] }
                      : {}}
                    transition={{ duration: 2, repeat: Infinity, delay: i * 0.5 }}
                    className="p-2 rounded-lg"
                    style={{ background: `${j.accent}18` }}
                  >
                    <j.Icon className="w-4 h-4" style={{ color: j.accent }} />
                  </motion.div>
                  {avg != null ? (
                    <ScorePill score={avg} accent={j.accent} />
                  ) : isRunning ? (
                    <PulsingDot color={j.accent} delay={i * 0.4} />
                  ) : null}
                </div>

                <div className="relative">
                  <p className="text-xs font-semibold text-white">{j.name}</p>
                  <p className="text-[10px] text-[var(--muted)] mt-0.5 leading-relaxed">{j.focus}</p>
                </div>

                <div className="relative space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] uppercase tracking-widest text-[var(--muted)]">
                      Criticality
                    </span>
                    <span
                      className="text-[9px] font-bold uppercase tracking-wide"
                      style={{ color: j.accent }}
                    >
                      {j.critLabel}
                    </span>
                  </div>
                  <CriticalityBar level={j.criticality} accent={j.accent} />
                </div>

                {/* Bottom accent */}
                <motion.div
                  className="absolute bottom-0 left-0 h-0.5 rounded-full"
                  style={{ background: j.accent }}
                  initial={{ width: 0 }}
                  animate={{ width: `${(j.criticality / 5) * 100}%` }}
                  transition={{ duration: 0.8, delay: 0.6 + i * 0.1 }}
                />
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
