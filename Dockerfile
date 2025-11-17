## Build Stage 1: build the SvelteKit app
FROM node:24-alpine3.21 AS node_builder

# Install corepack and pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy and build analysis/laws
WORKDIR /analysis-laws
COPY analysis/laws/.eslintrc.cjs analysis/laws/.npmrc analysis/laws/.prettierrc analysis/laws/package.json analysis/laws/pnpm-lock.yaml analysis/laws/postcss.config.js analysis/laws/svelte.config.js analysis/laws/tailwind.config.js analysis/laws/tsconfig.json analysis/laws/vite.config.ts ./

RUN pnpm install

COPY analysis/laws/. .

RUN pnpm run build

# Copy and build analysis/graph
WORKDIR /analysis-graph
COPY analysis/graph/.eslintrc.cjs analysis/graph/.npmrc analysis/graph/.prettierrc analysis/graph/package.json analysis/graph/pnpm-lock.yaml analysis/graph/postcss.config.js analysis/graph/svelte.config.js analysis/graph/tailwind.config.js analysis/graph/tsconfig.json analysis/graph/vite.config.ts ./

RUN pnpm install

COPY analysis/graph/. .

RUN pnpm run build

# Copy and build importer
WORKDIR /importer
COPY importer/.eslintrc.cjs importer/.npmrc importer/.prettierrc importer/package.json importer/pnpm-lock.yaml importer/postcss.config.js importer/svelte.config.js importer/tailwind.config.js importer/tsconfig.json importer/vite.config.ts ./

RUN pnpm install

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
RUN npm ci && npm run build

# Collect all required wallet files into a single directory
WORKDIR /wallet-files
RUN cp /wallet/nl-wallet/wallet_core/demo/demo_utils/assets/css/button-reset.css . && \
    cp /wallet/nl-wallet/wallet_core/demo/demo_utils/assets/css/reset.css . && \
    cp /wallet/nl-wallet/wallet_core/demo/demo_index/assets/css/nav.css . && \
    cp /wallet/nl-wallet/wallet_core/demo/demo_utils/assets/css/common.css . && \
    cp /wallet/nl-wallet/wallet_core/demo/demo_utils/assets/css/page.css . && \
    cp /wallet/nl-wallet/wallet_core/demo/demo_utils/assets/css/buttons-after.css . && \
    cp /wallet/nl-wallet/wallet_web/dist/nl-wallet-web.iife.js .


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
