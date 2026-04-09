/**
 * Next.js configuration: proxy /api requests to the local FastAPI backend
 * so the frontend can call /api/* and the backend remains accessible.
 */
/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'http://127.0.0.1:8000/:path*' },
      { source: '/api', destination: 'http://127.0.0.1:8000/' },
    ];
  },
};
