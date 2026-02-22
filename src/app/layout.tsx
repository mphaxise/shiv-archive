import type { Metadata } from "next";
import articlesData from "@/data/articles.json";
import { SiteFooter } from "@/components/shared/SiteFooter";
import { DatasetPayload } from "@/lib/types";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shiv Archive",
  description:
    "Multi-source article archive for exploring Shiv Visvanathan's public writing and thematic shifts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const dataset = articlesData as DatasetPayload;

  return (
    <html lang="en">
      <body>
        {children}
        <div className="globalFooterShell">
          <SiteFooter generatedAtUtc={dataset.metadata.generated_at_utc} citationsLabel="Shiv Archive" />
        </div>
      </body>
    </html>
  );
}
