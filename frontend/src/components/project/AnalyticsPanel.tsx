'use client'

import { useState, useContext, createContext } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Info, X } from 'lucide-react'
import type { Idea, IdeaGraphResponse, EvaluationEdge, Evaluation } from '@/lib/api'

interface Props {
  ideas: Idea[]
  graph: IdeaGraphResponse | null
  evaluations?: Evaluation[]
}

// ── Info bubble system ────────────────────────────────────────────────────────

type BubbleData = { title: string; body: string; example?: string }

const InfoCtx = createContext<(d: BubbleData) => void>(() => {})

const BUBBLES: Record<string, BubbleData> = {
  'Total Ideas': {
    title: 'Total Ideas',
    body: 'The full count of startup concepts your AI Council created — both original ideas (v1) and improved evolved versions (v2). More ideas means more angles on your problem, not just more noise.',
    example: '8 originals + 5 evolved = 13 total. Evolved ones are rewrites that address specific weaknesses.',
  },
  'Winner Score': {
    title: 'Winner Score',
    body: 'The average score (out of 10) the winning idea received from all three judges: Investor, Engineer, and Skeptic. A 7+ means the idea genuinely impressed the council. Below 6 even for the winner means the whole pool has fundamental problems.',
    example: 'Investor: 8.0 + Engineer: 7.5 + Skeptic: 5.5 = avg 7.0/10 — winner.',
  },
  'Pool Average': {
    title: 'Pool Average',
    body: 'The average quality score across every idea in the pool. Compare this to the winner\'s score. A big gap (winner 7.5, pool avg 4.8) means the winner was exceptional. A small gap means the whole pool was competitive — a healthy sign.',
    example: 'Pool avg 5.8 vs winner 7.0 = good gap. Pool avg 6.9 vs winner 7.0 = very tight race.',
  },
  'Evolution Lift': {
    title: 'Evolution Lift',
    body: 'How much better evolved (v2) ideas scored compared to the originals (v1). Positive = evolution worked — the AI listened to judge criticism and rebuilt the ideas. This is the core loop: generate → judge → evolve → repeat.',
    example: '+1.8 lift: ideas went from avg 5.1 → 6.9 after judges called out their flaws.',
  },
  'Score Leaderboard': {
    title: 'Score Leaderboard',
    body: 'All ideas ranked from best to worst by their average judge score. Bar color shows quality: green (8+) = strong investment case, yellow (6–8) = interesting but needs work, red (<6) = fundamental issues. The tiny colored dot shows which AI generator created it.',
  },
  'Score Distribution': {
    title: 'Score Distribution',
    body: 'A histogram bucketing all ideas by score range. In a healthy run, most bars are in the 5–8 zone with a few standouts at 8+. If most bars are below 5, the judges found the ideas fundamentally weak for this market — consider refining your problem statement.',
  },
  'Generator Performance': {
    title: 'Generator Performance',
    body: 'How each AI founder agent performed on average. Visionary = bold disruptive ideas. Strategist = market-first thinking. Architect = technical feasibility. Data Analyst = evidence-driven unit economics. The thick bar = average. The thin line below = min-to-max range across that agent\'s ideas.',
    example: 'Architect avg 7.2, range 4.5–9.0 = high variance. Strategist avg 6.1, range 5.8–6.4 = consistent.',
  },
  'Judge Score Matrix': {
    title: 'Judge Score Matrix',
    body: 'A grid showing exactly what score each judge gave to every idea. Green = liked it, red = rejected it. Look for rows where one judge gives 9 but another gives 3 — those are controversial ideas with strong upside AND serious hidden risk. The "Avg" column is the composite score used for ranking.',
    example: 'Investor: 9.0, Engineer: 8.5, Skeptic: 3.0 → the Skeptic saw a fatal flaw the others missed.',
  },
  'Generator × Judge Breakdown': {
    title: 'Generator × Judge Breakdown',
    body: 'Shows which AI generator\'s ideas each specific judge tends to rate higher. If the Investor consistently prefers Market-focused ideas, this market rewards business-model thinking over technical novelty. Use this insight to bias your next run.',
  },
  'Judge Disagreement': {
    title: 'Judge Disagreement',
    body: 'Ranks ideas by how much the three judges disagreed. Wide spread = polarising idea — one judge sees a unicorn, another sees a disaster. These are the MOST interesting ideas: high risk, high reward. Tight spread = consensus, safer bet but lower ceiling.',
    example: '±4.5 spread: Investor gave 9.5, Skeptic gave 5.0 — the idea is risky but has real upside.',
  },
  'Market Competitors': {
    title: 'Market Competitors',
    body: 'Real companies the AI identified as competing in this space. Frequently mentioned names = well-understood market. Diverse, spread-out competitors = fragmented market = potential for disruption. One dominant name appearing everywhere = strong incumbent you must out-position.',
  },
  'Evolution Impact': {
    title: 'Evolution Impact',
    body: 'For each evolved (v2) idea, shows the score before and after the AI rewrote it based on judge criticism. A big green jump means the judges\' feedback was specific and actionable. This is "the offer the market cannot refuse" — iterative refinement until the council says yes.',
    example: 'v1: 5.2 → v2: 7.8 (+2.6): Skeptic\'s weak-moat critique was fixed with a network-effect lock-in.',
  },
}

