ARG TORCH_VERSION=2.6.0
ARG CUDA_VERSION=12.4
FROM pytorch/pytorch:${TORCH_VERSION}-cuda${CUDA_VERSION}-cudnn9-runtime

WORKDIR /opt/NekoImageGallery

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    export PYTHONDONTWRITEBYTECODE=1 && \
    export UV_PROJECT_ENVIRONMENT=$(python -c "import sysconfig; print(sysconfig.get_config_var('prefix'))") && \
    uv sync --frozen --extra cu$(python -c "import torch; print(torch.version.cuda.replace('.', '').strip())") --no-dev --inexact --link-mode=copy

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
    APP_MODEL__EASYPADDLEOCR="/opt/models/ocr"

COPY . .

EXPOSE 8000

VOLUME ["/opt/NekoImageGallery/static"]

LABEL org.opencontainers.image.authors="EdgeNeko" \
      org.opencontainers.image.url="https://github.com/hv0905/NekoImageGallery" \
      org.opencontainers.image.source="https://github.com/hv0905/NekoImageGallery" \
      org.opencontainers.image.title="NekoImageGallery" \
      org.opencontainers.image.description="An AI-powered natural language & reverse Image Search Engine powered by CLIP & qdrant."

ENTRYPOINT ["python", "main.py"]