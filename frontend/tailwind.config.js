/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#080908',
        surface: {
          DEFAULT: '#111311',
          2: '#171A17',
          3: '#1E231E',
        },
        cream: {
          DEFAULT: '#F3EBDD',
          muted: '#C9C2B5',
          dark: '#9E978B',
        },
        forest: {
          DEFAULT: '#123B2A',
          light: '#1C563E',
          accent: '#297A59',
          glow: 'rgba(28, 86, 62, 0.4)',
        },
        magenta: {
          DEFAULT: '#B45A7A',
          glow: 'rgba(180, 90, 122, 0.35)',
        },
        muted: '#858983',
        border: 'rgba(243, 235, 221, 0.14)',
        borderStrong: 'rgba(243, 235, 221, 0.28)',
        success: '#A8D5BA',
        warning: '#D9C48A',
        danger: '#D58A8A',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        display: ['Silkscreen', 'Space Grotesk', 'monospace'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      letterSpacing: {
        tighter: '-0.04em',
        tight: '-0.02em',
        widest: '0.18em',
      },
      animation: {
        'breathe': 'breathe 4s ease-in-out infinite',
        'pulse-subtle': 'pulseSubtle 2.5s ease-in-out infinite',
      },
      keyframes: {
        breathe: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.9' },
          '50%': { transform: 'scale(1.03)', opacity: '1' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        }
      }
    },
  },
  plugins: [],
}
