'use client'

import { useRef } from 'react'
import Link from 'next/link'
import { motion, useInView } from 'framer-motion'
import { ThemeToggle } from '@/components/ui/ThemeToggle'

/* ── Data ──────────────────────────────────────────────────────────────────── */

const FOUNDERS = [
  {
    codename: 'The Visionary',
    role: 'Creative Founder Agent',
    model: 'Gemini 2.5 Flash',
    description:
      'Sees what others cannot. Conjures blue-ocean disruptions from the void, tearing apart markets with ideas so bold they border on madness.',
    icon: '◈',
    color: 'from-violet-900/30',
    border: 'border-violet-800/40',
    glow: 'rgba(139,92,246,0.15)',
  },
  {
    codename: 'The Consigliere',
    role: 'Market Founder Agent',
    model: 'Gemini 2.5 Flash',
    description:
      'Every empire needs counsel. She reads TAM like scripture and speaks fluent revenue — every move calculated toward dominion.',
    icon: '◎',
    color: 'from-amber-900/30',
    border: 'border-amber-800/40',
    glow: 'rgba(217,119,6,0.15)',
  },
  {
    codename: 'The Enforcer',
    role: 'Builder Founder Agent',
    model: 'Gemini 2.5 Flash',
    description:
      'While others talk, he builds. Sixty-day MVPs, named stacks, engineering moats that competitors cannot tunnel under.',
    icon: '◉',
    color: 'from-emerald-900/30',
    border: 'border-emerald-800/40',
    glow: 'rgba(16,185,129,0.15)',
  },
]

const COUNCIL = [
  {
    title: 'The Don',
    role: 'Investor Judge',
    model: 'GPT-4o-mini',
    rubric: 'Would I write a check today? Scrutinises TAM, moat, exit, and whether the founders understand their own market.',
    icon: '₿',
    border: 'border-gf-gold/30',
    textColor: 'text-gf-gold',
  },
  {
    title: 'The Architect',
    role: 'Engineer Judge',
    model: 'GPT-4o-mini',
    rubric: 'Could I build this by Thursday? Tears into scalability, security, technical debt, and whether the stack actually solves the problem.',
    icon: '⌥',
    border: 'border-cyan-700/40',
    textColor: 'text-cyan-400',
  },
  {
    title: "The Devil's Advocate",
    role: 'Skeptic Judge',
    model: 'GPT-4o-mini',
    rubric: 'Vitamin or painkiller? Exposes every assumption — real CAC, switching costs, and why customers already live without this.',
    icon: '∅',
    border: 'border-red-700/40',
    textColor: 'text-gf-red',
  },
]

const PROCESS = [
  { step: 'I',   name: 'The Research',    desc: 'Your documents are ingested and live market intelligence gathered. The Council knows the terrain.' },
  { step: 'II',  name: 'The Conception',  desc: 'Three Founders generate six distinct startup ideas — bold, market-ready, and technically defensible.' },
  { step: 'III', name: 'The Tribunal',    desc: 'Nine independent judgments are delivered. Every weakness is catalogued. Every strength noted.' },
  { step: 'IV',  name: 'The Evolution',   desc: 'The weakest ideas are taken back to the drawing room and reborn — stronger, sharper, meaner.' },
  { step: 'V',   name: 'The Tournament',  desc: 'One idea rises above all others. The winner earns the right to face the real world.' },
  { step: 'VI',  name: 'The Manifesto',   desc: 'A complete startup bible: market analysis, 90-day roadmap, GTM strategy, financials. Make your move.' },
]

/* ── Sub-components ────────────────────────────────────────────────────────── */

function AnimatedTitle() {
  const letters = 'IDEAFORGE'.split('')
  return (
    <div className="flex items-center justify-center gap-0">
      {letters.map((l, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0, y: 30, filter: 'blur(8px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ delay: 0.3 + i * 0.08, duration: 0.6, ease: 'easeOut' }}
          className="font-cinzel font-bold tracking-[0.25em] text-5xl sm:text-7xl md:text-8xl gold-shimmer"
        >
          {l}
        </motion.span>
      ))}
    </div>
  )
}

