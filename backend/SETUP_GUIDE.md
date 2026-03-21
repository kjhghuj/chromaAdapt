# 服务器部署指南

## 前提条件
- 服务器：2核2G Ubuntu 20.04+
- 已安装：Python 3.10+, Node.js 18+, Nginx, Git
- 代码仓库：Gitee (推荐) 或 GitHub

---

## 第一步：上传代码到服务器

### 方式A：Gitee（推荐，国内速度快）
1. 在 [gitee.com](https://gitee.com) 创建仓库
2. 本地关联远程仓库：
```bash
git remote add gitee https://gitee.com/你的用户名/chromaadapt-ai.git
git push -u gitee main
```

### 方式B：GitHub（需要代理）
```bash
git remote add origin https://github.com/你的用户名/chromaadapt-ai.git
git push -u origin main
```

---

## 第二步：初始化服务器

### 2.1 安装系统依赖
```bash
# Ubuntu/Debian
apt update && apt upgrade -y
apt install -y python3-pip python3-venv nginx git

# 安装 Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 验证安装
python3 --version   # 应显示 3.10+
node --version      # 应显示 v18.x
nginx -v
```

### 2.2 创建项目目录
```bash
mkdir -p /opt/chromaadapt-ai
cd /opt/chromaadapt-ai

# 如果已有代码，直接 clone
git clone https://gitee.com/你的用户名/chromaadapt-ai.git .
# 或
git clone https://github.com/你的用户名/chromaadapt-ai.git .

# 设置权限
chown -R root:root /opt/chromaadapt-ai
chmod +x /opt/chromaadapt-ai/backend/deploy.sh
chmod +x /opt/chromaadapt-ai/backend/webhook_server.py
```

---

## 第三步：配置并启动服务

### 3.1 安装 Python 依赖
```bash
cd /opt/chromaadapt-ai/backend
pip3 install -r requirements.txt
```

### 3.2 安装 Node 依赖并构建前端（首次手动构建）
```bash
cd /opt/chromaadapt-ai/frontend
npm install
npm run build
```

### 3.3 复制服务文件
```bash
# 复制 systemd 服务文件
cp /opt/chromaadapt-ai/backend/chroma-backend.service /etc/systemd/system/
cp /opt/chromaadapt-ai/backend/webhook.service /etc/systemd/system/

# 重新加载 systemd
systemctl daemon-reload
```

### 3.4 创建日志目录
```bash
mkdir -p /var/log
touch /var/log/deploy.log /var/log/webhook.log /var/log/chroma-backend.log
chmod 666 /var/log/deploy.log /var/log/webhook.log /var/log/chroma-backend.log
```

### 3.5 配置 Nginx
```bash
# 复制 Nginx 配置
cp /opt/chromaadapt-ai/backend/nginx.conf /etc/nginx/sites-available/chromaadapt

# 编辑配置文件，替换 your-domain.com 为你的域名或IP
nano /etc/nginx/sites-available/chromaadapt

# 启用站点
ln -s /etc/nginx/sites-available/chromaadapt /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

### 3.6 启动服务
```bash
# 启动 Webhook 监听服务
systemctl enable webhook
systemctl start webhook

# 启动后端服务
systemctl enable chroma-backend
systemctl start chroma-backend

# 检查状态
systemctl status webhook
systemctl status chroma-backend
```

---

## 第四步：配置 Gitee Webhook

1. 打开 Gitee 仓库 → **管理** → **WebHooks** → **添加 WebHook**
2. 填写信息：
   - **URL**: `http://你的服务器IP:9000/webhook`
   - **密码**: `your-secret-here`（与 webhook.service 中的 WEBHOOK_SECRET 一致）
   - **勾选**: ✅ Push
3. 点击**添加**，Gitee 会发送测试请求
4. 查看服务器 `/var/log/webhook.log` 确认是否收到

---

## 第五步：修改 Webhook 密码

编辑服务文件，修改密码：
```bash
nano /etc/systemd/system/webhook.service

# 修改这一行：
Environment="WEBHOOK_SECRET=你的密码"

# 重启服务
systemctl restart webhook
```

然后在 Gitee WebHook 设置中更新密码。

---

## 常用命令

```bash
# 查看日志
tail -f /var/log/webhook.log      # Webhook 日志
tail -f /var/log/deploy.log       # 部署日志
tail -f /var/log/chroma-backend.log  # 后端日志

# 重启服务
systemctl restart webhook
systemctl restart chroma-backend
systemctl restart nginx

# 手动触发一次部署
bash /opt/chromaadapt-ai/backend/deploy.sh
```

---

## 故障排查

### 1. Webhook 收不到请求
```bash
# 检查服务状态
systemctl status webhook

# 检查端口是否监听
netstat -tlnp | grep 9000

# 测试本地访问
curl http://localhost:9000/health
```

### 2. 部署失败
```bash
# 查看部署日志
cat /var/log/deploy.log

# 手动执行部署脚本看报错
bash -x /opt/chromaadapt-ai/backend/deploy.sh
```

### 3. 后端无法启动
```bash
# 检查端口占用
lsof -i:8000

# 手动启动看报错
cd /opt/chromaadapt-ai/backend
python manage.py runserver 0.0.0.0:8000
```

### 4. Nginx 502 错误
```bash
# 检查后端是否运行
systemctl status chroma-backend

# 检查 Nginx 日志
tail /var/log/nginx/error.log
```

---

## 完整的一键安装脚本

```bash
# 在服务器上以 root 身份运行以下命令：

cd /opt
mkdir -p chromaadapt-ai && cd chromaadapt-ai

# 从 Gitee clone（替换为你的仓库地址）
git clone https://gitee.com/你的用户名/chromaadapt-ai.git .

# 一键安装依赖并配置
bash << 'INSTALL_SCRIPT'
set -e

# 安装系统依赖
apt update && apt upgrade -y
apt install -y python3-pip python3-venv nginx git

# 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 安装 Python 依赖
cd /opt/chromaadapt-ai/backend
pip3 install -r requirements.txt

# 安装 Node 依赖并构建
cd /opt/chromaadapt-ai/frontend
npm install
npm run build

# 配置 systemd 服务
cp /opt/chromaadapt-ai/backend/chroma-backend.service /etc/systemd/system/
cp /opt/chromaadapt-ai/backend/webhook.service /etc/systemd/system/

# 创建日志文件
mkdir -p /var/log
touch /var/log/deploy.log /var/log/webhook.log /var/log/chroma-backend.log
chmod 666 /var/log/*.log

# 配置 Nginx
cp /opt/chromaadapt-ai/backend/nginx.conf /etc/nginx/sites-available/chromaadapt
ln -s /etc/nginx/sites-available/chromaadapt /etc/nginx/sites-enabled/

# 启动服务
systemctl daemon-reload
systemctl enable webhook chroma-backend nginx
systemctl start webhook chroma-backend nginx

echo "安装完成！请配置 Gitee WebHook"
INSTALL_SCRIPT
```

---

## 提交代码后自动部署流程

```
1. 本地 git push 到 Gitee
       ↓
2. Gitee 服务器收到 push 事件
       ↓
3. Gitee 向服务器 http://IP:9000/webhook 发送 POST 请求
       ↓
4. webhook_server.py 接收请求，验证后触发 deploy.sh
       ↓
5. deploy.sh 自动执行：
   - git pull 拉取最新代码
   - pip install 更新后端依赖
   - npm install + npm run build 构建前端
   - systemctl restart chroma-backend 重启后端
       ↓
6. 完成！访问你的域名即可看到更新后的网站
```
