/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Material 3 Dark Palette (Google AI Studio inspired)
                surface: {
                    DEFAULT: '#131314', // Main background
                    container: '#1E1F20', // Cards, Sidebars
                    raised: '#28292A', // Modals, Dropdowns
                    'raised-high': '#3C4043',
                    overlay: '#3C4043', // Alias for backward compatibility
                    border: '#444746', // Dividers
                },
                primary: {
                    DEFAULT: '#A8C7FA', // M3 Blue 80
                    hover: '#D3E3FD',
                    dim: '#669DF6',
                },
                secondary: {
                    DEFAULT: '#E3E3E3',
                    muted: '#C4C7C5',
                    dim: '#8E918F',
                },
                accent: {
                    DEFAULT: '#0B57D0', // Google Blue
                    glow: '#A8C7FA',
                },
                status: {
                    success: '#A8DAB5', // Green 80
                    error: '#F2B8B5',   // Red 80
                    warning: '#F7C67F', // Yellow 80
                    info: '#A8C7FA',    // Blue 80
                },
                text: {
                    primary: '#E3E3E3',
                    secondary: '#C4C7C5',
                    muted: '#8E918F', // Variant
                    inverse: '#1F1F1F',
                }
            },
            fontFamily: {
                sans: ['Inter', 'Roboto', 'sans-serif'],
                mono: ['"JetBrains Mono"', 'monospace'],
            },
            boxShadow: {
                'elevation-1': '0 1px 2px 0 rgba(0, 0, 0, 0.3), 0 1px 3px 1px rgba(0, 0, 0, 0.15)',
                'elevation-2': '0 1px 2px 0 rgba(0, 0, 0, 0.3), 0 2px 6px 2px rgba(0, 0, 0, 0.15)',
                'elevation-3': '0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 4px 8px 3px rgba(0, 0, 0, 0.15)',
                'glow': '0 0 15px rgba(168, 199, 250, 0.15)',
            },
            animation: {
                'fade-in': 'fadeIn 0.2s ease-out',
                'slide-up': 'slideUp 0.3s cubic-bezier(0.2, 0.0, 0, 1.0)',
                'scale-in': 'scaleIn 0.2s cubic-bezier(0.2, 0.0, 0, 1.0)',
                'pulse-slow': 'pulse 3s infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(10px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                scaleIn: {
                    '0%': { transform: 'scale(0.95)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                }
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'subtle-glow': 'radial-gradient(circle at center, var(--tw-gradient-stops))',
            }
        },
    },
    plugins: [],
}
