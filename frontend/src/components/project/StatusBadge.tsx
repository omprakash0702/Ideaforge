import { cn } from '@/lib/utils'
import type { ProjectStatus } from '@/lib/api'

const styles: Record<ProjectStatus, string> = {
  CREATED:    'bg-zinc-800 text-zinc-400 border-zinc-700',
  RUNNING:    'bg-blue-950 text-blue-400 border-blue-800',
  GENERATING: 'bg-violet-950 text-violet-400 border-violet-800',
  JUDGING:    'bg-amber-950 text-amber-400 border-amber-800',
  EVOLVING:   'bg-emerald-950 text-emerald-400 border-emerald-800',
  TOURNAMENT: 'bg-orange-950 text-orange-400 border-orange-800',
  REPORTING:  'bg-cyan-950 text-cyan-400 border-cyan-800',
  COMPLETED:  'bg-green-950 text-green-400 border-green-800',
  FAILED:     'bg-red-950 text-red-400 border-red-800',
}

const dots: Record<ProjectStatus, string> = {
  CREATED:    'bg-zinc-400',
  RUNNING:    'bg-blue-400',
  GENERATING: 'bg-violet-400 animate-pulse',
  JUDGING:    'bg-amber-400 animate-pulse',
  EVOLVING:   'bg-emerald-400 animate-pulse',
  TOURNAMENT: 'bg-orange-400 animate-pulse',
  REPORTING:  'bg-cyan-400 animate-pulse',
  COMPLETED:  'bg-green-400',
  FAILED:     'bg-red-400',
}

const labels: Record<ProjectStatus, string> = {
  CREATED:    'Created',
  RUNNING:    'Starting',
  GENERATING: 'Generating',
  JUDGING:    'Judging',
  EVOLVING:   'Evolving',
  TOURNAMENT: 'Tournament',
  REPORTING:  'Reporting',
  COMPLETED:  'Completed',
  FAILED:     'Failed',
}

interface Props {
  status: ProjectStatus
  size?: 'sm' | 'md'
}

export function StatusBadge({ status, size = 'md' }: Props) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 border rounded-full font-medium',
      styles[status],
      size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs',
    )}>
      <span className={cn('rounded-full', dots[status], size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2')} />
      {labels[status]}
    </span>
  )
}
