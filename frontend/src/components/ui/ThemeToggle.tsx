'use client'

import { useTheme } from 'next-themes'
import { useEffect, useState } from 'react'
import { Moon, Circle } from 'lucide-react'
import { cn } from '@/lib/utils'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])
  if (!mounted) return <div className="w-20 h-8" />

  const isDark = theme === 'dark'

  return (
    <button
      onClick={() => setTheme(isDark ? 'black' : 'dark')}
      className={cn(
        'flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-all duration-300',
        'border-[var(--border)] text-[var(--muted)] hover:text-[var(--text)] hover:border-[var(--accent)]',
      )}
      title={`Switch to ${isDark ? 'black' : 'dark'} mode`}
    >
      {isDark ? (
        <>
          <Circle className="w-3 h-3 fill-current" />
          <span>DARK</span>
        </>
      ) : (
        <>
          <Moon className="w-3 h-3 fill-current" />
          <span>BLACK</span>
        </>
      )}
    </button>
  )
}
