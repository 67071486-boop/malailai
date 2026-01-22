scp -r -i C:\Users\Administrator\.ssh\id_rsa . ubuntu@122.51.64.116:~/wxcloudrun-project

# 常用服务器与项目运行指令（Ubuntu）

以下命令在 Ubuntu 服务器与本地开发时都很常用。把它们放在项目根，便于团队共享。

## 前提 / 安装基础工具
（首次在服务器上运行）
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git unzip rsync openssh-client
```

## 在项目目录创建并使用虚拟环境
```bash
# 进入项目目录
cd ~/wxcloudrun-development   # 或项目实际路径

# 创建虚拟环境（目录名可为 .venv / venv）
python3 -m venv .venv

# 激活
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

## 启动应用（开发）
```bash
# run.py 接受 host 和 port
python run.py 0.0.0.0 8080

# 后台启动（将 stdout/stderr 写入日志）
nohup python run.py 0.0.0.0 5000 > app.log 2>&1 &
```

## 生产运行（推荐使用 gunicorn + systemd/nginx）
```bash
# 使用 gunicorn（module: object 为 wxcloudrun:app）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 wxcloudrun:app

# 示例 systemd 单元（保存为 /etc/systemd/system/wxcloudrun.service）
# [Unit]
# Description=wxcloudrun flask app
# After=network.target
#
# [Service]
# User=ubuntu
# WorkingDirectory=/home/ubuntu/wxcloudrun-project
# Environment="PATH=/home/ubuntu/wxcloudrun-project/.venv/bin"
# ExecStart=/home/ubuntu/wxcloudrun-project/.venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 wxcloudrun:app
# Restart=always
#
# [Install]
# WantedBy=multi-user.target

# 启用/查看状态
sudo systemctl daemon-reload
sudo systemctl enable --now wxcloudrun
sudo systemctl status wxcloudrun
sudo journalctl -u wxcloudrun -f
```

## 上传 / 同步项目文件
- 简单 scp 递归上传（不会删除远端额外文件）
```powershell
scp -r -i C:\Users\Administrator\.ssh\id_rsa . ubuntu@122.51.64.116:~/wxcloudrun-project
```

- 推荐增量同步（在 WSL / Linux 下执行）
```bash
# dry-run 先预览
rsync -avzn --progress --exclude='.venv' --exclude='.git' ./ ubuntu@122.51.64.116:~/wxcloudrun-project/

# 真同步（小心使用 --delete）
rsync -avz --progress --delete -e "ssh -i /home/<user>/.ssh/id_rsa" --exclude='.venv' --exclude='.git' ./ ubuntu@122.51.64.116:~/wxcloudrun-project/
```

## 环境变量 / .env
- 建议使用 `.env` 文件存放机密与配置（`python-dotenv` 已被项目使用）。示例：
```
MONGO_URI=mongodb://user:pass@host:port/admin?replicaSet=...
WXWORK_SUITE_ID=...
WXWORK_SUITE_SECRET=...
WXWORK_TOKEN=...
WXWORK_ENCODING_AES_KEY=...
```

在 shell 中导出（临时）或放在 systemd Environment 中：
```bash
export MONGO_URI="..."
```

## 日志与调试
```bash
# 查看 stdout 日志
tail -f app.log

# systemd 服务日志
sudo journalctl -u wxcloudrun -f

# 查看 Flask 运行情况（开发）
ps aux | grep python
```

## 数据库 & 测试脚本
```bash
# 快速测试向 Mongo 写入（仓库含 mongo_insert_test.py）
python mongo_insert_test.py

# 若需要进入 Mongo shell（安装 mongo 客户端）
sudo apt install -y mongodb-clients
mongo "<connection-string>"
```

## 常见操作速查
- 检查是否激活虚拟环境：`echo $VIRTUAL_ENV`
- 查找虚拟环境：`find $HOME -type f -path "*/bin/activate" 2>/dev/null`
- 删除虚拟环境：`rm -rf .venv`

## 注意事项
- `wxcloudrun/services/scheduler.py` 使用 APScheduler，开发时避免 Flask 自动重载导致 scheduler 重复启动（生产用 gunicorn/systemd）。
- 配置项与密钥必须通过环境变量或安全配置管理，不要把密钥提交到 Git。

---
如需我把这份文件提交（git commit & push）或者在服务器上按这些步骤执行（创建 venv、安装依赖、上传代码、启动服务），告诉我你要我先做哪一步。
