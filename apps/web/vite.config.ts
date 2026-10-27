import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const testPort = Number(process.env.PHASE1_E2E_API_PORT ?? '18000');
if (!Number.isInteger(testPort) || testPort < 1024 || testPort > 65535) {
  throw new Error('A non-privileged local API port is required');
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: Object.fromEntries(
      ['/api', '/health', '/docs', '/openapi.json'].map((route) => [
        route,
        { target: `http://127.0.0.1:${testPort}`, changeOrigin: false },
      ]),
    ),
  },
});
