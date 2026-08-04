## Build Stage 1: build the SvelteKit app
FROM node:24-alpine3.21 AS node_builder

RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy and build analysis/laws
WORKDIR /analysis-laws
COPY analysis/laws/.eslintrc.cjs analysis/laws/.npmrc analysis/laws/.prettierrc analysis/laws/package.json analysis/laws/pnpm-lock.yaml analysis/laws/postcss.config.js analysis/laws/svelte.config.js analysis/laws/tailwind.config.js analysis/laws/tsconfig.json analysis/laws/vite.config.ts ./

# --ignore-scripts on the pnpm installs is mostly about being explicit, and it
# also un-breaks this build. pnpm >= 10 already refuses dependency build
# scripts by default, and `corepack prepare pnpm@latest` has been resolving to
# such a version since June - which is why `docker-build` has failed on main
# since 2026-06-12 with ERR_PNPM_IGNORED_BUILDS on esbuild. That error is
# pnpm's "decide about this" gate, not a real need: esbuild's postinstall only
# hardlinks a CLI shim, and the binary that matters comes from the
# platform-specific optional dependency. We decide to skip it.
#
# Note the trade-off. This flag also silences the same gate for a future
# dependency that does need its build step. pnpm's in-repo alternatives
# (onlyBuiltDependencies / ignoredBuiltDependencies, in package.json or
# pnpm-workspace.yaml) would have been the better instrument, but neither
# satisfies strictDepBuilds in pnpm 11.20.0 - verified by hand; both still exit
# 1. Revisit when pnpm fixes that.
#
# The apps' own `prepare: svelte-kit sync` is not needed at install time: the
# SvelteKit vite plugin syncs during `pnpm run build`.
RUN pnpm install --ignore-scripts --package-import-method=hardlink

COPY analysis/laws/. .

RUN pnpm run build

# Copy and build analysis/graph
WORKDIR /analysis-graph
COPY analysis/graph/.eslintrc.cjs analysis/graph/.npmrc analysis/graph/.prettierrc analysis/graph/package.json analysis/graph/pnpm-lock.yaml analysis/graph/postcss.config.js analysis/graph/svelte.config.js analysis/graph/tailwind.config.js analysis/graph/tsconfig.json analysis/graph/vite.config.ts ./

RUN pnpm install --ignore-scripts --package-import-method=hardlink

COPY analysis/graph/. .

RUN pnpm run build

# Copy and build importer
WORKDIR /importer
COPY importer/.eslintrc.cjs importer/.npmrc importer/.prettierrc importer/package.json importer/pnpm-lock.yaml importer/postcss.config.js importer/svelte.config.js importer/tailwind.config.js importer/tsconfig.json importer/vite.config.ts ./

RUN pnpm install --ignore-scripts --package-import-method=hardlink

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
# --ignore-scripts: same reason as the pnpm installs above. wallet_web declares
# no prepare/postinstall of its own; `vite build` is all this stage needs.
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
