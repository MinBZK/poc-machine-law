# Stage 1: build the SvelteKit app
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


# Stage 2: serve the Python app including static files
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install the Dutch locale
RUN apt-get update && apt-get install -y locales locales-all

ADD . .

COPY --from=node_builder /analysis-laws/build analysis/laws/build
COPY --from=node_builder /analysis-graph/build analysis/graph/build
COPY --from=node_builder /importer/build importer/build

RUN uv sync --no-dev

CMD ["uv", "run", "--no-dev", "web/main.py"]

EXPOSE 8000
