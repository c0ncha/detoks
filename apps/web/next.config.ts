import type { NextConfig } from "next";
import os from "node:os";

// This machine's LAN addresses, so phones on the same network can use the dev server (HMR included).
const lanAddresses = Object.values(os.networkInterfaces()).flat()
  .filter((a) => a && a.family === "IPv4" && !a.internal)
  .map((a) => a!.address);

const nextConfig: NextConfig = {
  // E2E tests run their own dev server next to yours; a separate build dir keeps them from colliding.
  distDir: process.env.NEXT_DIST_DIR || ".next",
  allowedDevOrigins: lanAddresses,
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
