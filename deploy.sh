#!/bin/bash
# 量化交易平台 - 部署脚本
# Usage: ./deploy.sh

set -e

echo "=========================================="
echo "量化交易平台部署脚本"
echo "=========================================="
echo ""

# 配置
PROJECT_NAME="quant-trading-platform"
PROJECT_DIR="/opt/$PROJECT_NAME"
USER="quant"
SERVICE_NAME="quant-trading"

echo "[1/8] 检查系统环境..."
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行"
    exit 1
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python版本: $PYTHON_VERSION"

echo ""
echo "[2/8] 创建系统用户..."
if ! id "$USER" &>/dev/null; then
    useradd -m -s /bin/bash "$USER"
    echo "  用户 $USER 已创建"
else
    echo "  用户 $USER 已存在"
fi

echo ""
echo "[3/8] 安装系统依赖..."
apt-get update -qq
apt-get install -y -qq \
    python3-pip \
    python3-venv \
    git \
    cron \
    supervisor \
    nginx \
    htop \
    tree

echo "  系统依赖安装完成"

echo ""
echo "[4/8] 创建项目目录..."
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/config"
chown -R "$USER:$USER" "$PROJECT_DIR"
echo "  项目目录: $PROJECT_DIR"

echo ""
echo "[5/8] 复制项目文件..."
# 假设从当前目录复制
if [ -d "src" ]; then
    cp -r src "$PROJECT_DIR/"
    cp -r tests "$PROJECT_DIR/"
    cp -r docs "$PROJECT_DIR/"
    cp requirements.txt "$PROJECT_DIR/"
    cp *.py "$PROJECT_DIR/" 2>/dev/null || true
    echo "  项目文件已复制"
else
    echo "  警告: 未找到src目录，请手动复制项目文件"
fi

chown -R "$USER:$USER" "$PROJECT_DIR"

echo ""
echo "[6/8] 创建Python虚拟环境..."
sudo -u "$USER" bash -c "
    cd $PROJECT_DIR
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
"
echo "  虚拟环境创建完成"

echo ""
echo "[7/8] 配置环境变量..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > "$PROJECT_DIR/.env" << 'EOF'
# Tushare Pro API Token
# 请访问 https://tushare.pro/register 注册获取
TUSHARE_TOKEN=your_token_here

# 日志级别
LOG_LEVEL=INFO

# 数据目录
DATA_DIR=./data

# 交易配置
INITIAL_CAPITAL=100000
MAX_POSITION_PCT=0.2
MAX_DRAWDOWN_PCT=0.15
EOF
    chown "$USER:$USER" "$PROJECT_DIR/.env"
    echo "  环境变量模板已创建: $PROJECT_DIR/.env"
    echo "  ⚠️  请编辑 .env 文件，填入你的 TUSHARE_TOKEN"
else
    echo "  环境变量文件已存在"
fi

echo ""
echo "[8/8] 设置目录权限..."
chown -R "$USER:$USER" "$PROJECT_DIR"
chmod 750 "$PROJECT_DIR"
chmod 600 "$PROJECT_DIR/.env"

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo "=========================================="
echo ""
echo "项目目录: $PROJECT_DIR"
echo "运行用户: $USER"
echo ""
echo "下一步:"
echo "1. 编辑环境变量: sudo nano $PROJECT_DIR/.env"
echo "2. 运行测试: sudo -u $USER bash -c 'cd $PROJECT_DIR && source venv/bin/activate && python tests/test_full_system.py'"
echo "3. 配置定时任务: ./setup_cron.sh"
echo ""
