这是分支 企微第三方应用

## Ubuntu 常用指令（本仓库 / 服务器）

下文默认你在 **Ubuntu 服务器**（如 `122.51.64.116`）上操作；Python 虚拟环境、systemd、Nginx 等完整步骤见后面章节。

### 登录服务器

```bash
ssh ubuntu@122.51.64.116
```

需本机已配置 SSH 公钥，才能做到免密登录。

### 首次克隆仓库（服务器或本机均可）

```bash
git clone git@github.com:67071486-boop/wecom-development.git
cd wecom-development
```

### 日常同步代码（服务器上）

```bash
cd /你的项目目录   # 生产示例：/opt/wecom-prod（见「生产环境详细流程」）
git pull origin main
```

若 `requirements.txt` 有变更，先 `source .venv/bin/activate` 再 `pip install -r requirements.txt`。

### 发布改动后的典型流程

1. **本机**：改代码 → `git add` → `git commit` → `git push origin main`
2. **服务器**：`git pull origin main` →（必要时装依赖）→ `sudo systemctl restart wecom-prod` → `sudo systemctl status wecom-prod`

本机提交示例：

```bash
git add -A 暂存更改
git commit -m "描述本次改动"
git push origin main 打包提交
```

### 快速看服务是否在跑

```bash
sudo systemctl status wecom-prod
sudo journalctl -u wecom-prod -n 50 --no-pager
```

## 前提 / 安装基础工具
（首次在服务器上运行）
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git unzip rsync openssh-client
```

# 创建虚拟环境（目录名可为 .venv / venv）
python3 -m venv .venv

# 激活
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate


## 启动应用（开发）
```bash
# run.py 接受 host 和 port
python3 run.py 0.0.0.0 8081


## 生产环境详细流程（本项目推荐）
以下步骤适用于 Ubuntu + systemd + Nginx，项目监听 8080，由 Nginx 反代到域名。

### 1) 目录与虚拟环境
```bash
cd /opt/wecom-prod   # 以实际路径为准
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 2) 环境变量（推荐 systemd EnvironmentFile）
```bash
sudo nano /etc/wecom-prod.env
```
示例内容（替换为真实值）：
```
MONGO_URI=...
WXWORK_CORP_ID=...
WXWORK_SUITE_ID=...
WXWORK_SUITE_SECRET=...
WXWORK_TOKEN=...
WXWORK_ENCODING_AES_KEY=...
WXWORK_OAUTH_REDIRECT=...   # 可选
```
```bash
sudo chmod 600 /etc/wecom-prod.env
```

### 3) systemd 服务（生产常驻）
```bash
sudo nano /etc/systemd/system/wecom-prod.service

[Unit]
Description=wecom-prod
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/wecom-prod
EnvironmentFile=/etc/wecom-prod.env
ExecStart=/opt/wecom-prod/.venv/bin/gunicorn -w 2 -b 127.0.0.1:8080 "wxcloudrun:app"
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wecom-prod
sudo systemctl restart wecom-prod
sudo systemctl status wecom-prod
```

### 4) Nginx 反向代理（绑定域名）
```bash
sudo nano /etc/nginx/sites-available/wecom.suqing.chat
```
```
server {
	listen 80;
	listen 443 ssl;
	server_name wecom.suqing.chat;

	ssl_certificate /etc/nginx/ssl/_.suqing.chat.pem;
	ssl_certificate_key /etc/nginx/ssl/_.suqing.chat.key;

	location / {
		proxy_pass http://127.0.0.1:8080;
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;
	}
}
```
```bash
sudo ln -s /etc/nginx/sites-available/wecom.suqing.chat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5) 端口与安全组
- 若仅走 Nginx：只开放 80/443。
- 若需要直接暴露服务：将 systemd 的 `-b 127.0.0.1:8080` 改为 `-b 0.0.0.0:8080`，并在腾讯云安全组/防火墙开放 8080（不推荐）。
- 
sudo ufw allow 8081/tcp

### 6) 运行与排查
```bash
sudo systemctl status wecom-prod

sudo journalctl -u wecom-prod -f 
```

## 生产环境注意事项（本项目）
- 回调与鉴权依赖环境变量（如 WXWORK_TOKEN、WXWORK_ENCODING_AES_KEY），务必与企业微信后台一致。
- 生产建议使用 Nginx 反代 + HTTPS，避免直接暴露 8080。
- `wxcloudrun/services/scheduler.py` 会启动定时任务，避免用 Flask 自动重载模式（生产用 systemd/gunicorn）。
- MongoDB 连接使用 `MONGO_URI`，不要把真实连接串写入仓库。
- 若服务异常重启或返回 502，先看 systemd 日志与 Nginx 错误日志。


## 环境变量 / .env
- 建议使用 `.env` 文件存放机密与配置（`python-dotenv` 已被项目使用）。示例：

MONGO_URI=mongodb://user:pass@host:port/admin?replicaSet=...
WXWORK_SUITE_ID=...
WXWORK_SUITE_SECRET=...
WXWORK_TOKEN=...
WXWORK_ENCODING_AES_KEY=...

## 日志与调试
bash
# 查看 stdout 日志
tail -f app.log

# systemd 服务日志
sudo journalctl -u wxcloudrun -f

# 查看 Flask 运行情况（开发）
ps aux | grep python


## 常见操作速查
- 检查是否激活虚拟环境：`echo $VIRTUAL_ENV`
- 查找虚拟环境：`find $HOME -type f -path "*/bin/activate" 2>/dev/null`
- 删除虚拟环境：`rm -rf .venv`

## 注意事项
- `wxcloudrun/services/scheduler.py` 使用 APScheduler，开发时避免 Flask 自动重载导致 scheduler 重复启动（生产用 gunicorn/systemd）。
- 配置项与密钥必须通过环境变量或安全配置管理，不要把密钥提交到 Git。


