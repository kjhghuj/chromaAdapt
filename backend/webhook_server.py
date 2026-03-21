#!/usr/bin/env python3
"""
Git Webhook Listener for ChromaAdapt AI
轻量级 Webhook 监听服务，接收 Gitee/GitHub 推送事件触发自动部署
"""

from flask import Flask, request, jsonify
import subprocess
import os
import logging
from datetime import datetime

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-secret-here')
PROJECT_DIR = os.getenv('PROJECT_DIR', '/opt/chromaadapt-ai')
DEPLOY_SCRIPT = os.getenv('DEPLOY_SCRIPT', '/opt/deploy.sh')


@app.route('/webhook', methods=['POST'])
def webhook():
    """接收 Webhook 请求"""
    client_ip = request.remote_addr
    event = request.headers.get('X-Gitee-Event', request.headers.get('X-GitHub-Event', 'unknown'))

    logger.info(f"收到 Webhook 请求 | IP: {client_ip} | 事件: {event}")

    # Gitee 验证
    gitee_token = request.headers.get('X-Gitee-Token', '')
    if gitee_token and gitee_token != WEBHOOK_SECRET:
        logger.warning(f"Token 验证失败: {client_ip}")
        return jsonify({'error': 'unauthorized'}), 401

    # GitHub 验证 (HMAC)
    github_signature = request.headers.get('X-Hub-Signature-256', '')
    if github_signature:
        import hmac
        import hashlib
        secret = WEBHOOK_SECRET.encode()
        payload = request.get_data()
        expected = 'sha256=' + hmac.new(secret, payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(github_signature.lower(), expected.lower()):
            logger.warning(f"GitHub 签名验证失败: {client_ip}")
            return jsonify({'error': 'unauthorized'}), 401

    # 只处理 push 事件
    if event not in ('push', 'Push'):
        logger.info(f"忽略非 push 事件: {event}")
        return jsonify({'message': 'ignored'})

    # 异步触发部署（不阻塞响应）
    try:
        subprocess.Popen(
            ['bash', DEPLOY_SCRIPT],
            stdout=open('/var/log/deploy.log', 'a'),
            stderr=subprocess.STDOUT,
            env={**os.environ, 'DEPLOY_TRIGGERED_AT': datetime.now().isoformat()}
        )
        logger.info("部署任务已触发")
    except Exception as e:
        logger.error(f"启动部署脚本失败: {e}")
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'deployment started'})


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'service': 'webhook-listener'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=False)
