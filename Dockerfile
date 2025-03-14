# Stage 1: build the SvelteKit app
FROM node:23-alpine3.21 AS node_builder

# Install corepack and pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy the code into the container

WORKDIR /build
COPY analysis/graph/.eslintrc.cjs analysis/graph/.npmrc analysis/graph/.prettierrc analysis/graph/package.json analysis/graph/pnpm-lock.yaml analysis/graph/postcss.config.js analysis/graph/svelte.config.js analysis/graph/tailwind.config.js analysis/graph/tsconfig.json analysis/graph/vite.config.ts ./

RUN pnpm install

COPY analysis/graph/. .

RUN pnpm run build


# Stage 2: serve the Python app including static files
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ADD . .

COPY --from=node_builder /build/build analysis/graph/build

RUN uv sync --no-dev

CMD ["uv", "run", "--no-dev", "web/main.py"]

EXPOSE 8000
