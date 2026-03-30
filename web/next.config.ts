import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/auth/:path*",
        destination: "http://lan-control-plane-server:8000/auth/:path*",
      },
      {
        source: "/hosts/:path*",
        destination: "http://lan-control-plane-server:8000/hosts/:path*",
      },
      {
        source: "/jobs/:path*",
        destination: "http://lan-control-plane-server:8000/jobs/:path*",
      },
      {
        source: "/agents/:path*",
        destination: "http://lan-control-plane-server:8000/agents/:path*",
      },
      {
        source: "/metrics/:path*",
        destination: "http://lan-control-plane-server:8000/metrics/:path*",
      },
      {
        source: "/audit-logs",
        destination: "http://lan-control-plane-server:8000/audit-logs",
      },
      {
        source: "/ws/:path*",
        destination: "http://lan-control-plane-server:8000/ws/:path*",
      },
    ];
  },
};

export default nextConfig;
