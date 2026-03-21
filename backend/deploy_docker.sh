#!/bin/bash
# ================================================
# ChromaAdapt AI Docker 自动部署脚本
# 由 Webhook 触发执行
# ================================================

set -e

# 配置
PROJECT_DIR="/opt/chromaadapt-ai"
LOG_FILE="/var/log/deploy.log"
TIME=$(date '+%Y-%m-%d %H:%M:%S')

# 日志函数
log() {
    echo "[$TIME] [$1] $2" | tee -a "$LOG_FILE"
}

# 开始部署
log "INFO" "=========================================="
log "INFO" "开始 Docker 自动部署 ChromaAdapt AI"
log "INFO" "触发时间: $DEPLOY_TRIGGERED_AT"
log "INFO" "=========================================="

cd "$PROJECT_DIR" || {
    log "ERROR" "无法进入项目目录: $PROJECT_DIR"
    exit 1
}

# 拉取最新代码
log "INFO" "正在拉取最新代码..."
git fetch origin main
git reset --hard origin/main
log "INFO" "代码更新完成"

# 重新构建并启动 Docker 容器
log "INFO" "正在重建 Docker 容器..."
docker-compose build --no-cache
docker-compose up -d

log "INFO" "Docker 容器已重启"

# ================================================
# 完成
# ================================================
log "INFO" "=========================================="
log "INFO" "部署完成! 时间: $(date '+%Y-%m-%d %H:%M:%S')"
log "INFO" "=========================================="
