"""
AI模型集成 - 时序预测模型
"""
from typing import Optional, Tuple, List
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from loguru import logger


class TimeSeriesDataset(Dataset):
    """时序数据集"""
    
    def __init__(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str = 'close',
        seq_len: int = 20,
        pred_len: int = 1
    ):
        self.seq_len = seq_len
        self.pred_len = pred_len
        self.features = df[feature_cols].values
        self.targets = df[target_col].values
        
    def __len__(self):
        return len(self.features) - self.seq_len - self.pred_len + 1
    
    def __getitem__(self, idx):
        x = self.features[idx:idx + self.seq_len]
        y = self.targets[idx + self.seq_len:idx + self.seq_len + self.pred_len]
        return torch.FloatTensor(x), torch.FloatTensor(y)


class LSTMModel(nn.Module):
    """LSTM时序预测模型"""
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        output_size: int = 1,
        dropout: float = 0.2
    ):
        super().__init__()
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, output_size)
        )
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        # 只取最后一个时间步
        return self.fc(lstm_out[:, -1, :])


class TransformerModel(nn.Module):
    """Transformer时序预测模型"""
    
    def __init__(
        self,
        input_size: int,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 4,
        output_size: int = 1,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_projection = nn.Linear(input_size, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        
        self.fc = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, output_size)
        )
    
    def forward(self, x):
        x = self.input_projection(x)
        x = self.transformer(x)
        return self.fc(x[:, -1, :])


class PricePredictor:
    """价格预测器"""
    
    def __init__(
        self,
        model_type: str = 'lstm',
        seq_len: int = 20,
        device: str = 'cpu'
    ):
        self.model_type = model_type
        self.seq_len = seq_len
        self.device = device
        self.model: Optional[nn.Module] = None
        self.feature_cols: Optional[List[str]] = None
        self.target_scaler = None
    
    def build_model(self, input_size: int):
        """构建模型"""
        if self.model_type == 'lstm':
            self.model = LSTMModel(input_size=input_size)
        elif self.model_type == 'transformer':
            self.model = TransformerModel(input_size=input_size)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        self.model.to(self.device)
        logger.info(f"模型构建完成: {self.model_type}, 参数量: {sum(p.numel() for p in self.model.parameters())}")
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str = 'close',
        train_ratio: float = 0.8,
        batch_size: int = 32
    ) -> Tuple[DataLoader, DataLoader]:
        """
        准备数据
        """
        self.feature_cols = feature_cols
        
        # 标准化
        from sklearn.preprocessing import StandardScaler
        self.target_scaler = StandardScaler()
        
        df_scaled = df.copy()
        df_scaled[feature_cols] = StandardScaler().fit_transform(df[feature_cols])
        df_scaled[target_col] = self.target_scaler.fit_transform(df[[target_col]])
        
        # 划分训练集和验证集
        train_size = int(len(df_scaled) * train_ratio)
        train_df = df_scaled.iloc[:train_size]
        val_df = df_scaled.iloc[train_size:]
        
        # 创建数据集
        train_dataset = TimeSeriesDataset(train_df, feature_cols, target_col, self.seq_len)
        val_dataset = TimeSeriesDataset(val_df, feature_cols, target_col, self.seq_len)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        return train_loader, val_loader
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 50,
        lr: float = 0.001,
        patience: int = 10
    ) -> List[Dict]:
        """训练模型"""
        if self.model is None:
            raise ValueError("请先调用build_model构建模型")
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()
        
        best_val_loss = float('inf')
        patience_counter = 0
        history = []
        
        for epoch in range(epochs):
            # 训练
            self.model.train()
            train_loss = 0
            for x, y in train_loader:
                x, y = x.to(self.device), y.to(self.device)
                
                optimizer.zero_grad()
                pred = self.model(x)
                loss = criterion(pred, y)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            
            # 验证
            self.model.eval()
            val_loss = 0
            with torch.no_grad():
                for x, y in val_loader:
                    x, y = x.to(self.device), y.to(self.device)
                    pred = self.model(x)
                    val_loss += criterion(pred, y).item()
            
            val_loss /= len(val_loader)
            
            history.append({
                'epoch': epoch + 1,
                'train_loss': train_loss,
                'val_loss': val_loss
            })
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch + 1}")
                    break
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch + 1}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
        
        return history
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """预测"""
        if self.model is None or self.feature_cols is None:
            raise ValueError("模型未训练")
        
        self.model.eval()
        
        # 准备数据
        features = df[self.feature_cols].values[-self.seq_len:]
        x = torch.FloatTensor(features).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            pred = self.model(x).cpu().numpy()
        
        # 反标准化
        if self.target_scaler:
            pred = self.target_scaler.inverse_transform(pred)
        
        return pred
    
    def save(self, path: str):
        """保存模型"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_type': self.model_type,
            'feature_cols': self.feature_cols,
            'seq_len': self.seq_len
        }, path)
        logger.info(f"模型已保存: {path}")
    
    def load(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        
        self.model_type = checkpoint['model_type']
        self.feature_cols = checkpoint['feature_cols']
        self.seq_len = checkpoint['seq_len']
        
        self.build_model(len(self.feature_cols))
        self.model.load_state_dict(checkpoint['model_state_dict'])
        logger.info(f"模型已加载: {path}")
