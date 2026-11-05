import type { NextConfig } from "next";

// Static export: `next build` writes plain HTML/CSS/JS to ./out,
// which Azure Static Web Apps serves directly. All data is fetched
// in the browser from the Azure Function, so no Node server is needed.
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
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
