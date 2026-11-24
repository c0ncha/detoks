import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // E2E tests run their own dev server next to yours; a separate build dir keeps them from colliding.
  distDir: process.env.NEXT_DIST_DIR || ".next",
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