function SectionReveal({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

function FounderCard({ f, i }: { f: typeof FOUNDERS[0]; i: number }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: i === 0 ? -40 : i === 2 ? 40 : 0, y: i === 1 ? 40 : 0 }}
      animate={inView ? { opacity: 1, x: 0, y: 0 } : {}}
      transition={{ duration: 0.7, delay: i * 0.12, ease: 'easeOut' }}
      className={`relative rounded-2xl border ${f.border} bg-gradient-to-b ${f.color} to-transparent p-6 flex flex-col gap-4 group cursor-default`}
      style={{ boxShadow: `0 0 40px ${f.glow}` }}
    >
      {/* Ornamental frame corners */}
      <span className="absolute top-2 left-2 text-[var(--border)] text-xs select-none">┌</span>
      <span className="absolute top-2 right-2 text-[var(--border)] text-xs select-none">┐</span>
      <span className="absolute bottom-2 left-2 text-[var(--border)] text-xs select-none">└</span>
      <span className="absolute bottom-2 right-2 text-[var(--border)] text-xs select-none">┘</span>

      <div className="text-4xl text-center opacity-40 group-hover:opacity-80 transition-opacity">
        {f.icon}
      </div>
      <div className="text-center">
        <p className="font-cinzel font-bold text-gf-gold tracking-wider text-sm">{f.codename}</p>
        <p className="text-gf-ash text-xs mt-1">{f.role}</p>
        <p className="text-[10px] text-gf-gold/40 mt-0.5 font-mono">{f.model}</p>
      </div>
      <p className="text-gf-ash/80 text-xs leading-relaxed text-center font-serif">
        {f.description}
      </p>
    </motion.div>
  )
}

function CouncilCard({ c, i }: { c: typeof COUNCIL[0]; i: number }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay: i * 0.15 }}
      className={`relative rounded-2xl border ${c.border} bg-gf-surface p-6 flex flex-col gap-4`}
    >
      <div className={`text-4xl text-center ${c.textColor} opacity-50`}>{c.icon}</div>
      <div className="text-center">
        <p className={`font-cinzel font-bold ${c.textColor} tracking-wider text-sm`}>{c.title}</p>
        <p className="text-gf-ash text-xs mt-1">{c.role}</p>
        <p className="text-[10px] text-gf-gold/40 mt-0.5 font-mono">{c.model} · temp=0</p>
      </div>
      <p className="text-gf-ash/80 text-xs leading-relaxed text-center font-serif">{c.rubric}</p>
    </motion.div>
  )
}

function ProcessStep({ step, i }: { step: typeof PROCESS[0]; i: number }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-40px' })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: -30 }}
      animate={inView ? { opacity: 1, x: 0 } : {}}
      transition={{ duration: 0.5, delay: i * 0.1 }}
      className="flex gap-5 items-start group"
    >
      <div className="shrink-0 w-10 h-10 rounded-full border border-gf-gold/30 flex items-center justify-center bg-gf-surface group-hover:border-gf-gold/70 transition-colors">
        <span className="font-cinzel text-gf-gold text-xs">{step.step}</span>
      </div>
      <div className="flex-1 pb-6 border-b border-gf-border/40 last:border-0">
        <p className="font-serif font-bold text-gf-cream text-sm mb-1">{step.name}</p>
        <p className="text-gf-ash text-xs leading-relaxed">{step.desc}</p>
      </div>
    </motion.div>
  )
}

/* ── Page ──────────────────────────────────────────────────────────────────── */

