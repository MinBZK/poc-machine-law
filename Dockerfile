FROM ghcr.io/astral-sh/uv:python3.13-alpine

ADD . .

RUN uv sync

CMD ["uv", "run", "web/main.py"]

EXPOSE 8000
