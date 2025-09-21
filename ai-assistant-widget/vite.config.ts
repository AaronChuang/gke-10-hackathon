import { defineConfig } from 'vite'
import preact from '@preact/preset-vite'

export default defineConfig({
  plugins: [preact()],
  build: {
    cssCodeSplit: false,
    minify: 'esbuild',
    rollupOptions: {
      output: {
        format: 'iife',
        name: 'AIAssistantWidget',
        manualChunks: undefined,
        entryFileNames: 'ai-assistant-widget.js',
        assetFileNames: 'ai-assistant-widget.[ext]',
        inlineDynamicImports: true,
      },
      external: [],
    },
    target: 'es2015',
    outDir: 'dist',
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
})