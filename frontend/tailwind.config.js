/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './views/**/*.ejs',
    './public/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        // Palette moderne glassmorphism
        primary: {
          50: '#F0FDFA',
          100: '#CCFBF1',
          200: '#99F6E4',
          300: '#5EEAD4',
          400: '#2DD4BF',
          500: '#14B8A6',  // Teal - couleur principale
          600: '#0D9488',
          700: '#0F766E',
          800: '#115E59',
          900: '#134E4A',
        },
        navy: {
          50: '#F8FAFC',
          100: '#F1F5F9',
          200: '#E2E8F0',
          300: '#CBD5E1',
          400: '#94A3B8',
          500: '#64748B',
          600: '#475569',
          700: '#334155',
          800: '#1E293B',
          900: '#0F172A',
        },
        // Tags métier
        tag: {
          iard: '#F97316',     // Orange
          sante: '#14B8A6',    // Teal
          vie: '#3B82F6',      // Bleu
          glm: '#8B5CF6',      // Violet
          pricing: '#8B5CF6',  // Violet
          reserving: '#06B6D4', // Cyan
          fraude: '#EF4444',   // Rouge
          ml: '#EC4899',       // Pink
        },
        // Sources
        kaggle: '#20BEFF',
        insee: '#E63946',
        opendata: '#14B8A6',
        // Score gradient
        score: {
          low: '#EF4444',
          mid: '#EAB308',
          high: '#14B8A6',
        },
        // Glass colors
        glass: {
          white: 'rgba(255, 255, 255, 0.85)',
          dark: 'rgba(15, 23, 42, 0.85)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
        'glass-lg': '0 25px 50px -12px rgba(31, 38, 135, 0.25)',
        'card': '0 4px 20px -2px rgba(0, 0, 0, 0.1)',
        'card-hover': '0 20px 40px -8px rgba(0, 0, 0, 0.15)',
        'sidebar': '4px 0 24px -2px rgba(0, 0, 0, 0.1)',
      },
      backdropBlur: {
        'glass': '16px',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'mesh-gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
      },
    },
  },
  plugins: [],
}
