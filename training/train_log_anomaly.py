"""
Training script for log anomaly detection using TF-IDF + Autoencoder (PyTorch)
"""

import os
import numpy as np
import pandas as pd
from typing import Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import joblib
import glob


def load_log_files(data_dir: str = 'training/data/jenkins/logs') -> Tuple[list, list]:
    """
    Load console logs from files
    
    Args:
        data_dir: Directory containing log files
        
    Returns:
        Tuple of (log texts, labels)
    """
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Log directory not found: {data_dir}")
    
    # Find all log files
    log_files = glob.glob(f"{data_dir}/**/*.log", recursive=True)
    
    if not log_files:
        raise ValueError(f"No log files found in {data_dir}")
    
    print(f"Found {len(log_files)} log files")
    
    logs = []
    labels = []
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                log_text = f.read()
                logs.append(log_text)
                
                # Infer label from filename or content
                # Assume logs with 'FAILURE' or 'ERROR' are anomalies
                if 'FAILURE' in log_text or log_text.count('ERROR') > 10:
                    labels.append(1)  # Anomaly
                else:
                    labels.append(0)  # Normal
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
            continue
    
    print(f"Loaded {len(logs)} logs")
    print(f"Anomaly rate: {np.mean(labels):.2%}")
    
    return logs, labels


def create_tfidf_features(logs: list, max_features: int = 500) -> Tuple[TfidfVectorizer, np.ndarray]:
    """
    Create TF-IDF features from logs
    
    Args:
        logs: List of log texts
        max_features: Maximum number of features
        
    Returns:
        Tuple of (fitted vectorizer, feature matrix)
    """
    print("\nCreating TF-IDF features...")
    
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        max_df=0.95,
        min_df=2,
        ngram_range=(1, 2),
        stop_words='english',
        sublinear_tf=True
    )
    
    X = vectorizer.fit_transform(logs)
    
    print(f"TF-IDF matrix shape: {X.shape}")
    print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
    
    return vectorizer, X.toarray()


class Autoencoder(nn.Module):
    """Autoencoder model with tight bottleneck for anomaly detection"""
    
    def __init__(self, input_dim: int, encoding_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.3),
            nn.Linear(64, encoding_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.3),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, input_dim),
            nn.Sigmoid(),
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


def build_autoencoder(input_dim: int, encoding_dim: int = 32) -> Autoencoder:
    """
    Build autoencoder model with tight bottleneck for anomaly detection
    
    Args:
        input_dim: Input dimension
        encoding_dim: Encoding dimension (bottleneck)
        
    Returns:
        Autoencoder model
    """
    print("\nBuilding autoencoder...")
    model = Autoencoder(input_dim, encoding_dim)
    print(f"Autoencoder input dim: {input_dim}")
    print(f"Encoding dim: {encoding_dim}")
    print(f"Total parameters: {sum(p.numel() for p in model.parameters()):,}")
    return model


def train_autoencoder(model: Autoencoder, X_train: np.ndarray,
                     X_val: np.ndarray, epochs: int = 50, batch_size: int = 32):
    """
    Train autoencoder on normal logs only
    """
    print("\nTraining autoencoder...")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    
    train_tensor = torch.FloatTensor(X_train).to(device)
    val_tensor = torch.FloatTensor(X_val).to(device)
    
    train_dataset = TensorDataset(train_tensor, train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    optimizer = optim.Adam(model.parameters(), lr=0.0005)
    criterion = nn.MSELoss()
    
    best_val_loss = float('inf')
    patience = 5
    patience_counter = 0
    best_state = None
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for batch_x, _ in train_loader:
            optimizer.zero_grad()
            output = model(batch_x)
            loss = criterion(output, batch_x)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch_x.size(0)
        train_loss /= len(train_tensor)
        
        model.eval()
        with torch.no_grad():
            val_output = model(val_tensor)
            val_loss = criterion(val_output, val_tensor).item()
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs} - train_loss: {train_loss:.6f} - val_loss: {val_loss:.6f}")
        
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


def calculate_reconstruction_errors(model: Autoencoder, X: np.ndarray) -> np.ndarray:
    """
    Calculate reconstruction errors
    """
    device = next(model.parameters()).device
    model.eval()
    with torch.no_grad():
        x_tensor = torch.FloatTensor(X).to(device)
        predictions = model(x_tensor).cpu().numpy()
    mse = np.mean(np.power(X - predictions, 2), axis=1)
    return mse


