"""
Training script for LSTM-based CPU forecasting model (PyTorch)
"""

import os
import numpy as np
import pandas as pd
from typing import Tuple
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load_cpu_data(data_dir: str = 'training/data/prometheus') -> pd.DataFrame:
    """
    Load CPU timeseries data
    
    Args:
        data_dir: Directory containing Prometheus data
        
    Returns:
        DataFrame with CPU metrics
    """
    csv_file = f"{data_dir}/cpu_timeseries.csv"
    
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Data file not found: {csv_file}")
    
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} CPU samples from {csv_file}")
    
    # Parse timestamp if it's a string
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
    
    return df


def prepare_sequences(data: np.ndarray, lookback: int = 60, forecast_horizon: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare sequences for LSTM training
    
    Args:
        data: 1D array of CPU values
        lookback: Number of past timesteps to use as input
        forecast_horizon: Number of future timesteps to predict
        
    Returns:
        Tuple of (X sequences, y targets)
    """
    X, y = [], []
    
    for i in range(len(data) - lookback - forecast_horizon + 1):
        X.append(data[i:(i + lookback)])
        y.append(data[i + lookback + forecast_horizon - 1])  # Predict the last value in forecast horizon
    
    return np.array(X), np.array(y)


def create_sequences(df: pd.DataFrame, lookback: int = 60, forecast_horizon: int = 10) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler]:
    """
    Create sequences from CPU data
    
    Args:
        df: DataFrame with CPU metrics
        lookback: Number of past timesteps
        forecast_horizon: Number of future timesteps
        
    Returns:
        Tuple of (X sequences, y targets, fitted scaler)
    """
    print("\nPreparing sequences...")
    
    # Extract CPU values
    cpu_values = df['cpu_usage'].values.reshape(-1, 1)
    
    # Scale data to [0, 1]
    scaler = MinMaxScaler(feature_range=(0, 1))
    cpu_scaled = scaler.fit_transform(cpu_values)
    
    # Create sequences
    X, y = prepare_sequences(cpu_scaled.flatten(), lookback=lookback, forecast_horizon=forecast_horizon)
    
    # Reshape X for LSTM [samples, timesteps, features]
    X = X.reshape((X.shape[0], X.shape[1], 1))
    
    print(f"Sequence shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    print(f"Lookback: {lookback} minutes")
    print(f"Forecast horizon: {forecast_horizon} minutes")
    
    return X, y, scaler


class LSTMModel(nn.Module):
    """LSTM model for CPU forecasting"""
    
    def __init__(self, input_size=1, hidden_size_1=128, hidden_size_2=64, dense_size=32):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_size_1, batch_first=True)
        self.dropout1 = nn.Dropout(0.2)
        self.lstm2 = nn.LSTM(hidden_size_1, hidden_size_2, batch_first=True)
        self.dropout2 = nn.Dropout(0.2)
        self.fc1 = nn.Linear(hidden_size_2, dense_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(dense_size, 1)
    
    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.dropout1(out)
        out, _ = self.lstm2(out)
        out = self.dropout2(out[:, -1, :])  # Take last timestep
        out = self.relu(self.fc1(out))
        out = self.fc2(out)
        return out


def build_lstm_model(lookback: int) -> LSTMModel:
    """
    Build LSTM model for CPU forecasting
    """
    print("\nBuilding LSTM model...")
    model = LSTMModel(input_size=1)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"LSTM model built - Total parameters: {total_params:,}")
    print(f"  Input: ({lookback}, 1) → LSTM(128) → LSTM(64) → Dense(32) → Dense(1)")
    return model


def train_lstm(model: LSTMModel, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 50, batch_size: int = 32):
    """
    Train LSTM model
    """
    print("\nTraining LSTM model...")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    
    train_x = torch.FloatTensor(X_train).to(device)
    train_y = torch.FloatTensor(y_train).to(device)
    val_x = torch.FloatTensor(X_val).to(device)
    val_y = torch.FloatTensor(y_val).to(device)
    
    train_dataset = TensorDataset(train_x, train_y)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5, patience=5, min_lr=1e-6)
    criterion = nn.MSELoss()
    
    best_val_loss = float('inf')
    patience = 10
    patience_counter = 0
    best_state = None
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            output = model(batch_x).squeeze(-1)
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch_x.size(0)
        train_loss /= len(train_x)
        
        model.eval()
        with torch.no_grad():
            val_output = model(val_x).squeeze(-1)
            val_loss = criterion(val_output, val_y).item()
            val_mae = torch.mean(torch.abs(val_output - val_y)).item()
        
        scheduler.step(val_loss)
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            lr = optimizer.param_groups[0]['lr']
            print(f"Epoch {epoch+1}/{epochs} - loss: {train_loss:.6f} - val_loss: {val_loss:.6f} - val_mae: {val_mae:.6f} - lr: {lr:.6f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break
    
    if best_state is not None:
        model.load_state_dict(best_state)
    
    print("Training complete!")
    return model


def evaluate_model(model: LSTMModel, X_test: np.ndarray, y_test: np.ndarray,
                  scaler: MinMaxScaler) -> dict:
    """
    Evaluate LSTM model performance
    """
    print("\nEvaluating model...")
    
    device = next(model.parameters()).device
    model.eval()
    with torch.no_grad():
        x_tensor = torch.FloatTensor(X_test).to(device)
        y_pred = model(x_tensor).squeeze(-1).cpu().numpy()
    
    # Calculate metrics on scaled data
    mse = np.mean((y_test - y_pred) ** 2)
    mae = np.mean(np.abs(y_test - y_pred))
    rmse = np.sqrt(mse)
    
    # Inverse transform for actual values
    y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
    y_pred_actual = scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
    
    mse_actual = np.mean((y_test_actual - y_pred_actual) ** 2)
    mae_actual = np.mean(np.abs(y_test_actual - y_pred_actual))
    rmse_actual = np.sqrt(mse_actual)
    
    # Calculate MAPE (avoiding division by zero)
    mape = np.mean(np.abs((y_test_actual - y_pred_actual) / (y_test_actual + 1e-8))) * 100
    
    metrics = {
        'mse': mse_actual,
        'mae': mae_actual,
        'rmse': rmse_actual,
        'mape': mape
    }
    
    print("\nModel Performance (on actual values):")
    print(f"MSE:  {metrics['mse']:.6f}")
    print(f"MAE:  {metrics['mae']:.6f}")
    print(f"RMSE: {metrics['rmse']:.6f}")
    print(f"MAPE: {metrics['mape']:.2f}%")
    
    return metrics


def plot_predictions(y_test: np.ndarray, y_pred: np.ndarray, scaler: MinMaxScaler,
                    output_dir: str = 'training/data/prometheus'):
    """
    Plot actual vs predicted values
    
    Args:
        y_test: Test targets
        y_pred: Predictions
        scaler: Fitted scaler
        output_dir: Directory to save plot
    """
    # Inverse transform
    y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
    y_pred_actual = scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
    
    # Plot
    plt.figure(figsize=(15, 6))
    plt.plot(y_test_actual[:200], label='Actual', alpha=0.7)
    plt.plot(y_pred_actual[:200], label='Predicted', alpha=0.7)
    plt.xlabel('Time Step')
    plt.ylabel('CPU Usage')
    plt.title('CPU Forecasting: Actual vs Predicted')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plot_path = f"{output_dir}/lstm_predictions.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\nPrediction plot saved to {plot_path}")
    plt.close()


def save_models(model: LSTMModel, scaler: MinMaxScaler, output_dir: str = 'orchestrator/models'):
    """
    Save trained models
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save LSTM model (PyTorch)
    model_path = f"{output_dir}/lstm_cpu.pth"
    torch.save({
        'model_state_dict': model.state_dict(),
    }, model_path)
    print(f"\nLSTM model saved to {model_path}")
    
    # Save scaler
    scaler_path = f"{output_dir}/cpu_scaler.pkl"
    joblib.dump(scaler, scaler_path)
    print(f"Scaler saved to {scaler_path}")


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("LSTM CPU Forecasting Model Training")
    print("=" * 60)
    
    # Hyperparameters
    LOOKBACK = 60  # Use past 60 minutes
    FORECAST_HORIZON = 10  # Predict 10 minutes ahead
    EPOCHS = 50
    BATCH_SIZE = 32
    
    # Load data
    df = load_cpu_data()
    
    # Create sequences
    X, y, scaler = create_sequences(df, lookback=LOOKBACK, forecast_horizon=FORECAST_HORIZON)
    
    # Split data (80% train, 10% val, 10% test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, shuffle=False
    )
    
    print(f"\nTrain set: {len(X_train)} sequences")
    print(f"Val set:   {len(X_val)} sequences")
    print(f"Test set:  {len(X_test)} sequences")
    
    # Build model
    model = build_lstm_model(lookback=LOOKBACK)
    
    # Train model
    model = train_lstm(model, X_train, y_train, X_val, y_val, epochs=EPOCHS, batch_size=BATCH_SIZE)
    
    # Evaluate model
    metrics = evaluate_model(model, X_test, y_test, scaler)
    
    # Plot predictions
    device = next(model.parameters()).device
    model.eval()
    with torch.no_grad():
        x_tensor = torch.FloatTensor(X_test).to(device)
        y_pred = model(x_tensor).squeeze(-1).cpu().numpy()
    plot_predictions(y_test, y_pred, scaler)
    
    # Save models
    save_models(model, scaler)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
