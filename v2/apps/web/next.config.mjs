/**
 * Static export, deployed to GitHub Pages beside v1.
 *
 * v2 has no server-only features yet — every route is statically generated and lib/seed.ts is read
 * at build time — so it can ship on the same infrastructure v1 already uses. That removes the
 * deployment blocker entirely: no Vercel account needed until Phase 10 actually requires a server
 * (accounts, email, saved places), at which point this config changes and nothing else does.
 *
 * basePath keeps it at /on-record/preview so v1 stays live at the root and the two can be compared
 * by the same test users, on the same phones, on the same day.
 */
const BASE = "/on-record/preview";
/** @type {import('next').NextConfig} */
export default {
  output: "export",
  basePath: BASE,
  assetPrefix: BASE,
  trailingSlash: true,
  images: { unoptimized: true },   // no image optimiser on a static host
  reactStrictMode: true,
};
