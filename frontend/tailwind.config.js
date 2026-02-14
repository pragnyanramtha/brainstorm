darkMode: 'class',
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
                DEFAULT: "hsl(var(--surface))",
                    container: "hsl(var(--surface-container))",
                        raised: "hsl(var(--surface-raised))",
                            'raised-high': "hsl(var(--surface-raised-high))",
                                border: "hsl(var(--border))",
                                    overlay: "hsl(var(--surface-overlay))",
                },
            primary: {
                DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                        hover: "hsl(var(--primary-hover))",
                },
            secondary: {
                DEFAULT: "hsl(var(--secondary))",
                    muted: "hsl(var(--secondary-muted))",
                        foreground: "hsl(var(--secondary-foreground))",
                },
            accent: {
                DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))",
                        muted: "hsl(var(--accent-muted))",
                },
            status: {
                success: "hsl(var(--success))",
                    error: "hsl(var(--error))",
                        warning: "hsl(var(--warning))",
                            info: "hsl(var(--info))",
                },
            text: {
                primary: "hsl(var(--foreground))",
                    secondary: "hsl(var(--muted-foreground))",
                        muted: "hsl(var(--muted-foreground))",
                            inverse: "hsl(var(--background))",
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

