#!/bin/bash
# ================================================
# Docker + Gitee Webhook 自动部署 - 一键安装脚本
# 在服务器上以 root 身份运行此脚本
# ================================================

set -e

echo "=============================================="
echo "ChromaAdapt AI Docker 一键部署脚本"
echo "=============================================="

# 检查系统要求
if ! command -v docker &> /dev/null; then
    echo "[1/5] 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
else
    echo "[1/5] Docker 已安装，跳过"
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[2/5] 安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "[2/5] Docker Compose 已安装，跳过"
fi

echo "[3/5] 克隆项目代码..."
cd /opt
rm -rf chromaadapt-ai
git clone https://gitee.com/你的用户名/chromaadapt-ai.git chromaadapt-ai
cd chromaadapt-ai

echo "[4/5] 配置环境变量..."
cp .env.example .env
echo "请编辑 /opt/chromaadapt-ai/.env 文件，填写以下配置："
echo "  - ARK_API_KEY"
echo "  - ARK_ENDPOINT_ID 等"
echo "  - WEBHOOK_SECRET（Webhook 密码）"
echo ""
echo "按回车继续..."
read

echo "[5/5] 构建并启动容器..."
docker-compose up -d --build

echo ""
echo "=============================================="
echo "部署完成！"
echo "=============================================="
echo "检查服务状态: docker-compose ps"
echo "查看日志: docker-compose logs -f"
echo ""
echo "配置 Gitee WebHook:"
echo "  URL: http://你的服务器IP:9000/webhook"
echo "  密码: 你在 .env 中设置的 WEBHOOK_SECRET"
echo "=============================================="
