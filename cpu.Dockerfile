FROM python:3.10-slim-bookworm

RUN pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu --no-cache-dir

WORKDIR /opt/NekoImageGallery

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

VOLUME ["/opt/NekoImageGallery/static"]

ENV APP_CLIP__DEVICE="cpu"

LABEL org.opencontainers.image.authors="EdgeNeko" \
      org.opencontainers.image.url="https://github.com/hv0905/NekoImageGallery" \
      org.opencontainers.image.source="https://github.com/hv0905/NekoImageGallery"

ENTRYPOINT ["python", "main.py"]
