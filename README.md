# AI量化交易平台

基于LLM/VLM经验的A股AI驱动量化交易系统。

## 技术栈

- **数据层**: Tushare + akshare
- **存储**: Parquet + SQLite
- **计算**: Polars (向量化加速)
- **AI模型**: PyTorch + Transformers
- **回测**: 自研事件驱动回测引擎
- **可视化**: Streamlit

## 项目结构

```
quant-trading-platform/
├── src/
│   ├── data/          # 数据获取与处理
│   ├── models/        # AI模型 (时序预测/强化学习)
│   ├── strategies/    # 策略生成与回测
│   ├── execution/     # 交易执行
│   └── utils/         # 工具函数
├── tests/             # 单元测试
├── scripts/           # 运行脚本
├── configs/           # 配置文件
├── docs/              # 文档
└── data/              # 数据存储
    ├── raw/           # 原始数据
    ├── processed/     # 清洗后数据
    └── features/      # 特征数据
```

## 开发阶段

1. **阶段1**: 数据层搭建 (当前)
2. **阶段2**: 特征工程
3. **阶段3**: 策略回测引擎
4. **阶段4**: AI模型集成
5. **阶段5**: 交易执行
6. **阶段6**: 可视化界面

## 快速开始

```bash
pip install -r requirements.txt
python scripts/download_data.py --symbol 000001.SZ --start 20230101 --end 20241231
```
