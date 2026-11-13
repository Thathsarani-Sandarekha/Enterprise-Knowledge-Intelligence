import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Asteria | Hospitality Knowledge Intelligence",
  description: "A fictional hospitality architecture consultancy's private project knowledge workspace.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
