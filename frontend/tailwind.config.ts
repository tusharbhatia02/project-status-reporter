// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}', // If using App Router structure
  ],
  theme: {
    extend: {
      // Add custom theme extensions if needed
    },
  },
  plugins: [
    require('@tailwindcss/typography'), // <-- Add this line
  ],
}
export default config