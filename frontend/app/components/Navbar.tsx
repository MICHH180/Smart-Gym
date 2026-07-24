"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { cerrarSesion, getUsuarioActual, type Usuario } from "../lib/api";

const NAV_LINKS = [
  { href: "/", label: "Inicio" },
  { href: "/#ejercicios", label: "Ejercicios" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [checkingSesion, setCheckingSesion] = useState(true);

  useEffect(() => {
    getUsuarioActual()
      .then(setUsuario)
      .finally(() => setCheckingSesion(false));
  }, []);

  async function handleLogout() {
    await cerrarSesion();
    setUsuario(null);
    setMenuOpen(false);
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-brand text-black">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2.5}
              className="h-4.5 w-4.5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.5 6.5 v11 M17.5 6.5 v11 M2 9v6 M22 9v6 M6.5 12h11" />
            </svg>
          </span>
          <span className="font-display text-lg font-semibold tracking-tight text-foreground">
            SMART<span className="text-brand">-GYM</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-muted transition hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          {!checkingSesion && (
            <div className="hidden sm:flex sm:items-center sm:gap-3">
              {usuario ? (
                <>
                  <span className="text-sm text-muted">
                    Hola, <span className="text-foreground">{usuario.nombre.split(" ")[0]}</span>
                  </span>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-surface"
                  >
                    Cerrar sesión
                  </button>
                </>
              ) : (
                <Link
                  href="/login"
                  className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-black transition hover:bg-brand-dark"
                >
                  Iniciar sesión
                </Link>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Abrir menú"
            aria-expanded={menuOpen}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border text-foreground md:hidden"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              className="h-5 w-5"
            >
              {menuOpen ? (
                <path strokeLinecap="round" d="M6 6l12 12M18 6L6 18" />
              ) : (
                <path strokeLinecap="round" d="M4 7h16M4 12h16M4 17h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className="border-t border-border bg-background px-4 py-4 md:hidden">
          <nav className="flex flex-col gap-4">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMenuOpen(false)}
                className="text-sm font-medium text-muted transition hover:text-foreground"
              >
                {link.label}
              </Link>
            ))}

            {usuario ? (
              <>
                <span className="text-sm text-muted">
                  Hola, <span className="text-foreground">{usuario.nombre.split(" ")[0]}</span>
                </span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-lg border border-border px-4 py-2 text-center text-sm font-semibold text-foreground transition hover:bg-surface"
                >
                  Cerrar sesión
                </button>
              </>
            ) : (
              <Link
                href="/login"
                onClick={() => setMenuOpen(false)}
                className="rounded-lg bg-brand px-4 py-2 text-center text-sm font-semibold text-black transition hover:bg-brand-dark"
              >
                Iniciar sesión
              </Link>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
