---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "NekoImageGallery"
  text: "An AI-powered Image Gallery"
  tagline: An online AI image search engine based on the Clip model and Qdrant vector database. Supports keyword search and similar image search.
  image:
    src: /logo.png
    alt: NekoImageGallery
  actions:
    - theme: brand
      text: Introduction
      link: /introduction
    - theme: alt
      text: View on GitHub
      link: https://github.com/hv0905/NekoImageGallery

features:
  - title: AI-Powered Search
    details: Use the Clip model to generate 768-dimensional vectors for each image as the basis for search. No need for manual annotation or classification, unlimited classification categories.
  - title: OCR Text Search
    details: OCR Text search is supported, use PaddleOCR to extract text from images and use BERT to generate text vectors for search.
  - title: High-Performance Vector Database
    details: Use Qdrant vector database for efficient vector search.
---

