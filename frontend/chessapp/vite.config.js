import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: [
        'node_modules/',
        'src/index.jsx',
        'src/reportWebVitals.js',
        'src/App.backup.jsx',
        'src/pages/Callback.jsx',
        'src/pages/IotDashboard.jsx',
        'src/pages/Login.jsx',
        '**/pages/AngrinessPredictor.jsx',
        '**/pages/EnvironmentRecommendation.jsx',
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 70,
      },
    },
  },
})
