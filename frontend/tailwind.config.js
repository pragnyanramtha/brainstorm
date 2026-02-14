/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Professional Enterprise Palette
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                surface: {
                    DEFAULT: '#ffffff',
                    container: '#f8fafc', // Slate 50
                    raised: '#f1f5f9',    // Slate 100
                    'raised-high': '#e2e8f0', // Slate 200
                    border: '#e2e8f0',     // Slate 200
                    overlay: '#f1f5f9',    // Slate 100 - same as raised for overlay effect
                },
                primary: {
                    DEFAULT: '#0f172a', // Slate 900
                    foreground: '#f8fafc',
                    hover: '#1e293b',   // Slate 800
                },
                secondary: {
                    DEFAULT: '#64748b', // Slate 500
                    muted: '#94a3b8',   // Slate 400
                    foreground: '#0f172a',
                },
                accent: {
                    DEFAULT: '#2563eb', // Blue 600
                    foreground: '#ffffff',
                    muted: '#dbeafe',    // Blue 100
                },
                status: {
                    success: '#10b981', // Emerald 500
                    error: '#ef4444',   // Red 500
                    warning: '#f59e0b', // Amber 500
                    info: '#3b82f6',    // Blue 500
                },
                text: {
                    primary: '#0f172a',   // Slate 900
                    secondary: '#475569', // Slate 600
                    muted: '#64748b',     // Slate 500
                    inverse: '#ffffff',
                }
            },
            fontFamily: {
                sans: ['"Inter"', 'system-ui', 'sans-serif'],
                mono: ['"JetBrains Mono"', 'monospace'],
            },
            boxShadow: {
                'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                'DEFAULT': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
                'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                'elevation-1': '0 1px 3px rgba(0,0,0,0.1)',
                'elevation-2': '0 4px 6px rgba(0,0,0,0.05)',
                'elevation-3': '0 10px 15px rgba(0,0,0,0.05)',
            },
            animation: {
                'fade-in': 'fadeIn 0.2s ease-out',
                'slide-up': 'slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                'scale-in': 'scaleIn 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(8px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                scaleIn: {
                    '0%': { transform: 'scale(0.98)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                }
            },
        },
    },
    plugins: [],
}

