FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ADD . .

RUN uv sync --no-dev

CMD ["uv", "run", "--no-dev", "web/main.py"]

EXPOSE 8000
