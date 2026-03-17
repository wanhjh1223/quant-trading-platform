#!/bin/bash
# 量化交易平台 - 定时任务配置脚本
# Usage: ./setup_cron.sh

set -e

echo "=========================================="
echo "配置定时任务"
echo "=========================================="
echo ""

PROJECT_DIR="/opt/quant-trading-platform"
USER="quant"
LOG_DIR="$PROJECT_DIR/logs"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

echo "[1/3] 创建定时任务脚本..."

# 创建数据更新脚本
cat > "$PROJECT_DIR/run_data_update.sh" << 'SCRIPT'
#!/bin/bash
# 数据更新任务
set -e

PROJECT_DIR="/opt/quant-trading-platform"
LOG_FILE="$PROJECT_DIR/logs/data_update_$(date +%Y%m%d).log"

source "$PROJECT_DIR/venv/bin/activate"
cd "$PROJECT_DIR"

echo "[$(date)] 开始数据更新..." >> "$LOG_FILE"

# 运行数据下载脚本
python3 -c "
import sys
sys.path.insert(0, 'src')
from data.tushare_loader import DataDownloader
import os
from dotenv import load_dotenv

load_dotenv()

downloader = DataDownloader(
    data_dir='./data',
    token=os.getenv('TUSHARE_TOKEN')
)

# 下载沪深300成分股（用于测试）
import pandas as pd
df = downloader.source.get_stock_list('SSE')
print(f'获取到 {len(df)} 只股票')

# 下载前10只
downloaded = downloader.download_all_stocks(
    exchange='SSE',
    max_stocks=10
)
print(f'成功下载 {len(downloaded)} 只股票')
" 2>> "$LOG_FILE"

echo "[$(date)] 数据更新完成" >> "$LOG_FILE"
SCRIPT

chmod +x "$PROJECT_DIR/run_data_update.sh"
chown "$USER:$USER" "$PROJECT_DIR/run_data_update.sh"
echo "  ✓ 数据更新脚本已创建"

# 创建策略运行脚本
cat > "$PROJECT_DIR/run_strategy.sh" << 'SCRIPT'
#!/bin/bash
# 策略运行任务
set -e

PROJECT_DIR="/opt/quant-trading-platform"
LOG_FILE="$PROJECT_DIR/logs/strategy_$(date +%Y%m%d).log"
RESULT_FILE="$PROJECT_DIR/logs/signals_$(date +%Y%m%d).json"

source "$PROJECT_DIR/venv/bin/activate"
cd "$PROJECT_DIR"

echo "[$(date)] 开始运行策略..." >> "$LOG_FILE"

python3 -c "
import sys
sys.path.insert(0, 'src')
import json
import pandas as pd
from datetime import datetime
from data.storage import DataStore
from data.features import FeatureEngineer
from strategies.technical_strategies import DoubleMAStrategy

# 加载数据
store = DataStore('./data')
symbols = store.list_saved_symbols()

if not symbols:
    print('没有数据，请先运行数据更新')
    exit(0)

print(f'分析 {len(symbols)} 只股票...')

signals = []
for symbol in symbols[:5]:  # 只分析前5只
    try:
        df = store.load_daily_data(symbol)
        if df is None or len(df) < 60:
            continue
        
        # 计算特征
        engineer = FeatureEngineer()
        df = engineer.calculate_all_features(df)
        
        # 运行双均线策略
        strategy = DoubleMAStrategy(short=5, long=20)
        df = strategy.generate_signals(df)
        
        # 检查最新信号
        latest_signal = df['signal'].iloc[-1]
        latest_price = df['close'].iloc[-1]
        
        if latest_signal != 0:
            signals.append({
                'symbol': symbol,
                'signal': 'BUY' if latest_signal == 1 else 'SELL',
                'price': float(latest_price),
                'date': str(df.index[-1]) if hasattr(df, 'index') else str(len(df)),
                'timestamp': datetime.now().isoformat()
            })
            print(f'{symbol}: {\"买入\" if latest_signal == 1 else \"卖出\"}信号 @ {latest_price:.2f}')
    except Exception as e:
        print(f'{symbol} 处理失败: {e}')

# 保存信号
with open('$RESULT_FILE', 'w') as f:
    json.dump(signals, f, indent=2)

print(f'发现 {len(signals)} 个交易信号')
" 2>> "$LOG_FILE"

echo "[$(date)] 策略运行完成" >> "$LOG_FILE"
SCRIPT

chmod +x "$PROJECT_DIR/run_strategy.sh"
chown "$USER:$USER" "$PROJECT_DIR/run_strategy.sh"
echo "  ✓ 策略运行脚本已创建"

# 创建监控脚本
cat > "$PROJECT_DIR/run_monitor.sh" << 'SCRIPT'
#!/bin/bash
# 系统监控任务

PROJECT_DIR="/opt/quant-trading-platform"
LOG_FILE="$PROJECT_DIR/logs/monitor_$(date +%Y%m%d).log"

echo "[$(date)] 系统状态检查" >> "$LOG_FILE"
echo "磁盘使用:" >> "$LOG_FILE"
df -h "$PROJECT_DIR" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "内存使用:" >> "$LOG_FILE"
free -h >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "数据目录大小:" >> "$LOG_FILE"
du -sh "$PROJECT_DIR/data" 2>/dev/null || echo "数据目录不存在" >> "$LOG_FILE"
SCRIPT

chmod +x "$PROJECT_DIR/run_monitor.sh"
chown "$USER:$USER" "$PROJECT_DIR/run_monitor.sh"
echo "  ✓ 监控脚本已创建"

echo ""
echo "[2/3] 配置crontab..."

# 创建crontab内容
CRON_CONTENT="# 量化交易平台定时任务
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
PROJECT_DIR=$PROJECT_DIR

# 每天9:00更新数据（开盘前）
0 9 * * 1-5 $PROJECT_DIR/run_data_update.sh

# 每天15:30运行策略（收盘后）
30 15 * * 1-5 $PROJECT_DIR/run_strategy.sh

# 每小时监控
0 * * * * $PROJECT_DIR/run_monitor.sh

# 每周清理旧日志（保留30天）
0 0 * * 0 find $PROJECT_DIR/logs -name '*.log' -mtime +30 -delete
"

# 写入crontab
echo "$CRON_CONTENT" | crontab -u "$USER" -
echo "  ✓ crontab 已配置"

echo ""
echo "[3/3] 验证配置..."
crontab -u "$USER" -l | head -20
echo ""

echo "=========================================="
echo "✅ 定时任务配置完成!"
echo "=========================================="
echo ""
echo "任务计划:"
echo "  • 工作日 9:00  - 数据更新"
echo "  • 工作日 15:30 - 策略运行"
echo "  • 每小时      - 系统监控"
echo "  • 每周日 0:00 - 日志清理"
echo ""
echo "日志位置: $LOG_DIR"
echo ""
echo "手动测试:"
echo "  sudo -u $USER $PROJECT_DIR/run_data_update.sh"
echo "  sudo -u $USER $PROJECT_DIR/run_strategy.sh"
echo ""
