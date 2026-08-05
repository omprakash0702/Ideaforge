import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        /* ── Godfather palette ─────────────────────────── */
        gf: {
          bg:       '#080505',
          deep:     '#050303',
          surface:  '#130A08',
          border:   '#3D1818',
          red:      '#C41E3A',
          'red-dk': '#8B1020',
          gold:     '#C9A84C',
          'gold-dk':'#8B7335',
          cream:    '#F5F0E8',
          ash:      '#9A8878',
        },
        /* ── Cinematic dark ────────────────────────────── */
        cinema: {
          bg:       '#0E0E12',
          surface:  '#16161E',
          elevated: '#1E1E28',
          border:   '#2E2E3E',
          accent:   '#7C5CFC',
          'accent-dk':'#5538C8',
          text:     '#E8E8F2',
          muted:    '#6868A0',
          success:  '#22C55E',
          warning:  '#F59E0B',
          error:    '#EF4444',
        },
        /* ── Black mode ────────────────────────────────── */
        void: {
          bg:      '#000000',
          surface: '#080808',
          elevated:'#101010',
          border:  '#1C1C1C',
        },
      },
      fontFamily: {
        serif:    ['var(--font-playfair)', 'Georgia', 'serif'],
        cinzel:   ['var(--font-cinzel)', 'Georgia', 'serif'],
        sans:     ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },
      animation: {
        'grain':       'grain 8s steps(10) infinite',
        'line-in':     'lineIn 0.8s ease-out forwards',
        'fade-up':     'fadeUp 0.6s ease-out forwards',
        'glow-pulse':  'glowPulse 3s ease-in-out infinite',
        'shimmer':     'shimmer 2.5s ease-in-out infinite',
        'scan':        'scan 0.6s ease-in-out',
      },
      keyframes: {
        grain: {
          '0%,100%': { transform: 'translate(0,0)' },
          '10%':     { transform: 'translate(-2%,-3%)' },
          '20%':     { transform: 'translate(3%, 2%)' },
          '30%':     { transform: 'translate(-1%, 4%)' },
          '40%':     { transform: 'translate(4%,-1%)' },
          '50%':     { transform: 'translate(-3%, 3%)' },
          '60%':     { transform: 'translate(2%,-4%)' },
          '70%':     { transform: 'translate(-4%, 2%)' },
          '80%':     { transform: 'translate(3%, 1%)' },
          '90%':     { transform: 'translate(-2%,-2%)' },
        },
        lineIn: {
          '0%':   { width: '0', opacity: '0' },
          '100%': { width: '100%', opacity: '1' },
        },
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glowPulse: {
          '0%,100%': { boxShadow: '0 0 20px rgba(196,30,58,0.3)' },
          '50%':     { boxShadow: '0 0 40px rgba(196,30,58,0.6)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
        scan: {
          '0%':   { left: '-100%' },
          '100%': { left: '200%' },
        },
      },
      backgroundImage: {
        'gold-shimmer': 'linear-gradient(90deg, #C9A84C, #F5DFA0, #C9A84C, #8B7335, #C9A84C)',
        'red-glow':     'radial-gradient(ellipse at center, rgba(196,30,58,0.15) 0%, transparent 70%)',
        'vignette':     'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.85) 100%)',
      },
    },
  },
  plugins: [],
}

export default config
