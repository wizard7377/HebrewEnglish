# Davar as a container: build with `docker build -f dockerfile -t davar .`, run with `docker run -p 8080:8080 davar`.
# Debian rather than Alpine, since numpy and tokenizers ship prebuilt wheels for glibc but would compile on musl.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# No development dependencies, compiled bytecode for a faster start, and copies rather than links from uv's cache
ENV UV_NO_DEV=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HF_HOME=/opt/huggingface

WORKDIR /app

# Dependencies first, so that a change to the code alone reuses this layer
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# The embedding model is fetched now, so the container starts without reaching Hugging Face
# and readable by the unprivileged user it runs as
RUN .venv/bin/python -c "from model2vec import StaticModel; StaticModel.from_pretrained('minishlab/potion-base-32M')" \
    && chmod -R a+rX "$HF_HOME"

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Run as an unprivileged user; uid 1000 is also what Hugging Face Spaces expects
RUN useradd --create-home --uid 1000 davar
USER davar

# Hosts such as Render and Cloud Run choose the port through PORT
ENV PATH="/app/.venv/bin:$PATH" \
    HF_HUB_OFFLINE=1 \
    PORT=8080
EXPOSE 8080

CMD ["hebrewenglish", "--no-show"]
