"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Home" },
  { href: "/about", label: "About Hogwarts" },
  { href: "/houses", label: "Houses" },
  { href: "/admissions", label: "Admissions" },
  { href: "/faculty", label: "Faculty" },
  { href: "/contact", label: "Contact" },
];

export function Navbar() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-50 backdrop-blur-md border-b border-border">
      <nav
        aria-label="Primary"
        className="mx-auto max-w-6xl px-4 md:px-6 py-3 flex items-center justify-between"
      >
        <Link href="/" className="flex items-center gap-2 group">
          <span className="h-6 w-6 rounded-full gold-glow" aria-hidden />
          <span className="font-serif text-lg md:text-xl tracking-wide">
            Hogwarts
          </span>
        </Link>
        <ul className="hidden md:flex items-center gap-4">
          {links.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className={cn(
                  "px-3 py-1.5 rounded-md transition-colors",
                  pathname === l.href
                    ? "bg-secondary/20 text-foreground"
                    : "hover:bg-secondary/15 hover:text-foreground/90"
                )}
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
