import type React from "react";
import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/site/navbar";
import { Footer } from "@/components/site/footer";
import { WandCursor } from "@/components/site/wand-cursor";
import { Suspense } from "react";

export const metadata: Metadata = {
  title: "Hogwarts School of Witchcraft and Wizardry",
  description: "The official Hogwarts student portal.",
  generator: "v0.app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark antialiased">
      <body className="font-sans bg-background text-foreground cursor-none">
        <Suspense fallback={null}>
          <Navbar />
          <main className="min-h-dvh">{children}</main>
          <Footer />
          <WandCursor />
        </Suspense>
      </body>
    </html>
  );
}
