import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "NekoImageGallery",
  description: "An AI-powered natural language & reverse Image Search Engine powered by CLIP & qdrant.",
  
  locales: {
    root: {
      label: 'English',
      lang: 'en',
      description: "An AI-powered natural language & reverse Image Search Engine powered by CLIP & qdrant."
    },
    zh: {
      label: '简体中文',
      lang: 'zh-CN',
      link: '/zh/',
      description: "一个由CLIP和qdrant驱动的AI自然语言和反向图像搜索引擎。",
      themeConfig: {
        nav: [
          { text: '首页', link: '/zh/' },
          { text: '项目介绍', link: '/zh/introduction' },
          { text: '部署', link: '/zh/deployment' },
          { text: '配置', link: '/zh/configurations' },
          { text: 'API', link: '/zh/api' },
          { text: '贡献', link: '/zh/contributing' }
        ]
      }
    }
  },

  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Introduction', link: '/introduction' },
      { text: 'Deployment', link: '/deployment' },
      { text: 'Configurations', link: '/configurations' },
      { text: 'API', link: '/api' },
      { text: 'Contributing', link: '/contributing' }
    ],
    logo: {
      src: '/logo.png',
      alt: 'NekoImageGallery'
    },

    sidebar: {
      '/': [
        {
          text: 'Guide',
          items: [
            { text: 'Introduction', link: '/introduction' },
            { text: 'Deployment', link: '/deployment' },
            { text: 'Configurations', link: '/configurations' },
            { text: 'API', link: '/api' },
            { text: 'Contributing', link: '/contributing' }
          ]
        }
      ],
      '/zh/': [
        {
          text: '指南',
          items: [
            { text: '项目介绍', link: '/zh/introduction' },
            { text: '部署', link: '/zh/deployment' },
            { text: '配置', link: '/zh/configurations' },
            { text: 'API', link: '/zh/api' },
            { text: '贡献', link: '/zh/contributing' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/hv0905/NekoImageGallery' }
    ],
  }
})
