## Build Stage 1: build the SvelteKit app
FROM node:24-alpine3.21 AS node_builder

# pnpm is pinned rather than `pnpm@latest`: this stage runs in the job that
# pushes to GHCR with `packages: write` (.github/workflows/docker-build.yml),
# so the package manager is itself part of this image's supply chain and should
# not be whatever npm published most recently. `latest` also moved from pnpm 10
# to pnpm 11 on 2026-04-28 and broke this build from 2026-06-12 onwards (see
# below); pnpm 12 is already in beta. Nothing bumps this automatically -
# Dependabot's docker ecosystem only tracks FROM lines, and no other job runs
# pnpm - so bump it deliberately when you touch this file.
RUN corepack enable && corepack prepare pnpm@11.20.0 --activate

# Copy and build analysis/laws
WORKDIR /analysis-laws
COPY analysis/laws/.eslintrc.cjs analysis/laws/.npmrc analysis/laws/.prettierrc analysis/laws/package.json analysis/laws/pnpm-lock.yaml analysis/laws/postcss.config.js analysis/laws/svelte.config.js analysis/laws/tailwind.config.js analysis/laws/tsconfig.json analysis/laws/vite.config.ts ./

# Both flags below apply to all three pnpm installs in this stage.
#
# --ignore-scripts: a dependency's install script runs with the same GHCR-write
# token this job holds, which is exactly the path a hijacked npm package uses.
# Under the pinned pnpm 11 nothing would run one anyway - pnpm errors instead,
# see below - so the flag is here to record the decision explicitly, and to keep
# holding if a pnpm default changes, an `allowBuilds` entry appears, or an app
# moves back to npm. Nothing in these three apps needs one.
#
# --frozen-lockfile: `CI` is not set inside a Docker build, so pnpm does not
# freeze by default. Without it, package.json drifting from pnpm-lock.yaml
# makes pnpm re-resolve the semver ranges at build time and the lockfile's
# pinned versions are silently bypassed. The cost is that no pull request
# exercises this - docker-build runs only on push to main, plus manual
# dispatch - so a package.json/lockfile mismatch now fails the publish after
# merge rather than being absorbed. Keep pnpm-lock.yaml in the same commit as
# package.json.
#
# --ignore-scripts also un-breaks this build. pnpm 10 already declined to run
# dependency build scripts, but only warned about it and exited 0; pnpm 11
# (2026-04-28) flipped `strictDepBuilds` to true by default and made that
# warning a hard error, so the first push to main afterwards (2026-06-12)
# failed with ERR_PNPM_IGNORED_BUILDS on esbuild. That error is pnpm asking us
# to decide, not a build we actually need: esbuild's postinstall hardlinks the
# platform-specific optional dependency's native binary over its JS shim as a
# startup optimisation (and downloads that binary itself if the optional
# dependency is missing). Skipped, the shim resolves the same binary lazily at
# runtime. We decide to skip it.
#
# Note the trade-off: the flag also silences that gate for a future dependency
# that does need its build step. pnpm's instrument for that is `allowBuilds`, a
# package-pattern -> bool map; pnpm 11 removed onlyBuiltDependencies,
# ignoredBuiltDependencies and friends in its favour. `allowBuilds:
# {esbuild: false}` does satisfy the gate, but pnpm 11 no longer reads settings
# from package.json's `pnpm` field at all - only pnpm-workspace.yaml - so it
# would need a new pnpm-workspace.yaml per app plus an extra entry in each of
# the three COPY lists here. We keep the flag instead.
#
# The apps' own `prepare: svelte-kit sync` is not needed at install time: the
# SvelteKit vite plugin syncs during `pnpm run build`.
RUN pnpm install --ignore-scripts --frozen-lockfile --package-import-method=hardlink

COPY analysis/laws/. .

RUN pnpm run build

# Copy and build analysis/graph
WORKDIR /analysis-graph
COPY analysis/graph/.eslintrc.cjs analysis/graph/.npmrc analysis/graph/.prettierrc analysis/graph/package.json analysis/graph/pnpm-lock.yaml analysis/graph/postcss.config.js analysis/graph/svelte.config.js analysis/graph/tailwind.config.js analysis/graph/tsconfig.json analysis/graph/vite.config.ts ./

# --ignore-scripts, --frozen-lockfile: see the analysis/laws install above.
RUN pnpm install --ignore-scripts --frozen-lockfile --package-import-method=hardlink

COPY analysis/graph/. .

RUN pnpm run build

# Copy and build importer
WORKDIR /importer
COPY importer/.eslintrc.cjs importer/.npmrc importer/.prettierrc importer/package.json importer/pnpm-lock.yaml importer/postcss.config.js importer/svelte.config.js importer/tailwind.config.js importer/tsconfig.json importer/vite.config.ts ./

# --ignore-scripts, --frozen-lockfile: see the analysis/laws install above.
RUN pnpm install --ignore-scripts --frozen-lockfile --package-import-method=hardlink

COPY importer/. .

RUN pnpm run build


## Build Stage 2: build nl-wallet web assets
FROM node:24-alpine3.21 AS wallet_builder

# Copy nl-wallet submodule
WORKDIR /wallet
COPY wallet/nl-wallet ./nl-wallet

# Build wallet-web
WORKDIR /wallet/nl-wallet/wallet_web
ENV VITE_HELP_BASE_URL="https://example.com"
# --ignore-scripts: unlike pnpm, npm still runs *dependency* install scripts by
# default, so this is the one install here where the flag stops a dependency
# from executing - esbuild's postinstall did run and now won't. (In the pnpm
# stage pnpm 11 was already refusing those, and the flag only additionally
# suppresses the apps' own `prepare`.) At the pinned submodule commit wallet_web
# declares no install script of its own, and its only script-bearing
# dependencies are esbuild (see above) and fsevents (macOS-only, so never built
# here); `vite build` is all this stage needs.
# No --frozen-lockfile: `npm ci` already refuses to run if package.json and
# package-lock.json disagree.
RUN npm ci --ignore-scripts && npm run build

# Collect all required wallet files into a single directory
WORKDIR /wallet-files
RUN cp /wallet/nl-wallet/wallet_web/dist/nl-wallet-web.iife.js .


## Release stage: serve the Python app including static files
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS release

# Install the Dutch locale
RUN apt-get update && apt-get install -y locales locales-all

COPY --from=node_builder /analysis-laws/build analysis/laws/build
COPY --from=node_builder /analysis-graph/build analysis/graph/build
COPY --from=node_builder /importer/build importer/build
COPY --from=wallet_builder /wallet-files nl-wallet-files

ADD . .

RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "web/main.py"]
