# Graph analysis

![Screenshot](static/img/screenshot.png)

## Developing

Install the dependencies once with `pnpm install`. Then, start a development server:

```sh
pnpm dev
```

(However, this will be broken due to the Python backend not serving from the same domain.)

## Building

Should be built using Docker, e.g.:

```sh
docker build -t poc-machine-law .
docker run --rm -p8000:8000 poc-machine-law
```

The graph is then available under http://localhost:8000/analysis/graph/

## Building (alternatively)

```sh
cd analysis/graph
pnpm install
pnpm build
cd ../..
source .venv/bin/activate
uv run web/main.py
```

The graph is then also available under http://localhost:8000/analysis/graph/
