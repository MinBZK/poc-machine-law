# Machine law importer

Helps to convert existing laws to machine readable YAML.


# Running locally

Installation:

```sh
cp .env.example .env  # And add values
uv venv
uv sync
```

Each time:

```sh
source .venv/bin/activate
uv run --env-file=.env main.py
```
