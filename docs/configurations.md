# Configurations

NekoImageGallery uses a flexible configuration system that allows you to customize its behavior through environment variables or a `.env` file. The default configuration is stored in `config/default.env`. It is recommended to create a `config/local.env` file to override the default settings.

Here are the available configuration options:

## Vector Database Configuration

| Key | Description | Default |
| --- | --- | --- |
| `APP_QDRANT__MODE` | Mode for the vector database. Options: "server", "local", "memory". | `server` |
| `APP_QDRANT__HOST` | Hostname or IP address of the Qdrant server. | `localhost` |
| `APP_QDRANT__PORT` | Port number for the Qdrant HTTP server. | `6333` |
| `APP_QDRANT__GRPC_PORT` | Port number for the Qdrant gRPC server. | `6334` |
| `APP_QDRANT__PREFER_GRPC` | Set to `True` to use gRPC for Qdrant connection. | `True` |
| `APP_QDRANT__API_KEY` | API key for Qdrant server. | |
| `APP_QDRANT__COLL` | Collection name to use in Qdrant. | `NekoImg` |
| `APP_QDRANT__LOCAL_PATH` | Path to the file where vectors will be stored in local mode. | `./images_metadata` |

## Server Configuration

| Key | Description | Default |
| --- | --- | --- |
| `APP_DEVICE` | Device for PyTorch inference. "auto" for automatic detection. | `auto` |
| `APP_CORS_ORIGINS` | List of allowed origins for CORS. | `["*"]` |
| `APP_WITH_FRONTEND` | Enable built-in frontend. All APIs will be under `/api`. | `False` |

## Models Configuration

| Key | Description | Default |
| --- | --- | --- |
| `APP_MODEL__CLIP` | Model for CLIP embeddings (Vision Search). | `openai/clip-vit-large-patch14` |
| `APP_MODEL__BERT` | Model for BERT embeddings (OCR Search). | `bert-base-chinese` |
| `APP_MODEL__EASYPADDLEOCR` | Model for easypaddleocr inference (OCR indexing). | |

## OCR Search Configuration

| Key | Description | Default |
| --- | --- | --- |
| `APP_OCR_SEARCH__ENABLE` | Enable OCR search functionality. | `True` |
| `APP_OCR_SEARCH__OCR_MODULE` | OCR module to use for text extraction. | `easypaddleocr` |
| `APP_OCR_SEARCH__OCR_MIN_CONFIDENCE` | Minimum confidence for OCR results. | `1e-2` |
| `APP_OCR_SEARCH__OCR_LANGUAGE` | List of languages for OCR. | `["ch_sim", "en"]` |

## Admin API Configuration

| Key | Description | Default |
| --- | --- | --- |
| `APP_ADMIN_API_ENABLE` | Enable admin API. | `False` |
| `APP_ADMIN_TOKEN` | Token to access admin API. | `your-super-secret-admin-token` |
| `APP_ADMIN_INDEX_QUEUE_MAX_LENGTH` | Max length of the upload queue for admin API. | `200` |

## Access Protection Configuration

| Key | Description | Default |
| --- | --- | --- |
| `APP_ACCESS_PROTECTED` | Enable access protection using tokens. | `False` |
| `APP_ACCESS_TOKEN` | Token to access the API. | `your-super-secret-access-token` |

## Storage Settings

| Key | Description | Default |
| --- | --- | --- |
| `APP_STORAGE__METHOD` | Method for storing files. Options: "local", "s3", "disabled". | `local` |
| `APP_STORAGE__LOCAL__PATH` | Path where files will be stored locally. | `./static` |
| `APP_STORAGE__S3__BUCKET` | Name of the S3 bucket. | |
| `APP_STORAGE__S3__PATH` | Path where files will be stored in the S3 bucket. | `./static` |
| `APP_STORAGE__S3__REGION` | Region where the S3 bucket is located. | |
| `APP_STORAGE__S3__ENDPOINT_URL` | Endpoint URL for the S3 service. | |
| `APP_STORAGE__S3__ACCESS_KEY_ID` | Access key ID for S3. | |
| `APP_STORAGE__S3__SECRET_ACCESS_KEY` | Secret access key for S3. | |
| `APP_STORAGE__S3__SESSION_TOKEN` | Session token for S3 (optional). | |
| `APP_STORAGE__S3__USER_ENDPOINT_URL` | Optional Endpoint URL for final presentation to the user. | |
