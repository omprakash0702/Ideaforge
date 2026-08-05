'use client'

import { useState, useEffect, useRef } from 'react'
import { api, type Project, type ProjectStatus } from '@/lib/api'

const TERMINAL: ProjectStatus[] = ['COMPLETED', 'FAILED']
const POLL_MS = 3000

export function useProjectStatus(id: string, initialStatus: ProjectStatus) {
  const [project, setProject] = useState<Project | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const isTerminal = (status: ProjectStatus) => TERMINAL.includes(status)

  useEffect(() => {
    let current = initialStatus

    async function poll() {
      try {
        const data = await api.projects.get(id)
        setProject(data)
        current = data.status
        if (isTerminal(data.status) && timerRef.current) {
          clearInterval(timerRef.current)
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to fetch project')
        if (timerRef.current) clearInterval(timerRef.current)
      }
    }

    poll()

    if (!isTerminal(initialStatus)) {
      timerRef.current = setInterval(poll, POLL_MS)
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [id, initialStatus])

  return { project, error }
}

export const STATUS_LABELS: Record<ProjectStatus, string> = {
  CREATED:    'Created',
  RUNNING:    'Starting up',
  GENERATING: 'Generating ideas',
  JUDGING:    'Judging ideas',
  EVOLVING:   'Evolving top picks',
  TOURNAMENT: 'Running tournament',
  REPORTING:  'Writing report',
  COMPLETED:  'Completed',
  FAILED:     'Failed',
}

export const STATUS_ORDER: ProjectStatus[] = [
  'CREATED', 'RUNNING', 'GENERATING', 'JUDGING',
  'EVOLVING', 'TOURNAMENT', 'REPORTING', 'COMPLETED',
]
