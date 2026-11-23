FROM ghcr.io/allenai/cuda:12.0-dev-ubuntu20.04-v1.2.134 AS base

# Env variables
ENV PROJECT_DIR=/root/web-trajectory-scraper
ENV WANDB_DIR=/root/wandb
ENV UV_PROJECT_ENVIRONMENT=/root/.uv_venvs/web-trajectory-scraper
ENV UV=/root/.local/bin/uv

# Set workdir
WORKDIR $PROJECT_DIR

# Setup uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
COPY pyproject.toml uv.lock ./
COPY .python-version .
RUN $UV sync && $UV run playwright install --with-deps chromium
RUN $UV run python -c 'print("uv setup complete!")'
RUN $UV run python -c 'import nltk; nltk.download("punkt_tab")'
RUN mkdir -p $WANDB_DIR
RUN cp uv.lock /root/uv.lock
ENV PYTHON=/root/.uv_venvs/web-trajectory-scraper/bin/python


ENTRYPOINT ["bash", "-l"]
