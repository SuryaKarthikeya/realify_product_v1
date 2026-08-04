# Realify multi-channel prototype — production image.
# Matches the deployed image: python:3.12-slim, init-then-start, DB on the mounted /data volume.
FROM python:3.12-slim

WORKDIR /app

# deps first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app code (.dockerignore keeps .env, *.db*, caches, .git out of the image)
COPY . .

# DB lives on the mounted volume, not in the image
ENV REALIFY_DB=/data/realify_mc.db
EXPOSE 8001

# create/migrate schema, then serve + run the background scheduler
CMD ["sh","-c","python3 run.py init && python3 run.py start"]
