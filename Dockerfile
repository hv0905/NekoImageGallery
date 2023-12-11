FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime

WORKDIR /opt/NekoImageGallery

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

VOLUME ["/opt/NekoImageGallery/static"]

LABEL org.opencontainers.image.authors="EdgeNeko" \
      org.opencontainers.image.url="https://github.com/hv0905/NekoImageGallery" \
      org.opencontainers.image.source="https://github.com/hv0905/NekoImageGallery" \
      org.opencontainers.image.title="NekoImageGallery" \
      org.opencontainers.image.description="An AI-powered natural language & reverse Image Search Engine powered by CLIP & qdrant."

ENTRYPOINT ["python", "main.py"]