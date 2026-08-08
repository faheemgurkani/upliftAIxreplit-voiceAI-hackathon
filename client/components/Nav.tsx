"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/demo", label: "Demo" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/clusters", label: "Clusters" },
];

export function Nav() {
  const pathname = usePathname();
  const isLanding = pathname === "/";

  return (
    <header
      className={`relative z-20 w-full ${
        isLanding ? "absolute top-0 left-0 right-0" : "border-b border-white/5"
      }`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 md:px-8">
        <Link
          href="/"
          className="font-display text-xl tracking-tight text-mist-50 transition-colors duration-300 hover:text-brass-300 md:text-2xl"
        >
          Gawah
        </Link>
        <nav className="flex items-center gap-1 sm:gap-2">
          {links.map((link) => {
            const active =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-2.5 py-1.5 text-sm transition-colors duration-300 sm:px-3 ${
                  active
                    ? "text-brass-300"
                    : "text-mist-200/70 hover:text-mist-50"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