function InfoBubble({ data, onClose }: { data: BubbleData | null; onClose: () => void }) {
  return (
    <AnimatePresence>
      {data && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 14 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 8 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="relative z-10 w-full max-w-sm rounded-2xl border border-[var(--accent)]/30 bg-[var(--surface)] p-6 shadow-2xl"
            style={{ boxShadow: '0 0 60px rgba(124,92,252,0.15), 0 24px 48px rgba(0,0,0,0.4)' }}
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-[var(--muted)] hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-xl bg-[var(--accent)]/15 border border-[var(--accent)]/30 flex items-center justify-center shrink-0">
                <Info className="w-3.5 h-3.5 text-[var(--accent)]" />
              </div>
              <h3 className="font-semibold text-white text-sm leading-tight">{data.title}</h3>
            </div>
            <p className="text-[var(--muted)] text-sm leading-relaxed">{data.body}</p>
            {data.example && (
              <div className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--elevated)] p-3">
                <p className="text-[9px] font-bold uppercase tracking-widest text-[var(--accent)] mb-1.5">Example</p>
                <p className="text-[11px] text-[var(--muted)] leading-relaxed font-mono">{data.example}</p>
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}

// ── Utilities ──────────────────────────────────────────────────────────────────

function sc(score: number | null) {
  if (score == null) return '#6B7280'
  if (score >= 8)    return '#22C55E'
  if (score >= 6)    return '#F59E0B'
  return '#EF4444'
}

function avg(nums: number[]) {
  return nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : 0
}

const GEN_COLORS: Record<string, string> = {
  CREATIVE: '#A78BFA',
  MARKET:   '#FCD34D',
  BUILDER:  '#34D399',
  ANALYST:  '#FB923C',
}

const GEN_LABELS: Record<string, string> = {
  CREATIVE: 'Visionary',
  MARKET:   'Strategist',
  BUILDER:  'Architect',
  ANALYST:  'Data Analyst',
}

const JUDGE_COLORS: Record<string, string> = {
  INVESTOR: '#FCD34D',
  ENGINEER: '#60A5FA',
  SKEPTIC:  '#F87171',
}

const JUDGE_LABELS: Record<string, string> = {
  INVESTOR: 'Investor',
  ENGINEER: 'Engineer',
  SKEPTIC:  'Skeptic',
}

// Compute avg judge score for an idea from evaluation edges
function ideaAvgScore(ideaId: string, edges: EvaluationEdge[]) {
  const scores = edges.filter(e => e.target === ideaId).map(e => e.score)
  return scores.length ? avg(scores) : null
}

// ── Section header ─────────────────────────────────────────────────────────────

function SH({ title, sub, infoId }: { title: string; sub?: string; infoId?: string }) {
  const showBubble = useContext(InfoCtx)
  return (
    <div className="mb-4 flex items-start gap-2 justify-between">
      <div className="min-w-0">
        <h3 className="text-sm font-semibold text-white">{title}</h3>
        {sub && <p className="text-[10px] text-[var(--muted)] mt-0.5">{sub}</p>}
      </div>
      {infoId && (
        <button
          onClick={() => { const d = BUBBLES[infoId]; if (d) showBubble(d) }}
          className="shrink-0 w-5 h-5 rounded-full border border-[var(--border)] text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--accent)] transition-colors flex items-center justify-center mt-0.5"
          title={`What is ${infoId}?`}
        >
          <Info className="w-2.5 h-2.5" />
        </button>
      )}
    </div>
  )
}

// ── 1. Metrics row ─────────────────────────────────────────────────────────────

function MetricsRow({ ideas, evEdges }: { ideas: Idea[]; evEdges: EvaluationEdge[] }) {
  const showBubble = useContext(InfoCtx)
  const winner       = ideas.find(i => i.is_winner)
  const v1           = ideas.filter(i => i.version === 1)
  const v2           = ideas.filter(i => i.version > 1)
  const allScores    = ideas.map(i => ideaAvgScore(i.id, evEdges) ?? i.score ?? 0).filter(s => s > 0)
  const poolAvg      = avg(allScores)
  const v1Scores     = v1.map(i => ideaAvgScore(i.id, evEdges) ?? i.score ?? 0).filter(s => s > 0)
  const v2Scores     = v2.map(i => ideaAvgScore(i.id, evEdges) ?? i.score ?? 0).filter(s => s > 0)
  const evoLift      = avg(v2Scores) - avg(v1Scores)
  const winnerScore  = winner ? (ideaAvgScore(winner.id, evEdges) ?? winner.score) : null

  const cards = [
    {
      icon: '💡', label: 'Total Ideas',
      value: ideas.length.toString(),
      sub: `${v1.length} original · ${v2.length} evolved`,
    },
    {
      icon: '🏆', label: 'Winner Score',
      value: winnerScore != null ? `${winnerScore.toFixed(2)}/10` : '—',
      sub: winner?.title?.slice(0, 28) ?? '',
      valueColor: winnerScore != null ? sc(winnerScore) : undefined,
    },
    {
      icon: '📊', label: 'Pool Average',
      value: poolAvg > 0 ? poolAvg.toFixed(2) : '—',
      sub: `across ${allScores.length} scored ideas`,
      valueColor: poolAvg > 0 ? sc(poolAvg) : undefined,
    },
    {
      icon: '🧬', label: 'Evolution Lift',
      value: v2Scores.length ? `${evoLift >= 0 ? '+' : ''}${evoLift.toFixed(2)}` : '—',
      sub: v2Scores.length ? `v1 avg ${avg(v1Scores).toFixed(1)} → v2 avg ${avg(v2Scores).toFixed(1)}` : 'no evolutions yet',
      valueColor: evoLift > 0 ? '#22C55E' : evoLift < 0 ? '#EF4444' : undefined,
    },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {cards.map((c, i) => (
        <motion.div
          key={c.label}
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: i * 0.08 }}
          onClick={() => { const d = BUBBLES[c.label]; if (d) showBubble(d) }}
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 cursor-pointer hover:border-[var(--accent)]/40 transition-colors group relative"
        >
          <Info className="absolute top-3 right-3 w-3 h-3 text-[var(--border)] group-hover:text-[var(--accent)] transition-colors" />
          <div className="text-xl mb-1.5">{c.icon}</div>
          <div className="text-xl font-bold tabular-nums" style={{ color: c.valueColor ?? 'white' }}>
            {c.value}
          </div>
          <div className="text-[10px] font-medium text-[var(--muted)] mt-0.5">{c.label}</div>
          {c.sub && <div className="text-[9px] text-[var(--border)] mt-1 truncate">{c.sub}</div>}
        </motion.div>
      ))}
    </div>
  )
}

