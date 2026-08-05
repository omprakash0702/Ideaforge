'use client'

import { useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Trophy, GitBranch, TrendingUp, Wrench, AlertTriangle, ArrowUp, X, GitMerge } from 'lucide-react'
import type { IdeaGraphResponse, IdeaGraphNode, IdeaGraphEdge, EvaluationEdge } from '@/lib/api'

interface Props { graph: IdeaGraphResponse }

const NODE_W = 190
const NODE_H = 76
const H_GAP  = 64
const V_GAP  = 110

function layoutNodes(nodes: IdeaGraphNode[], edges: IdeaGraphResponse['edges']) {
  const evoEdges   = edges.filter(e => e.type === 'EVOLVED_INTO')
  const childOf    = new Map<string, string>()
  const childrenOf = new Map<string, string[]>()

  for (const e of evoEdges) {
    childOf.set(e.target, e.source)
    if (!childrenOf.has(e.source)) childrenOf.set(e.source, [])
    childrenOf.get(e.source)!.push(e.target)
  }

  // Only call place() from true roots (nodes with no parent edge)
  const roots     = nodes.filter(n => !childOf.has(n.id))
  const positions = new Map<string, { x: number; y: number }>()
  let xCursor     = 0

  function place(id: string, depth: number) {
    const children = childrenOf.get(id) ?? []
    if (children.length === 0) {
      positions.set(id, { x: xCursor * (NODE_W + H_GAP), y: depth * (NODE_H + V_GAP) })
      xCursor++
    } else {
      const start = xCursor
      for (const c of children) place(c, depth + 1)
      const mid = ((start + xCursor - 1) / 2) * (NODE_W + H_GAP)
      positions.set(id, { x: mid, y: depth * (NODE_H + V_GAP) })
    }
  }

  for (const r of roots) place(r.id, 0)

  // Fallback: any node that still has no position (edge references a missing parent)
  // place it as an orphan at the bottom so it's always visible
  const maxDepth = nodes.reduce((m, n) => Math.max(m, n.version - 1), 0)
  for (const node of nodes) {
    if (!positions.has(node.id)) {
      positions.set(node.id, { x: xCursor * (NODE_W + H_GAP), y: (maxDepth + 1) * (NODE_H + V_GAP) })
      xCursor++
    }
  }

  return positions
}

