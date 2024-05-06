FROM edgeneko/neko-image-gallery:latest

RUN mkdir -p /opt/models && \
    huggingface-cli download openai/clip-vit-large-patch14 model.safetensors *.txt *.json --local-dir /opt/models/clip && \
    huggingface-cli download google-bert/bert-base-chinese model.safetensors *.txt *.json --local-dir /opt/models/bert && \
    rm -rf /root/.cache/huggingface

ENV APP_CLIP__MODEL=/opt/models/clip
ENV APP_OCR_SEARCH__BERT_MODEL=/opt/models/bert