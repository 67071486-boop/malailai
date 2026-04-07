# Copilot 指南（uni-im-MP-WEIXIN）

## 项目概览（架构与边界）
- 这是一个 uni-app（Vue3）应用，入口在 [main.js](main.js)；Vue2/Vue3 兼容逻辑通过 `#ifdef VUE3` 条件编译切分。
- 前端页面路由集中在 [pages.json](pages.json)，包含根目录 pages/ 以及多个 uni_modules 页面（如 uni-id-pages 的登录/注册/资料页）。
- 即时通讯能力来自 uni-im 模块，核心后端在 [uni_modules/uni-im/uniCloud/cloudfunctions/uni-im-co](uni_modules/uni-im/uniCloud/cloudfunctions/uni-im-co)，依赖 uni-cloud-s2s、uni-config-center、uni-id-common 等云端公共模块（见 [uni_modules/uni-im/uniCloud/cloudfunctions/uni-im-co/package.json](uni_modules/uni-im/uniCloud/cloudfunctions/uni-im-co/package.json)）。
- 本仓库同时包含 uniCloud 目录（如 [uniCloud-alipay](uniCloud-alipay)），用于云函数与数据库配置；与 uni_modules 自带的云函数并存。

## 关键约定与修改策略
- 登录/注册/用户中心来自 uni-id-pages：若需要大幅二次开发，建议复制页面到根目录 pages/ 并在 [pages.json](pages.json) 仅引用根目录页面；避免升级 uni_modules 时冲突（见 [uni_modules/uni-id-pages/readme.md](uni_modules/uni-id-pages/readme.md)）。
- uni_modules 下内容通常来自插件市场，升级会覆盖：只在必要时直接改动，并保留可回放的差异记录。
- 小程序平台配置位于 [manifest.json](manifest.json)（mp-weixin 等），修改平台行为优先从该文件入手。

## 常见定位入口（示例）
- 应用生命周期与全局样式入口：见 [App.vue](App.vue)。
- 登录/注册/找回密码页面路径：见 [pages.json](pages.json) 中的 uni-id-pages 路由条目。
- IM 相关云函数与推送能力：从 [uni_modules/uni-im/uniCloud/cloudfunctions/uni-im-co](uni_modules/uni-im/uniCloud/cloudfunctions/uni-im-co) 进入，关注其依赖的 common 模块。

## 工作流与运行方式
- 本项目没有发现可直接执行的脚本配置；通常通过 HBuilderX 运行/调试 uni-app（小程序/APP/H5）。如需新增可重复的构建脚本，请明确目标平台并在仓库内补充说明文件。
