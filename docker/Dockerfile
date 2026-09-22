# SPDX-License-Identifier: MIT
FROM python:3.12-slim-bookworm

# libportaudio2 é exigida pelo sounddevice (áudio vem depois)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libportaudio2 alsa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
