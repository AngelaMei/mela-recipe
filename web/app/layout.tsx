import type { Metadata, Viewport } from "next";

import "../styles.css";

import { PREFS_BOOT_SCRIPT } from "@/lib/prefs";

import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Mela",
  description: "Our kitchen: recipes, cook log and a shared grocery list.",
  applicationName: "Mela",
  appleWebApp: { capable: true, title: "Mela", statusBarStyle: "default" },
  icons: {
    icon: [{ url: "/icon.svg", type: "image/svg+xml" }],
    apple: [{ url: "/apple-touch-icon.png" }],
  },
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#fbf7ef",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="light" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: PREFS_BOOT_SCRIPT }} />
      </head>
      <body>
        <Providers>
          <div className="app">{children}</div>
        </Providers>
      </body>
    </html>
  );
}
