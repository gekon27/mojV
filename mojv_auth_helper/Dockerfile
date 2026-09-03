FROM ghcr.io/home-assistant/base-python:3.13-alpine3.24

ARG BUILD_VERSION
ARG BUILD_ARCH

RUN apk add --no-cache \
      chromium \
      chromium-chromedriver \
      nss \
      freetype \
      harfbuzz \
      font-noto \
    && python3 -m pip install --no-cache-dir \
      aiohttp==3.12.15 \
      selenium==4.48.0

COPY rootfs /
RUN chmod a+x /etc/services.d/mojv-auth/run

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"
