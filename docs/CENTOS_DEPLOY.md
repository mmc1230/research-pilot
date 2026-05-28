# ResearchPilot CentOS 服务器部署指南

这份文档说明如何把 ResearchPilot 部署到 CentOS 服务器上，并使用 systemd 托管 FastAPI 后端和 Streamlit 前端。

推荐部署形态：

```text
Nginx :80/:443
  -> Streamlit UI 127.0.0.1:8502
  -> FastAPI API 127.0.0.1:8000
systemd
  -> researchpilot-api.service
  -> researchpilot-ui.service
```

## 1. 服务器准备

登录服务器：

```bash
ssh root@your_server_ip
```

安装基础依赖：

```bash
yum update -y
yum install -y git gcc gcc-c++ make openssl-devel bzip2-devel libffi-devel zlib-devel sqlite-devel nginx
```

如果系统 Python 版本低于 3.10，建议安装 Python 3.11 或 3.12。CentOS 7/8 常见做法是使用源码安装或 pyenv。下面以 Python 3.12 源码安装为例：

```bash
cd /usr/local/src
curl -O https://www.python.org/ftp/python/3.12.8/Python-3.12.8.tgz
tar -xzf Python-3.12.8.tgz
cd Python-3.12.8
./configure --enable-optimizations
make -j 2
make altinstall
```

确认版本：

```bash
python3.12 --version
```

## 2. 创建运行用户

```bash
useradd --system --create-home --shell /bin/bash researchpilot
mkdir -p /opt/research_pilot
chown -R researchpilot:researchpilot /opt/research_pilot
```

## 3. 上传或拉取项目代码

如果代码在 Git 仓库中：

```bash
sudo -u researchpilot git clone https://your-git-repo-url.git /opt/research_pilot
```

如果你从本地上传，可以使用 `scp`：

```bash
scp -r D:/Projects/rag-agent/research_pilot root@your_server_ip:/opt/research_pilot
chown -R researchpilot:researchpilot /opt/research_pilot
```

## 4. 创建虚拟环境并安装依赖

```bash
cd /opt/research_pilot
sudo -u researchpilot python3.12 -m venv .venv
sudo -u researchpilot .venv/bin/python -m pip install --upgrade pip
sudo -u researchpilot .venv/bin/python -m pip install -r requirements.txt
```

如果服务器访问 PyPI 慢，可以使用镜像源：

```bash
sudo -u researchpilot .venv/bin/python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## 5. 配置环境变量

```bash
cd /opt/research_pilot
sudo -u researchpilot cp .env.production.example .env
```

编辑 `.env`：

```bash
vim /opt/research_pilot/.env
```

离线演示可以保持：

```env
EMBEDDING_PROVIDER=fake
```

如果需要 OpenAI embedding 和模型回答：

```env
OPENAI_API_KEY=你的_API_Key
EMBEDDING_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

创建数据目录：

```bash
sudo -u researchpilot mkdir -p /opt/research_pilot/data/uploads /opt/research_pilot/data/vector_db /opt/research_pilot/data/projects
```

## 6. 本地启动测试

先测试后端：

```bash
cd /opt/research_pilot
sudo -u researchpilot .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端检查：

```bash
curl http://127.0.0.1:8000/health
```

再测试前端：

```bash
cd /opt/research_pilot
sudo -u researchpilot .venv/bin/streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8502 --server.headless true
```

## 7. 配置 systemd

复制服务文件：

```bash
cp /opt/research_pilot/deploy/researchpilot-api.service /etc/systemd/system/researchpilot-api.service
cp /opt/research_pilot/deploy/researchpilot-ui.service /etc/systemd/system/researchpilot-ui.service
```

加载并启动：

```bash
systemctl daemon-reload
systemctl enable researchpilot-api
systemctl enable researchpilot-ui
systemctl start researchpilot-api
systemctl start researchpilot-ui
```

查看状态：

```bash
systemctl status researchpilot-api
systemctl status researchpilot-ui
```

查看日志：

```bash
journalctl -u researchpilot-api -f
journalctl -u researchpilot-ui -f
```

## 8. 配置 Nginx

复制 Nginx 配置：

```bash
cp /opt/research_pilot/deploy/nginx-researchpilot.conf /etc/nginx/conf.d/researchpilot.conf
```

编辑域名：

```bash
vim /etc/nginx/conf.d/researchpilot.conf
```

把：

```nginx
server_name your-domain.com;
```

改成你的域名或服务器 IP：

```nginx
server_name your-domain.com;
```

检查配置：

```bash
nginx -t
```

启动 Nginx：

```bash
systemctl enable nginx
systemctl restart nginx
```

## 9. 防火墙

如果使用 firewalld：

```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

如果你暂时不使用 Nginx，而是直接暴露 Streamlit 端口：

```bash
firewall-cmd --permanent --add-port=8502/tcp
firewall-cmd --reload
```

生产环境更推荐只开放 80/443，由 Nginx 反向代理到本地端口。

## 10. HTTPS

如果有域名，可以安装 Certbot：

```bash
yum install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

完成后访问：

```text
https://your-domain.com
```

## 11. 前端后端地址

当前 Streamlit 前端左侧栏有“后端地址”输入框。服务器部署时，如果用户通过 Nginx 访问页面，可以填：

```text
http://your-domain.com/api
```

如果只在服务器本机调试，则填：

```text
http://127.0.0.1:8000
```

## 12. 常见问题

### 上传文件失败

检查目录权限：

```bash
chown -R researchpilot:researchpilot /opt/research_pilot/data
```

检查 Nginx 上传大小限制：

```nginx
client_max_body_size 100M;
```

### Chroma 或 SQLite 写入失败

确认运行用户有写权限：

```bash
ls -ld /opt/research_pilot/data
```

### 服务启动失败

查看日志：

```bash
journalctl -u researchpilot-api -n 100 --no-pager
journalctl -u researchpilot-ui -n 100 --no-pager
```

### 服务器内存不足

Chroma、LangChain 和 Streamlit 都会占用一定内存。建议服务器至少：

```text
2 CPU / 4 GB RAM
```

如果使用 OpenAI embedding，CPU 压力会小一些；如果后续换成本地 embedding 模型，建议更高配置。

## 13. 更新部署

如果使用 Git：

```bash
cd /opt/research_pilot
sudo -u researchpilot git pull
sudo -u researchpilot .venv/bin/python -m pip install -r requirements.txt
systemctl restart researchpilot-api
systemctl restart researchpilot-ui
```
