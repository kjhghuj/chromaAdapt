# AI API 使用指南 (新版)

本文档介绍如何在 ChromaAdapt AI 项目中配置通义千问 3.5 和火山引擎即梦 AI 4.0 服务。

## 1. 后端配置 (backend/.env)

本项目采用后端转发模式。请在 `backend/.env` 中配置以下密钥：

### 1.1 通义千问 3.5 (DashScope)
1.  访问 [阿里云百炼 (Model Studio)](https://bailian.console.aliyun.com/)。
2.  开通服务并生成 API Key。
3.  在 `.env` 中填入 `DASHSCOPE_API_KEY=你的_API_KEY`。

### 1.2 火山引擎即梦 AI (Jimeng AI)
1.  注册[火山引擎](https://www.volcengine.com/)账号。
2.  开通[即梦 AI 服务](https://www.volcengine.com/product/jimeng-ai)。
3.  获取 AccessKey ID (AK) 和 Secret AccessKey (SK)。
4.  在 `.env` 中填入 `VOLC_AK` 和 `VOLC_SK`。

---

## 2. 后端接口说明

后端使用 FastAPI 提供服务，默认运行在 `http://localhost:8000`。

-   **POST /analyze**: 图像理解与分析 (Qwen 3.5)。
-   **POST /generate**: 图像生成与色彩迁移 (Jimeng 4.0)。
-   **POST /edit**: 交互式图像编辑 (Jimeng 4.0)。

---

## 3. 前端服务调用 (frontend/services/apiService.ts)

前端通过 `apiService.ts` 统一调用后端。

-   所有图像数据以 Base64 格式传输。
-   后端负责所有 API 的签名和鉴权。

---

## 4. 常见问题

### 4.1 CORS 错误
如果前端提示 CORS 错误，请检查后端 `main.py` 中的 `allow_origins` 配置。默认已开启通配符支持。

### 4.2 签名失败
火山引擎签名对时间非常敏感，请确保服务器/电脑系统时间准确。
