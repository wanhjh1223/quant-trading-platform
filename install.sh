#!/bin/bash
# 量化交易平台 - 一键部署脚本
# Usage: sudo ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="quant-trading-platform"
PROJECT_DIR="/opt/$PROJECT_NAME"

echo "=========================================="
echo "量化交易平台 - 一键安装"
echo "=========================================="
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 sudo 运行"
    exit 1
fi

echo "📋 安装信息:"
echo "  项目目录: $PROJECT_DIR"
echo "  当前目录: $SCRIPT_DIR"
echo ""

# 步骤1: 运行部署脚本
echo "🚀 [步骤1/4] 执行部署..."
cd "$SCRIPT_DIR"
bash deploy.sh

# 步骤2: 配置定时任务
echo ""
echo "⏰ [步骤2/4] 配置定时任务..."
bash setup_cron.sh

# 步骤3: 配置服务
echo ""
echo "🔧 [步骤3/4] 配置系统服务..."
bash setup_services.sh

# 步骤4: 启动定时任务
echo ""
echo "✅ [步骤4/4] 完成安装"
echo ""

# 显示最终状态
echo "=========================================="
echo "🎉 安装完成!"
echo "=========================================="
echo ""
echo "📁 项目位置: $PROJECT_DIR"
echo "👤 运行用户: quant"
echo ""
echo "⚙️ 配置环境变量:"
echo "   sudo nano $PROJECT_DIR/.env"
echo ""
echo "🧪 运行测试:"
echo "   sudo -u quant bash -c 'cd $PROJECT_DIR && source venv/bin/activate && python tests/test_full_system.py'"
echo ""
echo "📊 定时任务:"
echo "   crontab -u quant -l"
echo ""
echo "📝 手动运行策略:"
echo "   sudo -u quant $PROJECT_DIR/run_strategy.sh"
echo ""
echo "📈 查看日志:"
echo "   tail -f $PROJECT_DIR/logs/strategy_$(date +%Y%m%d).log"
echo ""
echo "=========================================="
