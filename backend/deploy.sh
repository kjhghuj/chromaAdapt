#!/bin/bash
# ================================================
# ChromaAdapt AI 自动部署脚本
# 由 Webhook 触发执行
# ================================================

set -e

# 配置
PROJECT_DIR="/opt/chromaadapt-ai"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_FILE="/var/log/deploy.log"
TIME=$(date '+%Y-%m-%d %H:%M:%S')

# 日志函数
log() {
    echo "[$TIME] [$1] $2" | tee -a "$LOG_FILE"
}

# 开始部署
log "INFO" "=========================================="
log "INFO" "开始自动部署 ChromaAdapt AI"
log "INFO" "触发时间: $DEPLOY_TRIGGERED_AT"
log "INFO" "=========================================="

# 进入项目目录
cd "$PROJECT_DIR" || {
    log "ERROR" "无法进入项目目录: $PROJECT_DIR"
    exit 1
}

# 拉取最新代码
log "INFO" "正在拉取最新代码..."
git fetch origin main
git reset --hard origin/main
log "INFO" "代码更新完成"

# ================================================
# 后端构建
# ================================================
log "INFO" "开始构建后端..."

cd "$BACKEND_DIR"

# 安装 Python 依赖（使用清华源加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

# 数据库迁移（如果有的话）
python manage.py migrate --fake 2>/dev/null || true

log "INFO" "后端构建完成"

# ================================================
# 前端构建
# ================================================
log "INFO" "开始构建前端..."

cd "$FRONTEND_DIR"

# 安装 Node 依赖（使用淘宝源加速）
npm install --registry=https://registry.npmmirror.com --silent 2>&1 | tail -5

# 构建生产版本
npm run build

log "INFO" "前端构建完成"

# ================================================
# 重启后端服务
# ================================================
log "INFO" "重启后端服务..."

# 如果使用 systemd
if command -v systemctl &> /dev/null; then
    systemctl restart chroma-backend 2>/dev/null || {
        log "WARN" "systemd 重启失败，尝试直接启动..."
        # 杀死旧进程
        pkill -f "python.*manage.py runserver" || true
        # 启动新进程
        nohup python manage.py runserver 0.0.0.0:8000 > /var/log/chroma-backend.log 2>&1 &
        sleep 2
    }
    log "INFO" "后端服务已重启"
fi

# ================================================
# 完成
# ================================================
log "INFO" "=========================================="
log "INFO" "部署完成! 时间: $(date '+%Y-%m-%d %H:%M:%S')"
log "INFO" "=========================================="
