/** @type {import('next').NextConfig} */

// In Kubernetes the Ingress sends /api straight to FastAPI. This rewrite is the
// fallback (local dev, or clusters where you'd rather route everything via web).
// It is resolved at build time, so set API_INTERNAL_URL as a build arg if needed.
const apiUrl = process.env.API_INTERNAL_URL || "http://mela-api:8000";

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/api/:path*` }];
  },
};

export default nextConfig;