def determine_threshold(errors: np.ndarray, percentile: float = 95) -> float:
    """
    Determine anomaly threshold
    
    Args:
        errors: Reconstruction errors on normal data
        percentile: Percentile for threshold
        
    Returns:
        Threshold value
    """
    threshold = np.percentile(errors, percentile)
    print(f"\nAnomaly threshold (at {percentile}th percentile): {threshold:.6f}")
    return threshold


def evaluate_model(model: Autoencoder, X_test: np.ndarray, y_test: np.ndarray, 
                  threshold: float) -> dict:
    """
    Evaluate anomaly detection performance
    
    Args:
        autoencoder: Trained autoencoder
        X_test: Test features
        y_test: Test labels
        threshold: Anomaly threshold
        
    Returns:
        Dictionary with evaluation metrics
    """
    print("\nEvaluating model...")
    
    # Calculate reconstruction errors
    errors = calculate_reconstruction_errors(model, X_test)
    
    # Predict anomalies
    predictions = (errors > threshold).astype(int)
    
    # Calculate metrics
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    
    metrics = {
        'accuracy': accuracy_score(y_test, predictions),
        'precision': precision_score(y_test, predictions, zero_division=0),
        'recall': recall_score(y_test, predictions, zero_division=0),
        'f1_score': f1_score(y_test, predictions, zero_division=0),
        'roc_auc': roc_auc_score(y_test, errors)
    }
    
    print("\nModel Performance:")
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1_score']:.4f}")
    print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
    
    return metrics


def save_models(vectorizer: TfidfVectorizer, autoencoder: Autoencoder, 
               threshold: float, output_dir: str = 'orchestrator/models'):
    """
    Save trained models
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save TF-IDF vectorizer
    tfidf_path = f"{output_dir}/tfidf.pkl"
    joblib.dump(vectorizer, tfidf_path)
    print(f"\nTF-IDF vectorizer saved to {tfidf_path}")
    
    # Save autoencoder (PyTorch)
    autoencoder_path = f"{output_dir}/autoencoder.pth"
    torch.save({
        'model_state_dict': autoencoder.state_dict(),
        'input_dim': autoencoder.encoder[0].in_features,
        'encoding_dim': autoencoder.encoder[-2].out_features,
    }, autoencoder_path)
    print(f"Autoencoder saved to {autoencoder_path}")
    
    # Save threshold
    threshold_path = f"{output_dir}/anomaly_threshold.pkl"
    joblib.dump({'threshold': threshold}, threshold_path)
    print(f"Threshold saved to {threshold_path}")


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("Log Anomaly Detection Model Training")
    print("=" * 60)
    
    # Load logs
    logs, labels = load_log_files()
    labels = np.array(labels)
    
    # Create TF-IDF features
    vectorizer, X = create_tfidf_features(logs, max_features=500)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Use only normal samples for training autoencoder
    X_train_normal = X_train[y_train == 0]
    
    # Further split training data for validation
    X_train_normal, X_val_normal = train_test_split(
        X_train_normal, test_size=0.2, random_state=42
    )
    
    print(f"\nNormal train set: {len(X_train_normal)} samples")
    print(f"Normal val set:   {len(X_val_normal)} samples")
    print(f"Test set:         {len(X_test)} samples")
    
    # Build autoencoder
    autoencoder = build_autoencoder(input_dim=X.shape[1], encoding_dim=32)
    
    # Train autoencoder
    autoencoder = train_autoencoder(autoencoder, X_train_normal, X_val_normal, epochs=100, batch_size=16)
    
    # Determine threshold using validation set
    val_errors = calculate_reconstruction_errors(autoencoder, X_val_normal)
    # Use mean + 2*std for threshold (better than percentile for skewed distributions)
    threshold_mean = np.mean(val_errors)
    threshold_std = np.std(val_errors)
    threshold = threshold_mean + 2 * threshold_std
    print(f"\nAnomaly threshold (mean + 2*std): {threshold:.6f}")
    print(f"  Mean error: {threshold_mean:.6f}, Std: {threshold_std:.6f}")
    
    # Evaluate on test set
    metrics = evaluate_model(autoencoder, X_test, y_test, threshold)
    
    # Save models
    save_models(vectorizer, autoencoder, threshold)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
