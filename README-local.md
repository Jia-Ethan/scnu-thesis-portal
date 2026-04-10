# 本地运行说明

## 1. 安装后端依赖

```bash
cd /Users/ethan/scnu-thesis-portal
uv sync --project backend
```

## 2. 安装前端依赖

```bash
cd /Users/ethan/scnu-thesis-portal/web
npm install
```

## 3. 启动后端

```bash
cd /Users/ethan/scnu-thesis-portal
uv run --project backend uvicorn backend.app.main:app --reload --port 8000
```

## 4. 启动前端

```bash
cd /Users/ethan/scnu-thesis-portal/web
npm run dev
```

## 5. 构建本地演示版

```bash
cd /Users/ethan/scnu-thesis-portal/web
npm run build
```

构建完成后，后端会优先托管 `web/dist` 作为单入口演示页面。

## 6. 注意事项

- 仅支持 `.docx`
- 当前不支持 `.doc`
- 当前不保留原 Word 样式
- 当前依赖本地 XeLaTeX 环境
- 如果缺少 TeX 宏包，接口会返回明确错误
