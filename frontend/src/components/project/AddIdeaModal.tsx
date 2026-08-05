'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Loader2, Plus, Lightbulb } from 'lucide-react'
import toast from 'react-hot-toast'
import { api, type Idea, type UserIdeaCreate } from '@/lib/api'

interface Props {
  projectId: string
  open: boolean
  onClose: () => void
  onAdded: (idea: Idea) => void
}

const EMPTY: UserIdeaCreate = {
  title: '',
  problem: '',
  solution: '',
  target_audience: '',
  business_model: '',
  tech_stack: '',
  key_features: [],
  competitors: [],
}

function Field({
  label, name, value, onChange, multiline = false, placeholder,
}: {
  label: string
  name: string
  value: string
  onChange: (v: string) => void
  multiline?: boolean
  placeholder?: string
}) {
  const shared = `
    w-full bg-[var(--elevated)] border border-[var(--border)] rounded-lg px-3 py-2
    text-sm text-white placeholder:text-[var(--muted)] focus:outline-none
    focus:border-[var(--accent)] transition-colors resize-none
  `
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide">{label}</label>
      {multiline ? (
        <textarea
          rows={3}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className={shared}
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className={shared}
        />
      )}
    </div>
  )
}

function TagField({
  label, values, onChange, placeholder,
}: {
  label: string
  values: string[]
  onChange: (v: string[]) => void
  placeholder?: string
}) {
  const [input, setInput] = useState('')

  function add() {
    const v = input.trim()
    if (v && !values.includes(v)) onChange([...values, v])
    setInput('')
  }

  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide">{label}</label>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }}
          placeholder={placeholder}
          className="flex-1 bg-[var(--elevated)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-white placeholder:text-[var(--muted)] focus:outline-none focus:border-[var(--accent)] transition-colors"
        />
        <button
          type="button"
          onClick={add}
          className="px-3 py-2 rounded-lg border border-[var(--border)] text-[var(--muted)] hover:text-white hover:border-[var(--accent)] transition-colors"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
      {values.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {values.map((v, i) => (
            <span
              key={i}
              className="flex items-center gap-1 text-[11px] bg-[var(--elevated)] border border-[var(--border)] text-[var(--muted)] px-2 py-0.5 rounded"
            >
              {v}
              <button
                type="button"
                onClick={() => onChange(values.filter((_, j) => j !== i))}
                className="hover:text-white ml-0.5"
              >
                <X className="w-2.5 h-2.5" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export function AddIdeaModal({ projectId, open, onClose, onAdded }: Props) {
  const [form, setForm] = useState<UserIdeaCreate>(EMPTY)
  const [submitting, setSubmitting] = useState(false)

  function set(key: keyof UserIdeaCreate, value: string | string[]) {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  const required = ['title', 'problem', 'solution', 'target_audience', 'business_model', 'tech_stack'] as const
  const canSubmit = required.every(k => (form[k] as string).trim().length > 0) && !submitting

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    setSubmitting(true)
    try {
      const idea = await api.projects.addIdea(projectId, form)
      onAdded(idea)
      toast.success('Your idea was judged and added!')
      setForm(EMPTY)
      onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to add idea')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.2 }}
            className="relative z-10 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-2xl"
          >
            {/* Header */}
            <div className="sticky top-0 z-10 flex items-center justify-between p-6 border-b border-[var(--border)] bg-[var(--surface)]">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-pink-900/40 border border-pink-700/50 flex items-center justify-center">
                  <Lightbulb className="w-4 h-4 text-pink-400" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-white">Add Your Idea</h2>
                  <p className="text-[11px] text-[var(--muted)]">The AI council will judge it alongside the generated ideas</p>
                </div>
              </div>
              <button onClick={onClose} className="text-[var(--muted)] hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              <Field
                label="Idea Title *"
                name="title"
                value={form.title}
                onChange={v => set('title', v)}
                placeholder="e.g. EquiPay — Freelancer Payment Platform"
              />
              <Field
                label="Problem *"
                name="problem"
                value={form.problem}
                onChange={v => set('problem', v)}
                multiline
                placeholder="What specific problem does this solve?"
              />
              <Field
                label="Solution *"
                name="solution"
                value={form.solution}
                onChange={v => set('solution', v)}
                multiline
                placeholder="How does your idea solve the problem?"
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <Field
                  label="Target Audience *"
                  name="target_audience"
                  value={form.target_audience}
                  onChange={v => set('target_audience', v)}
                  placeholder="Who are your customers?"
                />
                <Field
                  label="Business Model *"
                  name="business_model"
                  value={form.business_model}
                  onChange={v => set('business_model', v)}
                  placeholder="How do you make money?"
                />
              </div>
              <Field
                label="Tech Stack *"
                name="tech_stack"
                value={form.tech_stack}
                onChange={v => set('tech_stack', v)}
                placeholder="e.g. React, FastAPI, PostgreSQL, Stripe"
              />
              <TagField
                label="Key Features (optional)"
                values={form.key_features ?? []}
                onChange={v => set('key_features', v)}
                placeholder="Type a feature, press Enter"
              />
              <TagField
                label="Competitors (optional)"
                values={form.competitors ?? []}
                onChange={v => set('competitors', v)}
                placeholder="Type a competitor, press Enter"
              />

              {/* Submit */}
              <div className="flex items-center justify-between pt-2 border-t border-[var(--border)]">
                <p className="text-[11px] text-[var(--muted)]">
                  {submitting ? 'Judging your idea — this takes ~10 seconds…' : 'All three judges will score your idea.'}
                </p>
                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="flex items-center gap-2 px-5 py-2 rounded-lg bg-[var(--accent)] text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lightbulb className="w-4 h-4" />}
                  {submitting ? 'Judging…' : 'Submit Idea'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
