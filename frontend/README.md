# 前端开发环境搭建指南

该文档说明如何在本地构建并运行 **Breastfeeding** 项目的前端（React + TypeScript + Vite + Tailwind CSS），同时解释相关依赖的来源，便于协作者快速落地环境。

---

## 1. 环境概览

- **Node.js**：建议使用 LTS 版本（≥ 20.x）。
- **包管理器**：`npm`（项目自带 `package-lock.json`，确保依赖锁定）。
- **构建工具**：Vite（使用 rolldown-vite 兼容构建链）。
- **样式方案**：Tailwind CSS 3.x（通过 PostCSS 管线构建，而非直接引入编译后的 CSS）。
- **语言**：React 19 + TypeScript 5.9。

> 📌 与 Python 后端类似，前端的依赖清单由 `package.json` 与 `package-lock.json` 负责描述，作用等同于 `requirements.txt`。任何团队成员只要运行 `npm install`，即可恢复完全一致的依赖树。

---

## 2. 必备软件

1. 安装 [Node.js](https://nodejs.org/)（选择 LTS，安装时会一并装好 `npm`）。
2. （可选）安装 [nvm](https://github.com/nvm-sh/nvm) 以便切换 Node 版本。
3. 确认环境变量：
   ```bash
   node -v
   npm -v
   ```
   若命令均输出版本号，说明安装成功。

---

## 3. 安装依赖

在项目根目录执行以下命令：

```bash
cd frontend
npm install
```

`npm install` 会读取 `package.json` 与 `package-lock.json` 并安装 **devDependencies** 与 **dependencies**。其中最关键的条目：

| 包名 | 作用 |
| --- | --- |
| `tailwindcss@3.4.15` | 样式引擎，扫描 TSX/HTML 生成 CSS |
| `postcss@8.5.6` | CSS 转译管线，Vite 会加载 `postcss.config.cjs` |
| `autoprefixer@10.4.21` | 自动补全不同浏览器前缀 |
| `@vitejs/plugin-react` | 提供 React HMR 与 JSX 支持 |
| `typescript` & `@types/*` | TypeScript 语言服务及类型声明 |

---

## 4. Tailwind 构建配置

为了让 Tailwind 在 Vite 中工作，项目提供了两个 CommonJS 配置文件：

- `tailwind.config.cjs`
  ```js
  module.exports = {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    theme: {
      extend: {
        animation: {
          blob: 'blob 7s infinite',
        },
        keyframes: { /* 背景动画关键帧 */ }
      },
    },
    plugins: [],
  };
  ```
  Tailwind 会根据 `content` 列表扫描组件中的类名，例如 `bg-purple-300`，动态生成 CSS。

- `postcss.config.cjs`
  ```js
  module.exports = {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  };
  ```
  Vite 在构建 CSS 时会加载此配置，依次执行 Tailwind 与 Autoprefixer。

> ✅ 因为我们使用的是 JIT 构建模式，`src/index.css` 只需保留 `@tailwind base/components/utilities;` 三行指令即可，Tailwind 会在运行时注入真实样式。

---

## 5. 启动/构建命令

所有命令均在 `frontend/` 目录执行：

```bash
# 开发模式（自动热更新，代理到 Flask backend: http://127.0.0.1:9001）
npm run dev

# 生产构建（输出至 frontend/dist）
npm run build

# 静态预览生产构建结果
npm run preview

# 代码质量检查
npm run lint
```

> 🔁 默认 dev 服务器监听 `http://localhost:5173`。如果端口被占用，Vite 会自动切换至其他端口，控制台会给出提示。

---

## 6. 与后端协作

- 后端 Flask 项目位于仓库根目录，可通过 `sh start.sh` 启动（监听 `9001`）。
- Vite 已在 `vite.config.ts` 中配置代理：
  ```ts
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9001',
        changeOrigin: true,
      },
    },
  }
  ```
  因此前端直接 `fetch('/api/...')` 即可转发到后端，无需手动拼接端口。

---

## 7. 常见问题排查

| 现象 | 排查点 |
| --- | --- |
| 页面无样式 | 确认已执行 `npm install`；检查 `postcss.config.cjs` 是否存在且为 CommonJS 语法；刷新浏览器时选择 *Empty Cache and Hard Reload* |
| 控制台报错 `Unknown at rule @tailwind` | 说明 PostCSS 未加载 Tailwind 插件，多为依赖缺失或配置文件命名错误 | 
| Tailwind 动画无效 | 检查 `AuthPage.tsx` 中是否使用了 `[animation-delay:2s]` 等类名，以及 `tailwind.config.cjs` 中的 `keyframes` 定义是否存在 |
| dev 端口被占用 | 关闭已有进程或手动运行 `lsof -ti:5173 | xargs kill -9` 后重启 |

---

## 8. 依赖清单速览

- **前端**：`package.json` / `package-lock.json`
- **后端**：`requirements.txt`

部署或 CI/CD 时，分别运行：
```bash
# 后端
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd frontend
npm ci  # 比 npm install 更适合 CI，严格遵守 lockfile
```

---

如需进一步扩展脚手架或团队规范，可基于此文档继续补充。欢迎在提交 PR 时同步更新本 README，保持说明与代码一致。