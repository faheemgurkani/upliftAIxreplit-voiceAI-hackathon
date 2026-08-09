#!/usr/bin/env node
/**
 * Cross-platform guard: this workspace must be installed with pnpm.
 * Replaces the previous bash-only preinstall hook (broke on Windows).
 */
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
for (const name of ["package-lock.json", "yarn.lock"]) {
  const p = path.join(root, name);
  try {
    if (fs.existsSync(p)) fs.unlinkSync(p);
  } catch {
    // ignore
  }
}

const ua = process.env.npm_config_user_agent || "";
if (!ua.includes("pnpm")) {
  console.error("Use pnpm instead of npm/yarn for the frontend workspace.");
  console.error("  npm i -g pnpm   # or: corepack enable && corepack prepare pnpm@latest --activate");
  process.exit(1);
}