// ── 2. Score Leaderboard ───────────────────────────────────────────────────────

function ScoreLeaderboard({ ideas, evEdges }: { ideas: Idea[]; evEdges: EvaluationEdge[] }) {
  const sorted = [...ideas]
    .map(i => ({ idea: i, score: ideaAvgScore(i.id, evEdges) ?? i.score ?? 0 }))
    .sort((a, b) => b.score - a.score)

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <SH title="Score Leaderboard" sub="All ideas ranked by aggregate judge score" infoId="Score Leaderboard" />
      <div className="space-y-2.5">
        {sorted.map(({ idea, score }, i) => {
          const color    = sc(score)
          const genColor = idea.generator_type ? GEN_COLORS[idea.generator_type] : '#6B7280'
          return (
            <motion.div
              key={idea.id}
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35, delay: i * 0.04 }}
              className="flex items-center gap-3"
            >
              <span className="text-[10px] tabular-nums text-[var(--muted)] w-5 text-right shrink-0">
                #{i + 1}
              </span>
              <div className="w-40 shrink-0">
                <p className="text-[10px] text-white truncate leading-tight">{idea.title}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-sm shrink-0" style={{ background: genColor }} />
                  <span className="text-[8px] text-[var(--muted)]">
                    {idea.version > 1 ? 'v2 · ' : ''}
                    {idea.generator_type ? (GEN_LABELS[idea.generator_type] ?? idea.generator_type) : 'Your Idea'}
                  </span>
                  {idea.is_winner && <span className="ml-0.5 text-[9px]">🏆</span>}
                </div>
              </div>
              <div className="flex-1 relative h-6 bg-[var(--elevated)] rounded overflow-hidden">
                <motion.div
                  className="absolute inset-y-0 left-0 rounded"
                  style={{ background: color + 'cc' }}
                  initial={{ width: 0 }}
                  animate={{ width: `${(score / 10) * 100}%` }}
                  transition={{ duration: 0.75, delay: 0.05 + i * 0.03, ease: 'easeOut' }}
                />
                <span className="absolute inset-0 flex items-center px-2 text-[9px] font-bold text-white">
                  {score.toFixed(2)}/10
                </span>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

// ── 3. Score Distribution Histogram ───────────────────────────────────────────

function ScoreDistribution({ ideas, evEdges }: { ideas: Idea[]; evEdges: EvaluationEdge[] }) {
  const buckets = [
    { label: '0–4', min: 0,  max: 4,     color: '#EF4444' },
    { label: '4–5', min: 4,  max: 5,     color: '#F97316' },
    { label: '5–6', min: 5,  max: 6,     color: '#EAB308' },
    { label: '6–7', min: 6,  max: 7,     color: '#F59E0B' },
    { label: '7–8', min: 7,  max: 8,     color: '#84CC16' },
    { label: '8–9', min: 8,  max: 9,     color: '#22C55E' },
    { label: '9–10', min: 9, max: 10.01, color: '#10B981' },
  ]

  const scored = ideas.map(i => ideaAvgScore(i.id, evEdges) ?? i.score ?? 0).filter(s => s > 0)
  const counts = buckets.map(b => ({
    ...b,
    count: scored.filter(s => s >= b.min && s < b.max).length,
  }))
  const maxCount = Math.max(...counts.map(c => c.count), 1)

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <SH title="Score Distribution" sub="Histogram of ideas by score range" infoId="Score Distribution" />
      <div className="flex items-end gap-1.5" style={{ height: 120 }}>
        {counts.map((b, i) => {
          const barH = Math.round((b.count / maxCount) * 88)
          return (
            <div key={b.label} className="flex-1 flex flex-col items-center gap-1">
              <span className="text-[9px] font-bold text-white tabular-nums" style={{ minHeight: 14 }}>
                {b.count > 0 ? b.count : ''}
              </span>
              <div className="w-full rounded-t flex items-end" style={{ height: 88, background: 'var(--elevated)' }}>
                <motion.div
                  className="w-full rounded-t"
                  style={{ background: b.color }}
                  initial={{ height: 0 }}
                  animate={{ height: barH }}
                  transition={{ duration: 0.7, delay: i * 0.06, ease: 'easeOut' }}
                />
              </div>
              <span className="text-[8px] text-[var(--muted)] text-center leading-tight">{b.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── 4. Generator Performance ───────────────────────────────────────────────────

function GeneratorPerformance({ ideas, evEdges }: { ideas: Idea[]; evEdges: EvaluationEdge[] }) {
  const genTypes = ['CREATIVE', 'MARKET', 'BUILDER', 'ANALYST']
  const stats = genTypes.map(gt => {
    const genIdeas = ideas.filter(i => i.generator_type === gt)
    const scores   = genIdeas.map(i => ideaAvgScore(i.id, evEdges) ?? i.score ?? 0).filter(s => s > 0)
    return {
      gt,
      count: genIdeas.length,
      hasWinner: genIdeas.some(i => i.is_winner),
      avgScore: avg(scores),
      maxScore: scores.length ? Math.max(...scores) : 0,
      minScore: scores.length ? Math.min(...scores) : 0,
    }
  }).filter(s => s.count > 0)

  if (stats.length === 0) return null

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <SH title="Generator Performance" sub="Average score breakdown per AI founder agent" infoId="Generator Performance" />
      <div className="space-y-4">
        {stats.map((s, i) => {
          const color = GEN_COLORS[s.gt]
          return (
            <motion.div
              key={s.gt}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-sm" style={{ background: color }} />
                  <span className="text-[11px] font-medium text-white">{GEN_LABELS[s.gt]}</span>
                  <span className="text-[9px] text-[var(--muted)]">{s.count} idea{s.count > 1 ? 's' : ''}</span>
                  {s.hasWinner && <span className="text-[10px]">🏆</span>}
                </div>
                <div className="flex items-center gap-3 text-[10px] tabular-nums text-[var(--muted)]">
                  <span>min {s.minScore.toFixed(1)}</span>
                  <span>max {s.maxScore.toFixed(1)}</span>
                  <span className="font-bold" style={{ color }}>avg {s.avgScore.toFixed(2)}</span>
                </div>
              </div>
              {/* Avg bar */}
              <div className="h-4 bg-[var(--elevated)] rounded overflow-hidden">
                <motion.div
                  className="h-full rounded"
                  style={{ background: color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${(s.avgScore / 10) * 100}%` }}
                  transition={{ duration: 0.85, delay: 0.15 + i * 0.1, ease: 'easeOut' }}
                />
              </div>
              {/* Range bar (min to max) */}
              <div className="relative h-1.5 bg-[var(--elevated)] rounded overflow-hidden">
                <motion.div
                  className="absolute h-full rounded opacity-40"
                  style={{
                    background: color,
                    left: `${(s.minScore / 10) * 100}%`,
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${((s.maxScore - s.minScore) / 10) * 100}%` }}
                  transition={{ duration: 0.7, delay: 0.25 + i * 0.1 }}
                />
              </div>
              <p className="text-[8px] text-[var(--border)]">range bar: min → max</p>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

// ── 5. Judge Score Matrix ──────────────────────────────────────────────────────

function JudgeMatrix({ ideas, evEdges }: { ideas: Idea[]; evEdges: EvaluationEdge[] }) {
  const judges  = ['INVESTOR', 'ENGINEER', 'SKEPTIC']
  const sorted  = [...ideas]
    .map(i => ({ idea: i, score: ideaAvgScore(i.id, evEdges) ?? i.score ?? 0 }))
    .sort((a, b) => b.score - a.score)

  const scoreFor = (ideaId: string, judge: string) => {
    const ev = evEdges.find(e => e.target === ideaId && e.source.startsWith(judge + '_'))
    return ev?.score ?? null
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <SH title="Judge Score Matrix" sub="Per-judge scores for every idea — color intensity = score quality" infoId="Judge Score Matrix" />
      <div className="overflow-x-auto">
        <table className="w-full text-[10px] border-collapse">
          <thead>
            <tr>
              <th className="text-left text-[var(--muted)] pb-3 pr-4 font-medium w-44">Idea</th>
              {judges.map(j => (
                <th key={j} className="text-center pb-3 px-3 font-semibold" style={{ color: JUDGE_COLORS[j] }}>
                  {JUDGE_LABELS[j]}
                </th>
              ))}
              <th className="text-center pb-3 px-3 font-medium text-[var(--muted)]">Avg</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(({ idea, score }, ri) => {
              const judgeScores = judges.map(j => scoreFor(idea.id, j))
              const valid = judgeScores.filter(s => s != null) as number[]
              const rowAvg = valid.length ? avg(valid) : null
              return (
                <motion.tr
                  key={idea.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: ri * 0.04 }}
                  className="border-t border-[var(--border)]"
                >
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-1.5">
                      {idea.generator_type && (
                        <span className="w-1.5 h-1.5 rounded-sm shrink-0" style={{ background: GEN_COLORS[idea.generator_type] }} />
                      )}
                      <span className="text-white truncate max-w-[130px]">{idea.title}</span>
                      {idea.is_winner && <span className="ml-0.5">🏆</span>}
                    </div>
                    <div className="text-[8px] text-[var(--muted)] mt-0.5 pl-3">
                      {idea.version > 1 ? 'v2 evolved · ' : ''}{idea.generator_type ? GEN_LABELS[idea.generator_type] ?? idea.generator_type : ''}
                    </div>
                  </td>
                  {judgeScores.map((s, ji) => (
                    <td key={ji} className="py-2.5 px-3 text-center">
                      {s != null ? (
                        <motion.div
                          className="inline-flex items-center justify-center w-11 h-7 rounded text-[9px] font-bold tabular-nums mx-auto"
                          style={{
                            background: sc(s) + '28',
                            color: sc(s),
                            border: `1px solid ${sc(s)}45`,
                          }}
                          initial={{ scale: 0.5, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          transition={{ delay: 0.15 + ri * 0.03 + ji * 0.02 }}
                        >
                          {s.toFixed(1)}
                        </motion.div>
                      ) : (
                        <span className="text-[var(--border)]">—</span>
                      )}
                    </td>
                  ))}
                  <td className="py-2.5 px-3 text-center">
                    {rowAvg != null ? (
                      <span className="font-bold tabular-nums" style={{ color: sc(rowAvg) }}>
                        {rowAvg.toFixed(2)}
                      </span>
                    ) : '—'}
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── 6. Evolution Impact ────────────────────────────────────────────────────────

function EvolutionImpact({ ideas, evEdges }: { ideas: Idea[]; evEdges: EvaluationEdge[] }) {
  const evolved = ideas
    .filter(i => i.version > 1 && i.parent_idea_id)
    .map(i => {
      const parent    = ideas.find(p => p.id === i.parent_idea_id)
      const scoreBefore = ideaAvgScore(i.parent_idea_id!, evEdges) ?? parent?.score ?? 0
      const scoreAfter  = ideaAvgScore(i.id, evEdges) ?? i.score ?? 0
      return { idea: i, parent, scoreBefore, scoreAfter, delta: scoreAfter - scoreBefore }
    })
    .sort((a, b) => b.delta - a.delta)

  if (evolved.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <SH title="Evolution Impact" sub="Score gains from AI-driven evolution" infoId="Evolution Impact" />
        <p className="text-[var(--muted)] text-xs">No evolved ideas yet.</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <SH title="Evolution Impact" sub="v1 → v2 score delta per evolved idea (sorted by improvement)" infoId="Evolution Impact" />
      <div className="space-y-3">
        {evolved.map(({ idea, scoreBefore, scoreAfter, delta }, i) => {
          const genColor = idea.generator_type ? GEN_COLORS[idea.generator_type] : '#6B7280'
          return (
            <motion.div
              key={idea.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.07 }}
              className="rounded-lg border border-[var(--border)] bg-[var(--elevated)] p-3"
            >
              <div className="flex items-start justify-between mb-2.5">
                <div className="min-w-0 flex-1">
                  <p className="text-[11px] font-semibold text-white truncate">{idea.title}</p>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-sm" style={{ background: genColor }} />
                    <span className="text-[9px] text-[var(--muted)]">
                      {GEN_LABELS[idea.generator_type!] ?? idea.generator_type}
                    </span>
                    {idea.is_winner && <span className="text-[9px]">🏆</span>}
                  </div>
                </div>
                <motion.div
                  className="text-right shrink-0 ml-3 px-2 py-1 rounded-lg"
                  style={{
                    background: delta >= 0 ? '#22C55E18' : '#EF444418',
                    border: `1px solid ${delta >= 0 ? '#22C55E40' : '#EF444440'}`,
                  }}
                  initial={{ scale: 0.7 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2 + i * 0.07 }}
                >
                  <span
                    className="text-[13px] font-bold tabular-nums block"
                    style={{ color: delta >= 0 ? '#22C55E' : '#EF4444' }}
                  >
                    {delta >= 0 ? '+' : ''}{delta.toFixed(2)}
                  </span>
                  <span className="text-[8px] text-[var(--muted)]">pts gained</span>
                </motion.div>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[8px] text-[var(--muted)] w-12 shrink-0">v1 Before</span>
                  <div className="flex-1 h-2.5 bg-[var(--surface)] rounded overflow-hidden">
                    <motion.div
                      className="h-full rounded"
                      style={{ background: sc(scoreBefore) + 'aa' }}
                      initial={{ width: 0 }}
                      animate={{ width: `${(scoreBefore / 10) * 100}%` }}
                      transition={{ duration: 0.7, delay: 0.1 + i * 0.06 }}
                    />
                  </div>
                  <span className="text-[9px] tabular-nums w-7 text-right" style={{ color: sc(scoreBefore) }}>
                    {scoreBefore.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[8px] text-emerald-400 w-12 shrink-0">v2 After</span>
                  <div className="flex-1 h-2.5 bg-[var(--surface)] rounded overflow-hidden">
                    <motion.div
                      className="h-full rounded"
                      style={{ background: sc(scoreAfter) }}
                      initial={{ width: 0 }}
                      animate={{ width: `${(scoreAfter / 10) * 100}%` }}
                      transition={{ duration: 0.7, delay: 0.25 + i * 0.06 }}
                    />
                  </div>
                  <span className="text-[9px] tabular-nums w-7 text-right" style={{ color: sc(scoreAfter) }}>
                    {scoreAfter.toFixed(1)}
                  </span>
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

// ── 7. Judge Disagreement dot-plot ─────────────────────────────────────────────

function JudgeDisagreement({ ideas, evEdges }: { ideas: Idea[]; evEdges: EvaluationEdge[] }) {
  const judges  = ['INVESTOR', 'ENGINEER', 'SKEPTIC']

  const rows = ideas
    .map(idea => {
      const scores = judges.map(j => {
        const ev = evEdges.find(e => e.target === idea.id && e.source.startsWith(j + '_'))
        return { judge: j, score: ev?.score ?? null }
      }).filter(s => s.score != null) as { judge: string; score: number }[]
      if (scores.length < 2) return null
      const vals   = scores.map(s => s.score)
      const spread = Math.max(...vals) - Math.min(...vals)
      return { idea, scores, spread }
    })
    .filter(Boolean)
    .sort((a, b) => b!.spread - a!.spread)
    .slice(0, 6)

  if (rows.length === 0) return null

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <SH title="Judge Disagreement" sub="Ideas where judges diverged most — each dot is one judge's score" infoId="Judge Disagreement" />
      <div className="space-y-5">
        {rows.map((row, i) => (
          <motion.div
            key={row!.idea.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07 }}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] text-white truncate max-w-[220px]">{row!.idea.title}</span>
              <span className="text-[9px] tabular-nums text-amber-400 ml-2 shrink-0">
                ±{row!.spread.toFixed(1)} spread
              </span>
            </div>
            {/* Dot plot track */}
            <div className="relative" style={{ height: 28 }}>
              {/* Track */}
              <div
                className="absolute top-1/2 left-0 right-0 h-px"
                style={{ background: 'var(--border)', transform: 'translateY(-50%)' }}
              />
              {/* Scale ticks */}
              {[0, 2, 4, 6, 8, 10].map(v => (
                <div
                  key={v}
                  className="absolute"
                  style={{ left: `${v * 10}%`, top: '50%', transform: 'translate(-50%, -50%)' }}
                >
                  <div className="w-px h-2 bg-[var(--border)] opacity-50" />
                </div>
              ))}
              {/* Judge dots */}
              {row!.scores.map(({ judge, score }) => {
                const color = JUDGE_COLORS[judge]
                return (
                  <motion.div
                    key={judge}
                    className="absolute w-3.5 h-3.5 rounded-full border-2 border-[var(--surface)]"
                    style={{
                      left: `${(score / 10) * 100}%`,
                      top: '50%',
                      transform: 'translate(-50%, -50%)',
                      background: color,
                      zIndex: 1,
                    }}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.25 + i * 0.07, type: 'spring', stiffness: 300 }}
                    title={`${JUDGE_LABELS[judge]}: ${score.toFixed(1)}`}
                  />
                )
              })}
            </div>
            {/* Scale labels */}
            <div className="flex justify-between text-[7px] text-[var(--border)] mt-0.5 px-0">
              {[0, 2, 4, 6, 8, 10].map(v => (
                <span key={v} style={{ width: 14, textAlign: 'center' }}>{v}</span>
              ))}
            </div>
          </motion.div>
        ))}

        {/* Legend */}
        <div className="flex items-center gap-4 pt-1 border-t border-[var(--border)] text-[9px] text-[var(--muted)]">
          {Object.entries(JUDGE_LABELS).map(([k, v]) => (
            <span key={k} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: JUDGE_COLORS[k] }} />
              {v}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── 8. Market Competitors ─────────────────────────────────────────────────────

function MarketCompetitors({ ideas }: { ideas: Idea[] }) {
  const ideasWithComp = ideas.filter(i => i.competitors && i.competitors.length > 0)

  if (ideasWithComp.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <SH title="Market Competitors" sub="Competitive landscape per idea" infoId="Market Competitors" />
        <p className="text-[var(--muted)] text-xs">No competitor data yet.</p>
      </div>
    )
  }

  // Frequency map — split on " — " to extract just the company name
  const freq = new Map<string, number>()
  for (const idea of ideasWithComp) {
    for (const c of idea.competitors ?? []) {
      const name = c.split(' — ')[0].split(' – ')[0].trim()
      if (name) freq.set(name, (freq.get(name) ?? 0) + 1)
    }
  }
  const topCompetitors = [...freq.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12)

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 space-y-6">
      <SH title="Market Competitors" sub="Real companies competing in this space, identified per idea by the AI agents" infoId="Market Competitors" />

      {/* ── Landscape heat strip ────────────────────────────────────────── */}
      <div>
        <p className="text-[9px] font-bold uppercase tracking-widest text-[var(--muted)] mb-2">
          Most-mentioned competitors
        </p>
        <div className="flex flex-wrap gap-2">
          {topCompetitors.map(([name, count], i) => {
            const intensity = count / (topCompetitors[0]?.[1] ?? 1)
            return (
              <motion.span
                key={name}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium border"
                style={{
                  background: `rgba(124,92,252,${0.07 + intensity * 0.18})`,
                  borderColor: `rgba(124,92,252,${0.2 + intensity * 0.4})`,
                  color: count > 1 ? 'var(--accent)' : 'var(--muted)',
                }}
              >
                {name}
                {count > 1 && (
                  <span
                    className="text-[8px] font-bold px-1 rounded-full"
                    style={{ background: 'rgba(124,92,252,0.25)', color: 'var(--accent)' }}
                  >
                    ×{count}
                  </span>
                )}
              </motion.span>
            )
          })}
        </div>
      </div>

      {/* ── Per-idea competitor lists ────────────────────────────────────── */}
      <div>
        <p className="text-[9px] font-bold uppercase tracking-widest text-[var(--muted)] mb-3">
          Competitive landscape per idea
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {ideasWithComp.map((idea, ci) => {
            const genColor = idea.generator_type ? GEN_COLORS[idea.generator_type] : '#6B7280'
            return (
              <motion.div
                key={idea.id}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: ci * 0.06 }}
                className="rounded-xl border p-4 space-y-3"
                style={{ borderColor: genColor + '30', background: genColor + '08' }}
              >
                {/* Idea header */}
                <div className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-sm shrink-0 mt-1.5" style={{ background: genColor }} />
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold text-white truncate leading-tight">
                      {idea.title}
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-[9px]" style={{ color: genColor }}>
                        {GEN_LABELS[idea.generator_type!] ?? idea.generator_type ?? 'Unknown'}
                      </span>
                      {idea.version > 1 && (
                        <span className="text-[8px] text-cyan-400">· v2</span>
                      )}
                      {idea.is_winner && <span className="text-[9px]">🏆</span>}
                    </div>
                  </div>
                </div>

                {/* Competitor list */}
                <ul className="space-y-1.5">
                  {(idea.competitors ?? []).map((comp, i) => {
                    const dashIdx = comp.indexOf(' — ')
                    const altDashIdx = comp.indexOf(' – ')
                    const splitAt = dashIdx !== -1 ? dashIdx : altDashIdx !== -1 ? altDashIdx : -1
                    const compName = splitAt !== -1 ? comp.slice(0, splitAt).trim() : comp.trim()
                    const compDesc = splitAt !== -1 ? comp.slice(splitAt + 3).trim() : ''
                    return (
                      <motion.li
                        key={i}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.25, delay: ci * 0.06 + i * 0.04 }}
                        className="flex items-start gap-2 text-[10px]"
                      >
                        <span className="text-[var(--muted)] mt-0.5 shrink-0">▸</span>
                        <span>
                          <span className="font-semibold text-white">{compName}</span>
                          {compDesc && (
                            <span className="text-[var(--muted)]"> — {compDesc}</span>
                          )}
                        </span>
                      </motion.li>
                    )
                  })}
                </ul>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── 9. Generator × Judge cross-table ─────────────────────────────────────────

function GeneratorComparison({ ideas, evEdges }: { ideas: Idea[]; evEdges: EvaluationEdge[] }) {
  const judges  = ['INVESTOR', 'ENGINEER', 'SKEPTIC']
  const genTypes = ['CREATIVE', 'MARKET', 'BUILDER', 'ANALYST']

  // For each generator × judge pair: avg score
  const data = genTypes.map(gt => {
    const genIdeas = ideas.filter(i => i.generator_type === gt)
    const judgeAvgs = judges.map(j => {
      const scores = genIdeas
        .map(i => evEdges.find(e => e.target === i.id && e.source.startsWith(j + '_'))?.score)
        .filter(s => s != null) as number[]
      return { judge: j, avg: avg(scores) }
    })
    return { gt, judgeAvgs, count: genIdeas.length }
  }).filter(g => g.count > 0)

  if (data.length === 0) return null

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <SH title="Generator × Judge Breakdown" sub="Average score each judge gave to each generator's ideas" infoId="Generator × Judge Breakdown" />
      <div className="overflow-x-auto">
        <table className="w-full text-[10px] border-collapse">
          <thead>
            <tr>
              <th className="text-left text-[var(--muted)] pb-3 pr-4 font-medium">Generator</th>
              {judges.map(j => (
                <th key={j} className="text-center pb-3 px-4 font-semibold" style={{ color: JUDGE_COLORS[j] }}>
                  {JUDGE_LABELS[j]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map(({ gt, judgeAvgs, count }, ri) => {
              const color = GEN_COLORS[gt]
              return (
                <motion.tr
                  key={gt}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: ri * 0.07 }}
                  className="border-t border-[var(--border)]"
                >
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-sm shrink-0" style={{ background: color }} />
                      <span className="text-white font-medium">{GEN_LABELS[gt]}</span>
                      <span className="text-[8px] text-[var(--muted)]">({count})</span>
                    </div>
                  </td>
                  {judgeAvgs.map(({ judge, avg: jAvg }) => (
                    <td key={judge} className="py-3 px-4 text-center">
                      {jAvg > 0 ? (
                        <div className="space-y-1">
                          <div
                            className="mx-auto h-1.5 rounded"
                            style={{ width: 40, background: 'var(--elevated)', position: 'relative', overflow: 'hidden' }}
                          >
                            <motion.div
                              className="absolute inset-y-0 left-0 rounded"
                              style={{ background: JUDGE_COLORS[judge] }}
                              initial={{ width: 0 }}
                              animate={{ width: `${(jAvg / 10) * 100}%` }}
                              transition={{ duration: 0.7, delay: 0.1 + ri * 0.08 }}
                            />
                          </div>
                          <span className="tabular-nums font-semibold" style={{ color: JUDGE_COLORS[judge] }}>
                            {jAvg.toFixed(1)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-[var(--border)]">—</span>
                      )}
                    </td>
                  ))}
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Main export ────────────────────────────────────────────────────────────────

export function AnalyticsPanel({ ideas, graph, evaluations = [] }: Props) {
  const [bubble, setBubble] = useState<BubbleData | null>(null)

  if (ideas.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-[var(--muted)]">
        <span className="text-4xl mb-3">📊</span>
        <p className="text-sm">No data yet — run the workflow to generate analysis.</p>
      </div>
    )
  }

  // Prefer Neo4j evaluation_edges; fall back to PostgreSQL evaluations table
  const graphEdges = graph?.evaluation_edges ?? []
  const dbEdges: EvaluationEdge[] = evaluations.map(ev => ({
    source: `${ev.judge_type}_${ideas[0]?.project_id ?? ''}`,
    target: ev.idea_id,
    score: ev.score,
    strengths: ev.strengths ?? [],
    weaknesses: ev.weaknesses ?? [],
    recommendations: ev.recommendations ?? [],
  }))
  const graphPairs = new Set(graphEdges.map(e => `${e.source}|${e.target}`))
  const evEdges: EvaluationEdge[] = [
    ...graphEdges,
    ...dbEdges.filter(e => !graphPairs.has(`${e.source}|${e.target}`)),
  ]

  return (
    <InfoCtx.Provider value={setBubble}>
      <div className="space-y-5">

        {/* Row 1: Key metrics */}
        <MetricsRow ideas={ideas} evEdges={evEdges} />

        {/* Row 2: Leaderboard (full width) */}
        <ScoreLeaderboard ideas={ideas} evEdges={evEdges} />

        {/* Row 3: Generator performance + Score distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <GeneratorPerformance ideas={ideas} evEdges={evEdges} />
          <ScoreDistribution ideas={ideas} evEdges={evEdges} />
        </div>

        {/* Row 4: Judge matrix (full width) */}
        <JudgeMatrix ideas={ideas} evEdges={evEdges} />

        {/* Row 5: Generator × Judge + Judge Disagreement */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <GeneratorComparison ideas={ideas} evEdges={evEdges} />
          <JudgeDisagreement ideas={ideas} evEdges={evEdges} />
        </div>

        {/* Row 6: Market Competitors (full width) */}
        <MarketCompetitors ideas={ideas} />

        {/* Row 7: Evolution impact (full width) */}
        <EvolutionImpact ideas={ideas} evEdges={evEdges} />

      </div>

      <InfoBubble data={bubble} onClose={() => setBubble(null)} />
    </InfoCtx.Provider>
  )
}
