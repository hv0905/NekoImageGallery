FROM python:3.11-slim-bookworm

RUN PYTHONDONTWRITEBYTECODE=1 pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu --no-cache-dir

WORKDIR /opt/NekoImageGallery

COPY requirements.txt .

RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /opt/models && \
    export PYTHONDONTWRITEBYTECODE=1 && \
    huggingface-cli download openai/clip-vit-large-patch14 'model.safetensors' '*.txt' '*.json' --local-dir /opt/models/clip && \
    huggingface-cli download google-bert/bert-base-chinese 'model.safetensors' '*.txt' '*.json' --local-dir /opt/models/bert && \
    huggingface-cli download pk5ls20/PaddleModel 'PaddleOCR2Pytorch/ch_ptocr_v4_det_infer.pth' 'PaddleOCR2Pytorch/ch_ptocr_v4_rec_infer.pth' \
     'PaddleOCR2Pytorch/ch_ptocr_mobile_v2.0_cls_infer.pth' 'PaddleOCR2Pytorch/configs/det/ch_PP-OCRv4/ch_PP-OCRv4_det_student.yml' \
     'PaddleOCR2Pytorch/configs/rec/PP-OCRv4/ch_PP-OCRv4_rec.yml' 'ppocr_keys_v1.txt' --local-dir /opt/models/ocr && \
    rm -rf /root/.cache/huggingface

ENV APP_MODEL__CLIP="/opt/models/clip" \
    APP_MODEL__BERT="/opt/models/bert" \
    APP_MODEL__EASYPADDLEOCR="/opt/models/ocr" \
    APP_DEVICE="cpu"

COPY . .

EXPOSE 8000

VOLUME ["/opt/NekoImageGallery/static"]


LABEL org.opencontainers.image.authors="EdgeNeko" \
      org.opencontainers.image.url="https://github.com/hv0905/NekoImageGallery" \
      org.opencontainers.image.source="https://github.com/hv0905/NekoImageGallery" \
      org.opencontainers.image.title="NekoImageGallery" \
      org.opencontainers.image.description="An AI-powered natural language & reverse Image Search Engine powered by CLIP & qdrant."

ENTRYPOINT ["python", "main.py"]