export default function Home() {
  return (
    <main
      className="film-grain vignette min-h-screen"
      style={{ background: 'linear-gradient(180deg, #080505 0%, #0A0505 50%, #080303 100%)' }}
    >
      {/* ── Navbar overlay ──────────────────────────────────────────────── */}
      <div className="fixed top-0 right-0 p-4 z-[200] flex items-center gap-3">
        <Link
          href="/projects"
          className="text-xs text-gf-ash hover:text-gf-gold transition-colors font-cinzel tracking-widest"
        >
          ENTER
        </Link>
        <ThemeToggle />
      </div>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 text-center z-10">
        {/* Radial red glow behind title */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 60% 40% at 50% 50%, rgba(139,16,32,0.18) 0%, transparent 70%)' }}
        />

        <AnimatedTitle />

        {/* Red horizontal rule */}
        <motion.div
          initial={{ scaleX: 0, opacity: 0 }}
          animate={{ scaleX: 1, opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.8, ease: 'easeOut' }}
          className="w-48 h-px bg-gf-red my-6"
          style={{ transformOrigin: 'center' }}
        />

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.6, duration: 0.6 }}
          className="text-gf-ash text-sm tracking-[0.3em] uppercase font-cinzel"
        >
          Startup Survival Simulator
        </motion.p>

        <motion.blockquote
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 2.0, duration: 0.7 }}
          className="mt-10 max-w-md font-serif text-gf-cream/70 text-lg leading-relaxed italic"
        >
          "I'm gonna make your market an offer it cannot refuse."
        </motion.blockquote>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 2.5, duration: 0.6 }}
          className="mt-12 flex flex-col sm:flex-row gap-4 items-center"
        >
          <Link
            href="/projects/new"
            className="btn-gf relative px-10 py-3.5 bg-gf-red text-gf-cream font-cinzel text-xs tracking-[0.2em] rounded border border-gf-red hover:bg-gf-red-dk transition-colors animate-glow-pulse"
          >
            SUBMIT YOUR PITCH
          </Link>
          <Link
            href="/projects"
            className="px-8 py-3.5 border border-gf-gold/30 text-gf-gold font-cinzel text-xs tracking-[0.2em] rounded hover:border-gf-gold hover:bg-gf-gold/5 transition-all"
          >
            VIEW PROJECTS
          </Link>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 3.2, duration: 1 }}
          className="absolute bottom-10 flex flex-col items-center gap-2"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
            className="w-px h-8 bg-gradient-to-b from-gf-gold/60 to-transparent"
          />
          <span className="text-gf-gold/40 text-[9px] tracking-[0.4em] font-cinzel">SCROLL</span>
        </motion.div>
      </section>

      {/* ── The Founders ────────────────────────────────────────────────── */}
      <section className="relative z-10 px-6 py-24 max-w-6xl mx-auto">
        <SectionReveal className="text-center mb-16">
          <p className="text-gf-red text-[10px] tracking-[0.5em] font-cinzel mb-4">THE ARCHITECTS</p>
          <h2 className="font-cinzel font-bold text-gf-cream text-3xl md:text-4xl">
            The Three Founders
          </h2>
          <div className="w-24 h-px bg-gf-border mx-auto mt-6" />
          <p className="text-gf-ash text-sm mt-6 max-w-lg mx-auto leading-relaxed font-serif">
            Every great empire requires three minds. One to dream it. One to sell it. One to build it.
          </p>
        </SectionReveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {FOUNDERS.map((f, i) => <FounderCard key={f.codename} f={f} i={i} />)}
        </div>
      </section>

      {/* ── Ornamental divider ───────────────────────────────────────────── */}
      <div className="flex items-center justify-center gap-4 px-6 opacity-20">
        <div className="flex-1 h-px bg-gf-border" />
        <span className="text-gf-gold font-cinzel text-xs">✦</span>
        <div className="flex-1 h-px bg-gf-border" />
      </div>

      {/* ── The Council ─────────────────────────────────────────────────── */}
      <section className="relative z-10 px-6 py-24 max-w-6xl mx-auto">
        <SectionReveal className="text-center mb-16">
          <p className="text-gf-red text-[10px] tracking-[0.5em] font-cinzel mb-4">THE JUDGMENT</p>
          <h2 className="font-cinzel font-bold text-gf-cream text-3xl md:text-4xl">
            The Council of Judgment
          </h2>
          <div className="w-24 h-px bg-gf-border mx-auto mt-6" />
          <p className="text-gf-ash text-sm mt-6 max-w-lg mx-auto leading-relaxed font-serif">
            Three judges. Zero mercy. Your idea will be cross-examined from every angle before a verdict is rendered.
          </p>
        </SectionReveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {COUNCIL.map((c, i) => <CouncilCard key={c.title} c={c} i={i} />)}
        </div>
      </section>

      {/* ── The Process ─────────────────────────────────────────────────── */}
      <section className="relative z-10 px-6 py-24" style={{ background: 'rgba(0,0,0,0.4)' }}>
        <div className="max-w-3xl mx-auto">
          <SectionReveal className="text-center mb-16">
            <p className="text-gf-red text-[10px] tracking-[0.5em] font-cinzel mb-4">THE OPERATION</p>
            <h2 className="font-cinzel font-bold text-gf-cream text-3xl md:text-4xl">
              How the Family Operates
            </h2>
            <div className="w-24 h-px bg-gf-border mx-auto mt-6" />
          </SectionReveal>
          <div className="space-y-0">
            {PROCESS.map((step, i) => <ProcessStep key={step.step} step={step} i={i} />)}
          </div>
        </div>
      </section>

      {/* ── Final CTA ───────────────────────────────────────────────────── */}
      <section className="relative z-10 px-6 py-32 text-center">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 50% 60% at 50% 50%, rgba(139,16,32,0.12) 0%, transparent 70%)' }}
        />
        <SectionReveal>
          <h2 className="font-cinzel font-bold text-gf-cream text-3xl md:text-5xl leading-tight mb-8">
            Ready to Make<br />
            <span className="gold-shimmer">Your Move?</span>
          </h2>
          <p className="text-gf-ash text-sm font-serif max-w-md mx-auto mb-12 leading-relaxed">
            The table is set. The council awaits. Submit your problem and let the Family decide
            whether your idea deserves to live.
          </p>
          <Link
            href="/projects/new"
            className="btn-gf inline-block px-14 py-4 bg-gf-red text-gf-cream font-cinzel text-sm tracking-[0.25em] rounded border border-gf-red hover:bg-gf-red-dk transition-all animate-glow-pulse"
          >
            MAKE YOUR MOVE
          </Link>
        </SectionReveal>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="relative z-10 border-t border-gf-border/40 py-8 text-center">
        <p className="text-gf-ash/30 text-[10px] font-cinzel tracking-[0.4em]">
          IDEAFORGE · STARTUP SURVIVAL SIMULATOR · AI-POWERED
        </p>
      </footer>
    </main>
  )
}
