FROM alpine:latest as source

RUN apk add --no-cache git

COPY . /project
WORKDIR /project

# Remove git history and create a new commit
RUN rm -rvf .git && \
    git init && \
    git add . && \
    git config user.email "32300164+mnixry@users.noreply.github.com" && \
    git config user.name "Mix" && \
    git commit -m "Initial commit"

FROM python:bookworm

RUN mkdir -p /app/checkpoints && \
    useradd -s /bin/bash app && \
    useradd -s /bin/bash bot

WORKDIR /app
RUN cd ./checkpoints && \
    wget https://github.com/AUTOMATIC1111/TorchDeepDanbooru/releases/download/v1/model-resnet_custom_v3.pt

COPY --from=source /project /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install -e . && \
    chown -R app:app /app/checkpoints

RUN gcc ./readflag.c -o /readflag && \
    gcc ./restart.c -o /restart && \
    chown root:bot /readflag && \
    chown root:bot /restart && \
    chmod 4550 /readflag && \
    chmod 4550 /restart

ENV HOST=0.0.0.0 \
    PORT=8080 \
    COLUMNS=120

ENTRYPOINT ["/app/entrypoint.sh"]