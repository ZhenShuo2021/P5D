# Build stage
FROM python:3.10-alpine AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .
RUN apk add --no-cache build-base curl
RUN mkdir -p /usr/share/fonts/opentype/noto 
RUN curl -L -o /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc https://salsa.debian.org/fonts-team/fonts-noto-cjk/-/raw/debian/unstable/Sans/OTC/NotoSansCJK-Regular.ttc
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.10-alpine AS final
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/share/fonts/opentype/noto /usr/share/fonts/opentype/noto
RUN apk add --no-cache fontconfig libstdc++ rsync

VOLUME ["/mnt/local_folder", "/mnt/remote_folder"]
ENTRYPOINT ["python", "-m", "p5d"]