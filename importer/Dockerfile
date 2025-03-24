# Stage 1
FROM digilabpublic.azurecr.io/node:23-alpine3.19 AS node_builder

RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy the code into the container. Note: copy to a dir instead of `.`, since Parcel cannot run in the root dir, see https://github.com/parcel-bundler/parcel/issues/6578
WORKDIR /build
COPY .eslintrc.cjs .npmrc .prettierrc package.json pnpm-lock.yaml postcss.config.js svelte.config.js tailwind.config.js tsconfig.json vite.config.ts ./

RUN pnpm install

COPY . .

RUN pnpm run build


# Stage 2
FROM digilabpublic.azurecr.io/nginx:1.25.3-alpine3.18

RUN apk add --no-cache tzdata

COPY --from=node_builder /build/build /usr/share/nginx/html

COPY nginx-default.conf /etc/nginx/conf.d/default.conf

# Build the static files
EXPOSE 80