function scoreColor(score: number | null) {
  if (score == null) return '#64748b'
  if (score >= 8)    return '#22C55E'
  if (score >= 6)    return '#F59E0B'
  return '#EF4444'
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

const JUDGE_META: Record<string, { Icon: typeof TrendingUp; color: string; label: string }> = {
  INVESTOR: { Icon: TrendingUp,    color: '#FCD34D', label: 'Investor' },
  ENGINEER: { Icon: Wrench,        color: '#60A5FA', label: 'Engineer' },
  SKEPTIC:  { Icon: AlertTriangle, color: '#F87171', label: 'Skeptic'  },
}

// ── Graph node ─────────────────────────────────────────────────────────────────

function GraphNode({
  node, x, y, selected, onClick,
}: {
  node: IdeaGraphNode; x: number; y: number; selected: boolean; onClick: () => void
}) {
  const color    = scoreColor(node.aggregate_score)
  const genColor = node.generator_type ? GEN_COLORS[node.generator_type] : null

  return (
    <g
      transform={`translate(${x}, ${y})`}
      style={{ cursor: 'pointer' }}
      onClick={onClick}
    >
      {node.is_winner && (
        <motion.rect
          x={-5} y={-5} width={NODE_W + 10} height={NODE_H + 10}
          rx={15} ry={15} fill="none"
          stroke="#EAB308" strokeWidth={1.5}
          animate={{ opacity: [0.4, 0.9, 0.4] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      )}
      <rect
        width={NODE_W} height={NODE_H} rx={11} ry={11}
        fill={selected ? 'rgba(124,92,252,0.35)' : '#1e2156'}
        stroke={selected ? '#7c5cfc' : node.is_winner ? '#EAB308' : '#5c5c9a'}
        strokeWidth={selected ? 2 : 1.5}
      />
      {genColor && (
        <rect x={0} y={0} width={3} height={NODE_H} rx={2} ry={2} fill={genColor} opacity={0.8} />
      )}
      <motion.rect
        x={0} y={NODE_H - 3} height={3} rx={0}
        style={{ fill: color }}
        initial={{ width: 0 }}
        animate={{ width: node.aggregate_score ? (node.aggregate_score / 10) * NODE_W : 0 }}
        transition={{ duration: 0.9, ease: 'easeOut', delay: 0.3 }}
      />
      {node.is_winner && (
        <text x={NODE_W - 14} y={15} textAnchor="middle" fontSize={11}>🏆</text>
      )}
      {node.version > 1 && (
        <text x={NODE_W - 30} y={15} textAnchor="middle" fontSize={9} fill="#22D3EE" fontWeight="bold">v{node.version}↑</text>
      )}
      <foreignObject x={10} y={10} width={NODE_W - 22} height={44}>
        <div style={{
          fontSize: '11px', color: '#e2e8f0', fontWeight: 500,
          overflow: 'hidden', display: '-webkit-box',
          WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as const,
          lineHeight: 1.4,
        }}>
          {node.title}
        </div>
      </foreignObject>
      {node.aggregate_score != null && (
        <text x={NODE_W / 2} y={NODE_H - 8}
          textAnchor="middle" fontSize={8.5} fill={color} fontWeight="bold">
          {node.aggregate_score.toFixed(1)}/10
        </text>
      )}
    </g>
  )
}

// ── Family tree modal ──────────────────────────────────────────────────────────

function FamilyTreeModal({
  selectedId,
  nodes,
  evoEdges,
  evaluationEdges,
  onClose,
}: {
  selectedId: string
  nodes: IdeaGraphNode[]
  evoEdges: IdeaGraphEdge[]
  evaluationEdges: EvaluationEdge[]
  onClose: () => void
}) {
  // Walk up to find the true family root
  const parentOf = new Map(evoEdges.map(e => [e.target, e.source]))
  let rootId = selectedId
  while (parentOf.has(rootId)) rootId = parentOf.get(rootId)!

  const rootNode = nodes.find(n => n.id === rootId)
  if (!rootNode) return null

  // BFS to collect all descendants grouped by depth
  type DescendantEntry = { node: IdeaGraphNode; edge: IdeaGraphEdge; depth: number }
  const descendants: DescendantEntry[] = []
  const visited = new Set<string>([rootId])
  const queue: { id: string; depth: number }[] = [{ id: rootId, depth: 0 }]
  while (queue.length > 0) {
    const { id, depth } = queue.shift()!
    for (const e of evoEdges.filter(e2 => e2.source === id)) {
      if (!visited.has(e.target)) {
        visited.add(e.target)
        const node = nodes.find(n => n.id === e.target)
        if (node) {
          descendants.push({ node, edge: e, depth: depth + 1 })
          queue.push({ id: e.target, depth: depth + 1 })
        }
      }
    }
  }
  // For backward compat, keep children = depth-1 descendants
  const children = descendants.filter(d => d.depth === 1).map(d => ({ node: d.node, edge: d.edge }))

  const rootEvals = evaluationEdges.filter(e => e.target === rootId)
  const rootColor  = rootNode.generator_type ? GEN_COLORS[rootNode.generator_type] : 'var(--muted)'

  // SVG connector dimensions
  const CARD_W  = 260
  const SVG_H   = 64
  const rootCX  = (children.length * CARD_W + (children.length - 1) * 16) / 2

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)' }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="rounded-2xl border border-[var(--border)] bg-[var(--elevated)] w-full overflow-auto"
        style={{ maxWidth: Math.max(600, children.length * 280 + 80), maxHeight: '90vh' }}
        initial={{ opacity: 0, scale: 0.92, y: 24 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.94, y: 12 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <GitMerge className="w-4 h-4 text-[var(--accent)]" />
            <span className="font-semibold text-white text-sm">Family Lineage Tree</span>
            <span className="text-[10px] text-[var(--muted)] ml-1">
              {descendants.length === 0
                ? 'No evolutions yet'
                : (() => {
                    const gens = new Set(descendants.map(d => d.depth)).size
                    return `1 original → ${descendants.length} evolved · ${gens} generation${gens !== 1 ? 's' : ''}`
                  })()
              }
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-[var(--muted)] hover:text-white transition-colors p-1 rounded-lg hover:bg-[var(--surface)]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-0">

          {/* Root node card */}
          <div className="flex justify-center">
            <motion.div
              initial={{ opacity: 0, y: -16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="rounded-xl border-2 p-4 w-72"
              style={{
                borderColor: rootColor + '60',
                background: rootColor + '0e',
              }}
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <span
                    className="text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded"
                    style={{ color: rootColor, background: rootColor + '20' }}
                  >
                    {rootNode.generator_type ? GEN_LABELS[rootNode.generator_type] : 'Original'} · v1
                  </span>
                </div>
                {rootNode.is_winner && <span className="text-base">🏆</span>}
              </div>
              <p className="text-sm font-semibold text-white leading-tight mt-2">{rootNode.title}</p>
              {rootNode.solution && (
                <p className="text-[10px] text-[var(--muted)] mt-1 leading-relaxed line-clamp-2">{rootNode.solution}</p>
              )}
              <div className="flex items-center gap-3 mt-3">
                {rootNode.aggregate_score != null && (
                  <span className="text-[11px] font-bold tabular-nums" style={{ color: scoreColor(rootNode.aggregate_score) }}>
                    {rootNode.aggregate_score.toFixed(2)}/10
                  </span>
                )}
                <span className="text-[9px] text-[var(--muted)]">Rank #{rootNode.tournament_rank ?? '—'}</span>
              </div>
              {/* Mini judge scores */}
              {rootEvals.length > 0 && (
                <div className="flex gap-1.5 mt-2 flex-wrap">
                  {rootEvals.map(ev => {
                    const jtype = ev.source.split('_')[0]
                    const meta  = JUDGE_META[jtype]
                    if (!meta) return null
                    return (
                      <span
                        key={ev.source}
                        className="text-[9px] font-semibold tabular-nums px-1.5 py-0.5 rounded"
                        style={{ color: meta.color, background: meta.color + '20' }}
                      >
                        {meta.label[0]}: {ev.score.toFixed(1)}
                      </span>
                    )
                  })}
                </div>
              )}
            </motion.div>
          </div>

          {/* SVG connector lines */}
          {children.length > 0 && (
            <div className="flex justify-center overflow-visible">
              <svg
                width={children.length * (CARD_W + 16) + 16}
                height={SVG_H}
                style={{ overflow: 'visible' }}
              >
                {/* Vertical line down from root */}
                <motion.line
                  x1={rootCX} y1={0} x2={rootCX} y2={SVG_H / 2}
                  stroke="var(--accent)" strokeWidth={1.5} strokeDasharray="4 3"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 0.7 }}
                  transition={{ duration: 0.4, delay: 0.3 }}
                />
                {/* Horizontal bar */}
                {children.length > 1 && (
                  <motion.line
                    x1={CARD_W / 2 + 8} y1={SVG_H / 2}
                    x2={(children.length - 1) * (CARD_W + 16) + CARD_W / 2 + 8} y2={SVG_H / 2}
                    stroke="var(--accent)" strokeWidth={1.5} strokeDasharray="4 3"
                    initial={{ scaleX: 0, opacity: 0 }}
                    animate={{ scaleX: 1, opacity: 0.7 }}
                    transition={{ duration: 0.4, delay: 0.5 }}
                    style={{ transformOrigin: `${rootCX}px ${SVG_H / 2}px` }}
                  />
                )}
                {/* Vertical drops to each child */}
                {children.map((_, ci) => {
                  const cx = ci * (CARD_W + 16) + CARD_W / 2 + 8
                  return (
                    <motion.line
                      key={ci}
                      x1={cx} y1={SVG_H / 2} x2={cx} y2={SVG_H}
                      stroke="var(--accent)" strokeWidth={1.5} strokeDasharray="4 3"
                      initial={{ pathLength: 0, opacity: 0 }}
                      animate={{ pathLength: 1, opacity: 0.7 }}
                      transition={{ duration: 0.3, delay: 0.6 + ci * 0.08 }}
                    />
                  )
                })}
                {/* Score delta labels on the line */}
                {children.map(({ edge }, ci) => {
                  if (!edge.score_delta) return null
                  const cx = ci * (CARD_W + 16) + CARD_W / 2 + 8
                  return (
                    <motion.text
                      key={`delta-${ci}`}
                      x={cx + 6} y={SVG_H / 2 + 4}
                      fontSize={9} fill="#22D3EE" fontWeight="bold"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.7 + ci * 0.1 }}
                    >
                      +{edge.score_delta.toFixed(1)}
                    </motion.text>
                  )
                })}
              </svg>
            </div>
          )}

          {/* Child cards */}
          {children.length > 0 && (
            <div
              className="flex gap-4 overflow-x-auto pb-2"
              style={{ justifyContent: children.length <= 3 ? 'center' : 'flex-start' }}
            >
              {children.map(({ node, edge }, ci) => {
                const childEvals  = evaluationEdges.filter(e => e.target === node.id)
                const genColor    = node.generator_type ? GEN_COLORS[node.generator_type] : 'var(--muted)'
                return (
                  <motion.div
                    key={node.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.5 + ci * 0.1 }}
                    className="rounded-xl border p-4 shrink-0"
                    style={{
                      width: CARD_W,
                      borderColor: genColor + '50',
                      background: genColor + '0a',
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span
                        className="text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded"
                        style={{ color: genColor, background: genColor + '20' }}
                      >
                        {node.generator_type ? GEN_LABELS[node.generator_type] : 'Evolved'} · v{node.version}
                      </span>
                      {node.is_winner && <span className="text-base">🏆</span>}
                    </div>

                    <p className="text-xs font-semibold text-white leading-tight mt-2">{node.title}</p>

                    {node.solution && (
                      <p className="text-[10px] text-[var(--muted)] mt-1 leading-relaxed line-clamp-2">
                        {node.solution}
                      </p>
                    )}

                    <div className="flex items-center gap-3 mt-2">
                      {node.aggregate_score != null && (
                        <span className="text-[11px] font-bold tabular-nums" style={{ color: scoreColor(node.aggregate_score) }}>
                          {node.aggregate_score.toFixed(2)}/10
                        </span>
                      )}
                      {edge.score_delta != null && edge.score_delta > 0 && (
                        <span className="text-[10px] text-emerald-400 flex items-center gap-0.5 font-semibold">
                          <ArrowUp className="w-2.5 h-2.5" />+{edge.score_delta.toFixed(1)}
                        </span>
                      )}
                    </div>

                    {/* Evolution rationale */}
                    {edge.evolution_rationale && (
                      <div
                        className="mt-2 rounded-lg p-2 text-[9px] leading-relaxed line-clamp-3"
                        style={{ background: 'rgba(34,211,238,0.06)', color: '#67E8F9', border: '1px solid rgba(34,211,238,0.15)' }}
                      >
                        {edge.evolution_rationale}
                      </div>
                    )}

                    {/* Mini judge scores */}
                    {childEvals.length > 0 && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {childEvals.map(ev => {
                          const jtype = ev.source.split('_')[0]
                          const meta  = JUDGE_META[jtype]
                          if (!meta) return null
                          return (
                            <span
                              key={ev.source}
                              className="text-[9px] font-semibold tabular-nums px-1.5 py-0.5 rounded"
                              style={{ color: meta.color, background: meta.color + '20' }}
                            >
                              {meta.label[0]}: {ev.score.toFixed(1)}
                            </span>
                          )
                        })}
                      </div>
                    )}
                  </motion.div>
                )
              })}
            </div>
          )}

          {/* Deeper generations (v3, v4, ...) */}
          {descendants.filter(d => d.depth > 1).length > 0 && (
            <div className="mt-4 space-y-3">
              {[...new Set(descendants.filter(d => d.depth > 1).map(d => d.depth))].sort((a, b) => a - b).map(depth => (
                <div key={depth}>
                  <p className="text-[9px] font-bold uppercase tracking-widest text-cyan-500/60 px-1 mb-2">
                    Generation {depth} (v{depth + 1})
                  </p>
                  <div className="flex gap-3 overflow-x-auto pb-1">
                    {descendants.filter(d => d.depth === depth).map(({ node, edge }) => {
                      const genColor = node.generator_type ? GEN_COLORS[node.generator_type] : 'var(--muted)'
                      return (
                        <div
                          key={node.id}
                          className="rounded-xl border p-3 shrink-0"
                          style={{ width: 220, borderColor: genColor + '40', background: genColor + '08' }}
                        >
                          <p className="text-[10px] font-semibold text-white leading-tight line-clamp-2">{node.title}</p>
                          {node.aggregate_score != null && (
                            <span className="text-[10px] font-bold tabular-nums mt-1 block" style={{ color: scoreColor(node.aggregate_score) }}>
                              {node.aggregate_score.toFixed(2)}/10
                            </span>
                          )}
                          {edge.evolution_rationale && (
                            <p className="text-[9px] text-cyan-400/70 mt-1 leading-relaxed line-clamp-2">{edge.evolution_rationale}</p>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {children.length === 0 && (
            <div className="flex justify-center py-6">
              <p className="text-[var(--muted)] text-xs">This idea was not evolved (it already scored well).</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}

// ── Detail panel ───────────────────────────────────────────────────────────────

function DetailPanel({
  node, evaluationEdges, evoEdges, onShowTree,
}: {
  node: IdeaGraphNode
  evaluationEdges: EvaluationEdge[]
  evoEdges: IdeaGraphEdge[]
  onShowTree: () => void
}) {
  const myEvals = evaluationEdges.filter(e => e.target === node.id)
  const evoIn   = evoEdges.find(e => e.target === node.id && e.type === 'EVOLVED_INTO')

  return (
    <motion.div
      key={node.id}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.25 }}
      className="rounded-xl border border-[var(--accent)] bg-[var(--elevated)] p-5 space-y-4"
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        {node.is_winner && <Trophy className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />}
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-white text-sm leading-tight">{node.title}</h4>
          <div className="flex items-center gap-3 mt-1 text-[10px] text-[var(--muted)]">
            <span>Rank #{node.tournament_rank ?? '—'}</span>
            <span>·</span>
            <span style={{ color: scoreColor(node.aggregate_score) }}>
              {node.aggregate_score?.toFixed(2) ?? '—'}/10
            </span>
            {node.generator_type && (
              <>
                <span>·</span>
                <span style={{ color: GEN_COLORS[node.generator_type] }}>
                  {GEN_LABELS[node.generator_type] ?? node.generator_type}
                </span>
              </>
            )}
            {node.version > 1 && (
              <span className="text-cyan-400 flex items-center gap-0.5">
                <GitBranch className="w-2.5 h-2.5" />v{node.version}
              </span>
            )}
          </div>
        </div>
        {/* View lineage tree button */}
        <button
          onClick={onShowTree}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--border)] text-[10px] text-[var(--muted)] hover:text-[var(--accent)] hover:border-[var(--accent)] transition-colors shrink-0"
        >
          <GitMerge className="w-3 h-3" />
          Lineage
        </button>
      </div>

      {node.solution && (
        <div className="text-[11px] text-[var(--muted)] leading-relaxed line-clamp-3">
          <span className="text-[var(--text)] font-medium">Solution: </span>
          {node.solution}
        </div>
      )}

      {evoIn?.evolution_rationale && (
        <div className="rounded-lg border border-cyan-800/40 bg-cyan-950/20 p-3 text-[10px] text-cyan-300 leading-relaxed">
          <div className="flex items-center gap-1.5 mb-1 font-semibold">
            <ArrowUp className="w-3 h-3" />
            Evolution rationale
            {evoIn.score_delta != null && (
              <span className="ml-auto text-emerald-400">
                +{evoIn.score_delta.toFixed(1)} pts
              </span>
            )}
          </div>
          {evoIn.evolution_rationale}
        </div>
      )}

      {myEvals.length > 0 && (
        <div className="space-y-2">
          <p className="text-[9px] font-bold uppercase tracking-widest text-[var(--muted)]">
            Judge Verdicts
          </p>
          {myEvals.map(ev => {
            const jtype = ev.source.split('_')[0]
            const meta  = JUDGE_META[jtype]
            if (!meta) return null
            const { Icon, color, label } = meta
            return (
              <motion.div
                key={ev.source}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Icon className="w-3 h-3" style={{ color }} />
                    <span className="text-[10px] font-semibold" style={{ color }}>{label}</span>
                  </div>
                  <span className="text-[11px] font-bold tabular-nums" style={{ color }}>
                    {ev.score.toFixed(1)}/10
                  </span>
                </div>
                <div className="h-1 bg-[var(--elevated)] rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(ev.score / 10) * 100}%` }}
                    transition={{ duration: 0.6 }}
                  />
                </div>
                {ev.strengths.length > 0 && (
                  <div className="text-[9px] text-emerald-400 leading-relaxed">
                    ✓ {ev.strengths[0]}
                  </div>
                )}
                {ev.weaknesses.length > 0 && (
                  <div className="text-[9px] text-red-400 leading-relaxed">
                    ✗ {ev.weaknesses[0]}
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>
      )}
    </motion.div>
  )
}

// ── Main export ────────────────────────────────────────────────────────────────

export function IdeaGraph({ graph }: Props) {
  const [selected, setSelected]         = useState<IdeaGraphNode | null>(null)
  const [treeNodeId, setTreeNodeId]     = useState<string | null>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  const evoEdges  = graph.edges.filter(e => e.type === 'EVOLVED_INTO')
  const rankEdges = graph.edges.filter(e => e.type === 'RANKED_ABOVE')

  if (graph.nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-[var(--muted)]">
        <GitBranch className="w-10 h-10 mb-3 opacity-30" />
        <p className="text-sm">No graph data yet. Run the workflow first.</p>
      </div>
    )
  }

  const positions = layoutNodes(graph.nodes, graph.edges)
  const posVals = [...positions.values()]
  const PAD = 48
  const svgW = posVals.length > 0
    ? Math.max(...posVals.map(p => p.x)) + NODE_W + PAD * 2
    : NODE_W + PAD * 2
  const svgH = posVals.length > 0
    ? Math.max(...posVals.map(p => p.y)) + NODE_H + PAD * 2
    : NODE_H + PAD * 2
  const viewBox = `-${PAD} -${PAD} ${svgW} ${svgH}`

  // When many columns exist, auto-scaling makes nodes too tiny to read.
  // Threshold: if svgW fits in ~900px at ≥60% scale → auto-scale.
  // Otherwise use explicit pixel size so nodes stay full-size and container scrolls.
  const useScroll = svgW > 900

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-[10px] text-[var(--muted)]">
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-green-500" />≥ 8.0</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-500" />≥ 6.0</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-500" />&lt; 6.0</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-px border-t-2 border-dashed border-[var(--muted)]" />Evolved from</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-px border-t border-[var(--muted)] opacity-40" />Ranked above</span>
        {Object.entries(GEN_COLORS).map(([k, c]) => (
          <span key={k} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-sm" style={{ background: c }} />{GEN_LABELS[k]}
          </span>
        ))}
        <span className="ml-auto flex items-center gap-1 text-[var(--accent)] font-medium">
          <GitMerge className="w-3 h-3" />Click node → Lineage tree
        </span>
      </div>

      {/* SVG canvas */}
      {useScroll && (
        <p className="text-[10px] text-[var(--muted)] flex items-center gap-1.5">
          <span>←</span> Scroll right to see all {graph.nodes.length} ideas <span>→</span>
        </p>
      )}
      <div
        className="rounded-xl border border-[var(--border)] overflow-auto"
        style={{ background: '#090914', maxHeight: '70vh' }}
      >
        <svg
          ref={svgRef}
          viewBox={viewBox}
          style={useScroll
            ? { display: 'block', width: svgW, height: Math.max(svgH, 300), flexShrink: 0 }
            : { display: 'block', width: '100%', height: 'auto', minHeight: 260 }
          }
        >

          {rankEdges.map((edge, i) => {
            const s = positions.get(edge.source)
            const t = positions.get(edge.target)
            if (!s || !t) return null
            const sx = s.x + NODE_W / 2, sy = s.y + NODE_H / 2
            const tx = t.x + NODE_W / 2, ty = t.y + NODE_H / 2
            return (
              <motion.line
                key={`rank-${i}`}
                x1={sx} y1={sy} x2={tx} y2={ty}
                stroke="#2d2d50" strokeWidth={0.8} opacity={0.35}
                initial={{ opacity: 0 }} animate={{ opacity: 0.35 }}
                transition={{ duration: 0.5, delay: 0.6 + i * 0.05 }}
              />
            )
          })}

          {evoEdges.map((edge, i) => {
            const s = positions.get(edge.source)
            const t = positions.get(edge.target)
            if (!s || !t) return null
            const sx = s.x + NODE_W / 2, sy = s.y + NODE_H
            const tx = t.x + NODE_W / 2, ty = t.y
            const my = (sy + ty) / 2
            const hasBonus = (edge.score_delta ?? 0) > 0
            // Cap delay so it never becomes sluggish with many edges
            const delay = Math.min(0.3 + i * 0.12, 1.5)
            return (
              <g key={`evo-${i}`}>
                <motion.path
                  d={`M ${sx} ${sy} C ${sx} ${my}, ${tx} ${my}, ${tx} ${ty}`}
                  fill="none"
                  stroke={hasBonus ? '#22D3EE' : '#3a3a60'}
                  strokeWidth={hasBonus ? 1.8 : 1.2}
                  strokeDasharray="5 3"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 1 }}
                  transition={{ duration: 0.7, delay }}
                />
                {edge.score_delta != null && (
                  <motion.text
                    x={(sx + tx) / 2} y={my}
                    textAnchor="middle" fontSize={8}
                    fill="#22D3EE" fontWeight="bold"
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    transition={{ duration: 0.4, delay: delay + 0.4 }}
                  >
                    +{edge.score_delta.toFixed(1)}
                  </motion.text>
                )}
              </g>
            )
          })}

          {graph.nodes.map(node => {
            const pos = positions.get(node.id)
            if (!pos) return null
            return (
              <GraphNode
                key={node.id}
                node={node}
                x={pos.x}
                y={pos.y}
                selected={selected?.id === node.id}
                onClick={() => {
                  const next = selected?.id === node.id ? null : node
                  setSelected(next)
                }}
              />
            )
          })}
        </svg>
      </div>

      {/* Detail panel */}
      <AnimatePresence mode="wait">
        {selected && (
          <DetailPanel
            key={selected.id}
            node={selected}
            evaluationEdges={graph.evaluation_edges}
            evoEdges={graph.edges}
            onShowTree={() => setTreeNodeId(selected.id)}
          />
        )}
      </AnimatePresence>

      {/* Lineage tree modal */}
      <AnimatePresence>
        {treeNodeId && (
          <FamilyTreeModal
            selectedId={treeNodeId}
            nodes={graph.nodes}
            evoEdges={evoEdges}
            evaluationEdges={graph.evaluation_edges}
            onClose={() => setTreeNodeId(null)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  )
}
