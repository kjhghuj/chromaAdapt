# ChromaAdapt AI 技术架构文档

本文档详细描述了 ChromaAdapt AI 项目的系统架构、数据流以及关键技术实现。

## 1. 系统概览

ChromaAdapt AI 是一个前后端分离的图像处理系统，集成了 **通义千问 3.5 (Qwen 3.5)** 和 **火山引擎即梦 AI 4.0**。系统通过 Python 后端封装 AI 调用，前端通过 React 界面提供交互式体验。

## 2. 核心架构模式

项目采用了 **Frontend-Backend-Service** 的分层架构模式：

-   **Frontend (React)**: 负责 UI 渲染、用户交互及状态管理。
-   **Backend (FastAPI)**: 负责鉴权 (V4 签名)、API 转发及复杂的 AI 逻辑处理。
-   **AI Services**: 外部大模型服务 (阿里云 DashScope, 火山引擎)。

### 2.1 关键前端模块 (frontend/)

-   `hooks/useChromaApp.ts`: 全局状态中心。
-   `services/apiService.ts`: 与 Python 后端通信的唯一接口层。

### 2.2 关键后端模块 (backend/)

-   `main.py`: 路由定义、CORS 配置及 V4 签名逻辑实现。

## 3. 数据流与工作原理

### 3.1 色彩适配流程 (Color Adapt)

1.  用户上传参考图。
2.  前端调用后端 `/analyze` 接口。
3.  后端调用 **Qwen 3.5 VL** 提取色盘 (Palette)。
4.  用户上传目标海报。
5.  前端调用后端 `/generate` 接口。
6.  后端调用 **Jimeng 4.0** 进行色彩迁移。

### 3.2 批量流水线 (Pipeline)

1.  用户上传一组参考图或目标图。
2.  任务被添加到前端 `pipelineQueue` 中。
3.  前端根据并发设置依次请求后端接口。

## 4. 技术挑战与解决方案

-   **安全鉴权**: 火山引擎 API 需要复杂的 HMAC-SHA256 V4 签名。通过在 Python 后端集中处理签名逻辑，避免了前端暴露密钥及复杂的签名计算。
-   **跨域问题 (CORS)**: 后端通过 FastAPI 的 `CORSMiddleware` 统一解决，确保前端可以安全访问后端服务。
-   **模型替换**: 通过将 Gemini 替换为 Qwen 3.5 和 Jimeng 4.0，显著提升了中文理解能力和图像生成的专业度。
