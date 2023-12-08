
# Vector Database Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLL = "NekoImg"

# CLIP Configuration
CLIP_DEVICE = 'auto'
CLIP_MODEL = "openai/clip-vit-large-patch14"

# Static File Hosting: Useful for local deployment / local file deployment without OSS like S3/MinIO
STATIC_FILE_ENABLE = True
STATIC_FILE_PATH = "./static"

# Server Configuration
CORS_ORIGINS = ["*"]
