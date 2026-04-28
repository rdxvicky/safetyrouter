// Sync the Next.js static export (out/) into ../docs/ for GitHub Pages.
// - Removes only files that came from a previous build (not user files like design.md)
// - Drops Next.js's internal .txt files that GitHub Pages doesn't need
// - Adds .nojekyll so GitHub Pages serves _next/ correctly

import { rm, mkdir, cp, readdir, stat, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const WEB = resolve(__dirname, "..");
const OUT = join(WEB, "out");
const DOCS = resolve(WEB, "..", "docs");

// Files/folders we own — built artifacts. Anything else in docs/ is preserved
// (CNAME, design.md, custom assets, etc.).
const BUILD_PATHS = [
  "_next",
  "_not-found",
  "404",
  "404.html",
  "index.html",
  ".nojekyll",
];

// Internal Next.js files that aren't needed for static hosting.
const SKIP_PATTERNS = [/^__next\..*\.txt$/, /^index\.txt$/];

async function rmIfExists(p) {
  if (existsSync(p)) await rm(p, { recursive: true, force: true });
}

async function syncDir(src, dest) {
  await mkdir(dest, { recursive: true });
  const entries = await readdir(src);
  for (const name of entries) {
    if (SKIP_PATTERNS.some((re) => re.test(name))) continue;
    const srcPath = join(src, name);
    const destPath = join(dest, name);
    const s = await stat(srcPath);
    if (s.isDirectory()) {
      await syncDir(srcPath, destPath);
    } else {
      await cp(srcPath, destPath);
    }
  }
}

async function main() {
  if (!existsSync(OUT)) {
    console.error("No out/ directory — did `next build` run?");
    process.exit(1);
  }
  await mkdir(DOCS, { recursive: true });

  // Remove only previous build artifacts; preserve anything else (e.g. design.md).
  for (const p of BUILD_PATHS) {
    await rmIfExists(join(DOCS, p));
  }

  await syncDir(OUT, DOCS);
  await writeFile(join(DOCS, ".nojekyll"), "");
  await rm(OUT, { recursive: true, force: true });
  console.log("✓ docs/ synced from out/");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
