// static/js/styles.js
tailwind.config = {
    theme: {
        extend: {
            colors: {
                'spad': {
                    // Couleurs primaires SPAD
                    'primary': '#5CC3D2',     // Turquoise principal
                    'secondary': '#0C8C6B',   // Vert secondaire
                    'accent': '#1C6AB4',      // Bleu d'accent

                    // Nuances pour le turquoise
                    50: '#f0f9fa',
                    100: '#e0f2f5',
                    200: '#bae6ec',
                    300: '#7dd3e2',
                    400: '#5cc3d2',
                    500: '#3fb3c5',
                    600: '#2a9fb3',
                    700: '#1f8a9c',
                    800: '#176e7d',
                    900: '#0f525d',
                },
                'spad-green': {
                    // Nuances pour le vert SPAD
                    50: '#f0f8f5',
                    100: '#d9f0e9',
                    200: '#a8e1cd',
                    300: '#6dcead',
                    400: '#0c8c6b',
                    500: '#0a7a5e',
                    600: '#08684f',
                    700: '#065641',
                    800: '#044433',
                    900: '#023226',
                },
                'spad-blue': {
                    // Nuances pour le bleu SPAD
                    50: '#f0f7ff',
                    100: '#e0effe',
                    200: '#bad8fd',
                    300: '#7db9fc',
                    400: '#1c6ab4',
                    500: '#185d9e',
                    600: '#145088',
                    700: '#104372',
                    800: '#0c365c',
                    900: '#082946',
                },
                'health': {
                    'good': '#0C8C6B',      // Utilise le vert SPAD pour la santé bonne
                    'warning': '#f59e0b',
                    'critical': '#ef4444',
                }
            },
            fontFamily: {
                'sans': ['Inter', 'system-ui', 'sans-serif'],
                'display': ['Montserrat', 'sans-serif'],
            },
            transitionProperty: {
                'colors': 'background-color, border-color, color, fill, stroke',
            }
        }
    },
    plugins: [
        function ({ addUtilities }) {
            addUtilities({
                '.transition-colors': {
                    'transition-property': 'background-color, border-color, color, fill, stroke',
                    'transition-timing-function': 'cubic-bezier(0.4, 0, 0.2, 1)',
                    'transition-duration': '200ms',
                }
            })
        }
    ]
}