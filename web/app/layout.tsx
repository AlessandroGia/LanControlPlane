import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LAN Control Plane",
  description: "Host control dashboard for LAN Control Plane",
  applicationName: "LAN Control Plane",
};

export const viewport: Viewport = {
  themeColor: "#0b1020",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}