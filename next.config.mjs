/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV === "development";

const nextConfig = {
  // Keep dev and production build artifacts separate to avoid missing-chunk
  // errors when `next dev` and `next build` are run in the same workspace.
  distDir: isDev ? ".next-dev" : ".next-build",
  ...(isDev ? {} : { output: "export" }),
  images: {
    unoptimized: true,
  },
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;
