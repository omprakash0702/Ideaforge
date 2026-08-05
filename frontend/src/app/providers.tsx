'use client'

import { ThemeProvider } from 'next-themes'
import { Toaster } from 'react-hot-toast'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      themes={['dark', 'black']}
      defaultTheme="dark"
      enableSystem={false}
      disableTransitionOnChange={false}
    >
      {children}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: 'var(--surface)',
            color: 'var(--text)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
          },
          success: { iconTheme: { primary: '#22C55E', secondary: 'var(--surface)' } },
          error:   { iconTheme: { primary: '#EF4444', secondary: 'var(--surface)' } },
        }}
      />
    </ThemeProvider>
  )
}
