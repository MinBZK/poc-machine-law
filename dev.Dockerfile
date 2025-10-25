# Stage 1: build the SvelteKit apps (same as production but for dev)
FROM node:25-alpine3.21 AS node_builder

# Install corepack and pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

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


# Stage 2: Development Python app with hot reloading
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install system dependencies for development
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies including dev dependencies
RUN uv sync

# Copy the entire project

# Copy built SvelteKit static files from node_builder stage


COPY ./schema /app/web/schema
COPY ./law /app/web/law
COPY ./law /app/law
COPY ./law_mcp /app/law_mcp
COPY ./services /app/web/services
COPY ./machine /app/machine
COPY ./explain /app/explain
COPY ./web /app/web
COPY ./submodules/regelrecht-laws/script /app/script
COPY ./data /app/data

WORKDIR /app/web

COPY --from=node_builder /analysis-graph/build analysis/graph/build
COPY --from=node_builder /importer/build importer/build

# Expose the port
EXPOSE 8000

# Use uvicorn with hot reload for development
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
