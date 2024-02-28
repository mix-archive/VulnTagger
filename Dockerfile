FROM python:bookworm

RUN mkdir -p /app/checkpoints && \
    useradd -s /bin/bash app && \
    useradd -s /bin/bash bot

WORKDIR /app
RUN cd ./checkpoints && \
    wget https://github.com/AUTOMATIC1111/TorchDeepDanbooru/releases/download/v1/model-resnet_custom_v3.pt

COPY . /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install -e . && \
    chown -R app:app /app/checkpoints

ENV HOST=0.0.0.0 \
    PORT=8080

ENTRYPOINT ["/app/entrypoint.sh"]