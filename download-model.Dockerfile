FROM edgeneko/neko-image-gallery:latest

RUN mkdir -p /opt/models && \
    huggingface-cli download openai/clip-vit-large-patch14 model.safetensors *.txt *.json --local-dir /opt/models/clip && \
    huggingface-cli download google-bert/bert-base-chinese model.safetensors *.txt *.json --local-dir /opt/models/bert && \
    huggingface-cli download pk5ls20/PaddleModel PaddleOCR2Pytorch/ch_ptocr_v4_det_infer.pth PaddleOCR2Pytorch/ch_ptocr_v4_rec_infer.pth \
     PaddleOCR2Pytorch/ch_ptocr_mobile_v2.0_cls_infer.pth PaddleOCR2Pytorch/configs/det/ch_PP-OCRv4/ch_PP-OCRv4_det_student.yml \
     PaddleOCR2Pytorch/configs/rec/PP-OCRv4/ch_PP-OCRv4_rec.yml ppocr_keys_v1.txt --local-dir /opt/models/paddleocr && \
    rm -rf /root/.cache/huggingface

ENV APP_MODEL__CLIP=/opt/models/clip
ENV APP_MODEL__BERT=/opt/models/bert
ENV APP_MODEL__EASYPADDLEOCR=/opt/models/ocr