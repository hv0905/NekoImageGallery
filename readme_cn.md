# NekoImageGallery

[![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/hv0905/NekoImageGallery/prod.yml?logo=github)](https://github.com/hv0905/NekoImageGallery/actions)
[![codecov](https://codecov.io/gh/hv0905/NekoImageGallery/branch/master/graph/badge.svg?token=JK2KZBDIYP)](https://codecov.io/gh/hv0905/NekoImageGallery)
![Man hours](https://img.shields.io/endpoint?url=https%3A%2F%2Fmanhours.aiursoft.cn%2Fr%2Fgithub.com%2Fhv0905%2FNekoImageGallery.json)

基于Clip模型与Qdrant向量数据库的在线AI图片搜索引擎。支持关键字搜索以及相似图片搜索。

[English Document](readme.md)

## ✨特性

- 使用Clip模型为每张图片生成768维向量作为搜索依据。无需人工标注或分类，无限分类类别。
- 支持OCR文本搜索，使用PaddleOCR提取图片文本并使用BERT模型生成文本特征向量。
- 使用Qdrant向量数据库进行高效的向量搜索。

## 📷截图

![Screenshot1](web/screenshots/1.png)
![Screenshot2](web/screenshots/2.png)
![Screenshot3](web/screenshots/3.png)
![Screenshot4](web/screenshots/4.png)
![Screenshot5](web/screenshots/5.png)
![Screenshot6](web/screenshots/6.png)

> 以上截图可能包含来自不同画师的版权图片，请不要将其用作其它用途。


## ✈️部署

### 🖥️ 本地部署

#### 选择元数据存储方式

NekoImageGallery支持两种元数据存储方式：Qdrant数据库存储与本地文件存储。您可以根据自己的需求选择其中一种方式。

##### Qdrant数据库 （推荐）

在大多数情况下，我们推荐使用Qdrant数据库存储元数据。Qdrant数据库提供了高效的检索性能，灵活的扩展性以及更好的数据安全性。

请根据[Qdrant文档](https://qdrant.tech/documentation/quick-start/)部署Qdrant数据库，推荐使用docker部署。

如果你不想自己部署Qdrant，可以使用[Qdrant官方提供的在线服务](https://qdrant.tech/documentation/cloud/)。

##### 本地文件存储

本地文件存储直接将图片元数据（包括特征向量等）存在本地的Sqlite数据库中。仅建议在小规模部署或开发部署中使用。

本地文件存储不需要额外的数据库部署流程，但是存在以下缺点：

- 本地存储没有对向量进行索引和优化，所有搜索的时间复杂度为`O(n)`，因此若数据规模较大，搜索与索引的性能会下降。
- 使用本地文件存储会使得NekoImageGallery变得有状态，因此会丧失横向扩展能力。
- 当你希望迁移到Qdrant数据库进行存储时，已索引的元数据可能难以直接迁移。

#### 部署NekoImageGallery
1. 将项目目录clone到你自己的PC或服务器中。
2. 强烈建议在python venv虚拟环境中安装本项目所需依赖， 运行下面命令：
    ```shell
    python -m venv .venv
    . .venv/bin/activate
    ```
3. 安装PyTorch. 按照[PyTorch文档](https://pytorch.org/get-started/locally/)使用pip安装适合你的系统的torch版本
   > 如果您希望使用CUDA加速推理，务必在本步中安装支持Cuda的pytorch版本，安装完成后可以使用`torch.cuda.is_available()`确认CUDA是否可用。
4. 安装其它本项目所需依赖：
    ```shell
    pip install -r requirements.txt
    ```
5. 按需修改位于`config`目录下的配置文件，您可以直接修改`default.env`，但是建议创建一个名为`local.env`的文件，覆盖`default.env`中的配置。
6. 初始化Qdrant数据库，运行下面命令：
    ```shell
    python main.py --init-database
    ```
   此操作将会在Qdrant数据库中创建一个名字与`config.QDRANT_COLL`相同的collection，用于存储图片向量。
7. (可选)在开发部署与小规模部署中，可以使用本应用自带的静态文件索引与服务功能。使用下面命令索引您本地的图片目录：
    ```shell
   python main.py --local-index <path-to-your-image-directory>
    ```
   此操作会将位于`<path-to-your-image-directory>`目录下的所有图片文件复制到`config.STATIC_FILE_PATH`目录下(默认为`./static`)，并将图片信息写入Qdrant数据库。
   
   然后运行下面的命令，为所有static目录下的图片生成缩略图：

   ```shell
    python main.py --local-create-thumbnail
   ```
   
   如果你希望大规模部署，可以使用类似`MinIO`的OSS存储服务，将图片文件存储在OSS中，然后将图片信息写入Qdrant数据库即可。
8. 运行本应用：
    ```shell
    python main.py
    ```
   你可以通过`--host`指定希望绑定到的ip地址(默认为0.0.0.0)，通过`--port`指定希望绑定到的端口(默认为8000)。
9. (可选)部署前端应用：[NekoImageGallery.App](https://github.com/hv0905/NekoImageGallery.App)是本项目的一个简易web前端应用，如需部署请参照它的[部署文档](https://github.com/hv0905/NekoImageGallery.App)。

### 🐋 Docker 部署

#### 关于Docker镜像

NekoImageGallery镜像发布在DockerHub上，并包含多个变种，设计于在不同的环境使用。

| Tags                                                                                                                                        | 介绍                     | Latest 镜像尺寸                                                                                                                                                                                                |
|---------------------------------------------------------------------------------------------------------------------------------------------|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `edgeneko/neko-image-gallery:<version>`<br>`edgeneko/neko-image-gallery:<version>-cuda`<br>`edgeneko/neko-image-gallery:<version>-cuda12.1` | 基于CUDA12.1, 支持GPU推理的镜像 | [![Docker Image Size (tag)](https://img.shields.io/docker/image-size/edgeneko/neko-image-gallery/latest?label=Docker%20Image%20(cuda))](https://hub.docker.com/r/edgeneko/neko-image-gallery)              |
| `edgeneko/neko-image-gallery:<version>-cuda11.8`                                                                                            | 基于CUDA11.8, 支持GPU推理的镜像 | [![Docker Image Size (tag)](https://img.shields.io/docker/image-size/edgeneko/neko-image-gallery/latest-cuda11.8?label=Docker%20Image%20(cuda11.8))](https://hub.docker.com/r/edgeneko/neko-image-gallery) |
| `edgeneko/neko-image-gallery:<version>-cpu`                                                                                                 | 仅支持CPU推理的镜像            | [![Docker Image Size (tag)](https://img.shields.io/docker/image-size/edgeneko/neko-image-gallery/latest-cpu?label=Docker%20Image%20(cpu))](https://hub.docker.com/r/edgeneko/neko-image-gallery)           |

其中，`<version>`为NekoImageGallery的版本号或版本代称，具体如下：

| Version           | 介绍                                                   |
|-------------------|------------------------------------------------------|
| `latest`          | 最新的稳定版本                                              |
| `v*.*.*` / `v*.*` | 特定版本号(与GitHub Tag对应)                                 |
| `edge`            | 最新的开发版本，与master分支同步更新，可能包含未经完善测试的功能和breaking changes |

#### 准备`nvidia-container-runtime`

如果你希望在推理时支持CUDA加速，请参考[Docker GPU相关文档](https://docs.docker.com/config/containers/resource_constraints/#gpu)准备支持GPU的容器运行时。

> 相关文档：  
> 1. https://docs.docker.com/config/containers/resource_constraints/#gpu
> 2. https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker
> 3. https://nvidia.github.io/nvidia-container-runtime/

#### 运行

1. 下载`docker-compose.yml`文件。
   ```shell
   # For cuda deployment (default)
   wget https://raw.githubusercontent.com/hv0905/NekoImageGallery/master/docker-compose.yml
   # For CPU-only deployment
   wget https://raw.githubusercontent.com/hv0905/NekoImageGallery/master/docker-compose-cpu.yml && mv docker-compose-cpu.yml docker-compose.yml
   ```
2. 按需修改docker-compose.yml文件
3. 运行下面命令启动docker-compose
   ```shell
   # start in foreground
   docker compose up
   # start in background(detached mode)
   docker compose up -d
   ```

## 📚 API文档

API文档由FastAPI内置的Swagger UI提供。您可以通过访问服务器的`/docs`或`/redoc`路径来查看API文档。

## ⚡ 相关项目

以下项目基于NekoImageGallery工作！

[![NekoImageGallery.App](https://github-readme-stats.vercel.app/api/pin/?username=hv0905&repo=NekoImageGallery.App&show_owner=true)](https://github.com/hv0905/NekoImageGallery.App)
[![LiteLoaderQQNT-NekoImageGallerySearch](https://github-readme-stats.vercel.app/api/pin/?username=pk5ls20&repo=LiteLoaderQQNT-NekoImageGallerySearch&show_owner=true)](https://github.com/pk5ls20/LiteLoaderQQNT-NekoImageGallerySearch)
[![nonebot-plugin-nekoimage](https://github-readme-stats.vercel.app/api/pin/?username=pk5ls20&repo=nonebot-plugin-nekoimage&show_owner=true)](https://github.com/pk5ls20/pk5ls20/nonebot-plugin-nekoimage)

## 📊仓库信息

![Alt](https://repobeats.axiom.co/api/embed/ac080afa0d2d8af0345f6818b9b7c35bf8de1d31.svg "Repobeats analytics image")

## ❤️贡献指南

有很多种可以为本项目提供贡献的方式：记录 Bug，提交 Pull Request，报告问题，提出建议等等。

即使您拥有对本仓库的写入权限，您也应该在有需要时创建自己的功能分支并通过 Pull Request 的方式提交您的变更。
这有助于让我们的主仓库保持整洁并使您的个人工作流程不可见。

我们也很感兴趣听到您关于这个项目未来的反馈。您可以通过 Issues 追踪器提交建议或功能请求。为了使这个过程更加有效，我们希望这些内容包含更多信息，以更清晰地定义它们。

## Copyright

Copyright 2023 EdgeNeko

Licensed under GPLv3 license.