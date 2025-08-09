---
layout: home

hero:
  name: "NekoImageGallery"
  text: "一个由AI驱动的相册"
  tagline: 一个基于Clip模型和Qdrant向量数据库的在线AI图片搜索引擎。支持关键词搜索和以图搜图。
  image:
    src: /logo.png
    alt: NekoImageGallery
  actions:
    - theme: brand
      text: 项目介绍
      link: /zh/introduction
    - theme: alt
      text: 在GitHub上查看
      link: https://github.com/hv0905/NekoImageGallery

features:
  - title: AI驱动的搜索
    details: 使用Clip模型为每张图片生成768维向量作为搜索基础。无需手动标注或分类，分类类别不限。
  - title: OCR文字搜索
    details: 支持OCR文字搜索，使用PaddleOCR从图片中提取文字，并使用BERT生成文字向量进行搜索。
  - title: 高性能向量数据库
    details: 使用Qdrant向量数据库进行高效的向量搜索。
---
