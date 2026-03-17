#!/bin/bash
# 量化交易平台 - 服务管理配置
# Usage: ./setup_services.sh

set -e

echo "=========================================="
echo "配置系统服务"
echo "=========================================="
echo ""

PROJECT_DIR="/opt/quant-trading-platform"
USER="quant"

echo "[1/3] 创建supervisor配置..."

# 创建supervisor配置文件
cat > /etc/supervisor/conf.d/quant-trading.conf << 'EOF'
[program:quant-trading-api]
command=/opt/quant-trading-platform/venv/bin/python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000
autostart=false
autorestart=true
startsecs=5
startretries=3
user=quant
directory=/opt/quant-trading-platform
redirect_stderr=true
stdout_logfile=/opt/quant-trading-platform/logs/api.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PYTHONPATH="/opt/quant-trading-platform/src"

[program:quant-trading-web]
command=/opt/quant-trading-platform/venv/bin/streamlit run web_ui.py --server.port 8501 --server.address 0.0.0.0
autostart=false
autorestart=true
startsecs=10
startretries=3
user=quant
directory=/opt/quant-trading-platform
redirect_stderr=true
stdout_logfile=/opt/quant-trading-platform/logs/web.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PYTHONPATH="/opt/quant-trading-platform/src"

[group:quant-trading]
programs=quant-trading-api,quant-trading-web
EOF

echo "  ✓ supervisor配置已创建"

echo ""
echo "[2/3] 创建系统服务..."

# 创建systemd服务
cat > /etc/systemd/system/quant-trading.service << 'EOF'
[Unit]
Description=Quant Trading Platform
After=network.target

[Service]
Type=forking
User=quant
Group=quant
WorkingDirectory=/opt/quant-trading-platform
ExecStart=/usr/bin/supervisord -c /etc/supervisor/supervisord.conf
ExecReload=/usr/bin/supervisorctl reload
ExecStop=/usr/bin/supervisorctl shutdown
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "  ✓ systemd服务已创建"

echo ""
echo "[3/3] 创建启动脚本..."

cat > "$PROJECT_DIR/start.sh" << 'SCRIPT'
#!/bin/bash
# 启动量化交易平台服务

echo "启动量化交易平台..."

# 启动supervisor管理的服务
sudo supervisorctl start quant-trading-api quant-trading-web

echo "服务状态:"
sudo supervisorctl status

echo ""
echo "访问地址:"
echo "  API: http://localhost:8000"
echo "  Web: http://localhost:8501"
SCRIPT

chmod +x "$PROJECT_DIR/start.sh"

cat > "$PROJECT_DIR/stop.sh" << 'SCRIPT'
#!/bin/bash
# 停止量化交易平台服务

echo "停止量化交易平台..."
sudo supervisorctl stop quant-trading-api quant-trading-web
echo "已停止"
SCRIPT

chmod +x "$PROJECT_DIR/stop.sh"

cat > "$PROJECT_DIR/status.sh" << 'SCRIPT'
#!/bin/bash
# 查看服务状态

echo "服务状态:"
sudo supervisorctl status quant-trading-api quant-trading-web

echo ""
echo "系统资源:"
free -h | grep -E "(Mem|Swap)"

echo ""
echo "磁盘使用:"
df -h /opt/quant-trading-platform

echo ""
echo "最近日志:"
tail -n 10 /opt/quant-trading-platform/logs/api.log 2>/dev/null || echo "暂无API日志"
SCRIPT

chmod +x "$PROJECT_DIR/status.sh"

chown "$USER:$USER" "$PROJECT_DIR"/*.sh
echo "  ✓ 启动脚本已创建"

echo ""
echo "=========================================="
echo "✅ 服务配置完成!"
echo "=========================================="
echo ""
echo "管理命令:"
echo "  启动: $PROJECT_DIR/start.sh"
echo "  停止: $PROJECT_DIR/stop.sh"
echo "  状态: $PROJECT_DIR/status.sh"
echo ""
echo "Supervisor管理:"
echo "  sudo supervisorctl start quant-trading-api"
echo "  sudo supervisorctl start quant-trading-web"
echo "  sudo supervisorctl status"
echo ""
