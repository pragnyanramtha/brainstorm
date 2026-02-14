/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Base - Zinc 950/900
                surface: {
                    DEFAULT: '#09090b', // zinc-950
                    raised: '#18181b',  // zinc-900
                    overlay: '#27272a', // zinc-800
                    border: '#27272a',  // zinc-800
                    hover: '#27272a',   // zinc-800
                },
                // Accent - Blue 600/500
                accent: {
                    DEFAULT: '#2563eb', // blue-600
                    hover: '#1d4ed8',   // blue-700
                    muted: '#1e40af',   // blue-800
                    subtle: 'rgba(37, 99, 235, 0.1)',
                },
                // Text - Zinc 50/400
                text: {
                    primary: '#fafafa',   // zinc-50
                    secondary: '#a1a1aa', // zinc-400
                    muted: '#71717a',     // zinc-500
                    inverse: '#09090b',   // zinc-950
                },
                // Status
                success: '#10b981', // emerald-500
                warning: '#f59e0b', // amber-500
                error: '#ef4444',   // red-500
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
            },
            animation: {
                'pulse-subtle': 'pulse-subtle 2s ease-in-out infinite',
                'slide-up': 'slide-up 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                'fade-in': 'fade-in 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                'scale-in': 'scale-in 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
            },
            keyframes: {
                'pulse-subtle': {
                    '0%, 100%': { opacity: '1' },
                    '50%': { opacity: '0.7' },
                },
                'slide-up': {
                    '0%': { transform: 'translateY(10px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                'fade-in': {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                'scale-in': {
                    '0%': { transform: 'scale(0.95)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                },
            },
            boxShadow: {
                'glow': '0 0 20px -5px rgba(37, 99, 235, 0.3)',
            },
        },
    },
    plugins: [],
}
