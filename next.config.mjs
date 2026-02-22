/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV === "development";

const nextConfig = {
  // Keep dev artifacts separate so local `next dev` and `next build` do not
  // stomp on each other; keep production on default export output (`out`).
  ...(isDev ? { distDir: ".next-dev" } : {}),
  output: "export",
  images: {
    unoptimized: true,
  },
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;
