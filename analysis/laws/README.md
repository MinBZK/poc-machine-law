# Law Analysis Tool

This Svelte-based web application provides a detailed view and analysis of Dutch laws and their relationships. It's part of the larger Machine Law PoC, focusing on making legal texts more accessible and understandable.

## Features

### Law Inspection
- Detailed view of individual laws
- View law metadata and properties

### Law Details
- Shows law dependencies and relationships
- Displays input and output parameters
- Lists source references
- Indicates connections to other laws

## Technical Details

- Built with SvelteKit
- Uses Tailwind CSS for styling
- Fetches law data from FastAPI backend
- Provides SPA (Single Page Application) functionality

## Development

To run the project locally:

```sh
cd analysis/laws
pnpm install
pnpm run dev
```

To build for production:

```sh
pnpm run build
```

The built files will be served by the FastAPI backend under the `analysis/laws` path.

Or build the project using Docker, e.g. in the repo root:

```sh
docker build -t poc-machine-law .
docker run --rm -p8000:8000 poc-machine-law
```
