# Stage 1
FROM digilabpublic.azurecr.io/node:23-alpine3.19 AS node_builder

RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy the code into the container. Note: copy to a dir instead of `.`, since Parcel cannot run in the root dir, see https://github.com/parcel-bundler/parcel/issues/6578
WORKDIR /build
COPY .eslintrc.cjs .npmrc .prettierrc package.json pnpm-lock.yaml postcss.config.js svelte.config.js tailwind.config.js tsconfig.json vite.config.ts ./

RUN pnpm install

COPY static static
COPY src src

# Build the static files
ENTRYPOINT sh -c 'pnpm run dev --host 0.0.0.0'
