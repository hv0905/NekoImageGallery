# 配置

NekoImageGallery使用灵活的配置系统，允许您通过环境变量或`.env`文件自定义其行为。默认配置存储在`config/default.env`中。建议创建一个`config/local.env`文件来覆盖默认设置。

以下是可用的配置选项：

## 向量数据库配置

| 键 | 描述 | 默认值 |
| --- | --- | --- |
| `APP_QDRANT__MODE` | 向量数据库的模式。选项："server"、"local"、"memory"。 | `server` |
| `APP_QDRANT__HOST` | Qdrant服务器的主机名或IP地址。 | `localhost` |
| `APP_QDRANT__PORT` | Qdrant HTTP服务器的端口号。 | `6333` |
| `APP_QDRANT__GRPC_PORT` | Qdrant gRPC服务器的端口号。 | `6334` |
| `APP_QDRANT__PREFER_GRPC` | 设置为`True`以使用gRPC进行Qdrant连接。 | `True` |
| `APP_QDRANT__API_KEY` | Qdrant服务器的API密钥。 | |
| `APP_QDRANT__COLL` | 在Qdrant中使用的集合名称。 | `NekoImg` |
| `APP_QDRANT__LOCAL_PATH` | 在本地模式下存储向量的文件的路径。 | `./images_metadata` |

## 服务器配置

| 键 | 描述 | 默认值 |
| --- | --- | --- |
| `APP_DEVICE` | PyTorch推理的设备。"auto"表示自动检测。 | `auto` |
| `APP_CORS_ORIGINS` | CORS允许的来源列表。 | `["*"]` |
| `APP_WITH_FRONTEND` | 启用内置前端。所有API将位于`/api`下。 | `False` |

## 模型配置

| 键 | 描述 | 默认值 |
| --- | --- | --- |
| `APP_MODEL__CLIP` | 用于CLIP嵌入（视觉搜索）的模型。 | `openai/clip-vit-large-patch14` |
| `APP_MODEL__BERT` | 用于BERT嵌入（OCR搜索）的模型。 | `bert-base-chinese` |
| `APP_MODEL__EASYPADDLEOCR` | 用于easypaddleocr推理（OCR索引）的模型。 | |

## OCR搜索配置

| 键 | 描述 | 默认值 |
| --- | --- | --- |
| `APP_OCR_SEARCH__ENABLE` | 启用OCR搜索功能。 | `True` |
| `APP_OCR_SEARCH__OCR_MODULE` | 用于文本提取的OCR模块。 | `easypaddleocr` |
| `APP_OCR_SEARCH__OCR_MIN_CONFIDENCE` | OCR结果的最低置信度。 | `1e-2` |
| `APP_OCR_SEARCH__OCR_LANGUAGE` | OCR的语言列表。 | `["ch_sim", "en"]` |

## 管理API配置

| 键 | 描述 | 默认值 |
| --- | --- | --- |
| `APP_ADMIN_API_ENABLE` | 启用管理API。 | `False` |
| `APP_ADMIN_TOKEN` | 用于访问管理API的令牌。 | `your-super-secret-admin-token` |
| `APP_ADMIN_INDEX_QUEUE_MAX_LENGTH` | 管理API的上传队列的最大长度。 | `200` |

## 访问保护配置

| 键 | 描述 | 默认值 |
| --- | --- | --- |
| `APP_ACCESS_PROTECTED` | 使用令牌启用访问保护。 | `False` |
| `APP_ACCESS_TOKEN` | 用于访问API的令牌。 | `your-super-secret-access-token` |

## 存储设置

| 键 | 描述 | 默认值 |
| --- | --- | --- |
| `APP_STORAGE__METHOD` | 存储文件的方法。选项："local"、"s3"、"disabled"。 | `local` |
| `APP_STORAGE__LOCAL__PATH` | 本地存储文件的路径。 | `./static` |
| `APP_STORAGE__S3__BUCKET` | S3存储桶的名称。 | |
| `APP_STORAGE__S3__PATH` | S3存储桶中存储文件的路径。 | `./static` |
| `APP_STORAGE__S3__REGION` | S3存储桶所在的区域。 | |
| `APP_STORAGE__S3__ENDPOINT_URL` | S3服务的端点URL。 | |
| `APP_STORAGE__S3__ACCESS_KEY_ID` | S3的访问密钥ID。 | |
| `APP_STORAGE__S3__SECRET_ACCESS_KEY` | S3的秘密访问密钥。 | |
| `APP_STORAGE__S3__SESSION_TOKEN` | S3的会话令牌（可选）。 | |
| `APP_STORAGE__S3__USER_ENDPOINT_URL` | 可选的最终呈现给用户的端点URL。 | |
