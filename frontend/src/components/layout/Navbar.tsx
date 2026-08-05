'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { Flame, LayoutDashboard, Plus, LogOut } from 'lucide-react'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { useUser } from '@/hooks/useUser'
import { cn } from '@/lib/utils'

const navLinks = [
  { href: '/projects',     label: 'Projects',    icon: LayoutDashboard },
  { href: '/projects/new', label: 'New Project',  icon: Plus },
]

export function Navbar() {
  const pathname = usePathname()
  const { user, logout } = useUser()

  return (
    <motion.header
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="sticky top-0 z-50 border-b border-[var(--border)] backdrop-blur-md"
      style={{ background: 'rgba(var(--bg-rgb, 14,14,18), 0.85)' }}
    >
      <nav className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between gap-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <Flame className="w-5 h-5 text-[var(--accent)] group-hover:scale-110 transition-transform" />
          <span className="font-cinzel font-bold text-sm tracking-[0.2em] text-white">
            IDEAFORGE
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {navLinks.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + '/')
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                  active
                    ? 'bg-[var(--accent)] text-white'
                    : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface)]',
                )}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </Link>
            )
          })}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          <ThemeToggle />
          {user && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-[var(--muted)] max-w-[120px] truncate">
                {user.name}
              </span>
              <button
                onClick={logout}
                className="p-1.5 rounded-lg text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface)] transition-colors"
                title="Sign out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </nav>
    </motion.header>
  )
}
