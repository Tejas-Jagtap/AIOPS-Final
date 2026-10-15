"""
Training script for XGBoost-based CI/CD failure prediction model
"""

import os
import pandas as pd
import numpy as np
from typing import Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from xgboost import XGBClassifier
import joblib


def load_jenkins_data(data_dir: str = 'training/data/jenkins') -> pd.DataFrame:
    """
    Load Jenkins build data
    
    Args:
        data_dir: Directory containing Jenkins data
        
    Returns:
        DataFrame with build data
    """
    csv_file = f"{data_dir}/all_builds.csv"
    
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Data file not found: {csv_file}")
    
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} builds from {csv_file}")
    
    return df


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features and target variable
    
    Args:
        df: Raw DataFrame
        
    Returns:
        Tuple of (features DataFrame, target Series)
    """
    # Create binary target: 1 for FAILURE, 0 for SUCCESS
    df['failed'] = (df['result'] == 'FAILURE').astype(int)
    
    # Select feature columns
    feature_columns = [
        'duration',
        'warnings',
        'errors',
        'failures',
        'log_length'
    ]
    
    # Add test features if available
    if 'tests_failed' in df.columns:
        feature_columns.extend(['tests_failed', 'tests_passed', 'tests_total'])
        # Fill missing test values with 0
        df[['tests_failed', 'tests_passed', 'tests_total']] = df[['tests_failed', 'tests_passed', 'tests_total']].fillna(0)
    
    # Handle missing values
    df[feature_columns] = df[feature_columns].fillna(0)
    
    # Remove any rows with infinite values
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=feature_columns + ['failed'])
    
    X = df[feature_columns]
    y = df['failed']
    
    print(f"\nFeatures: {feature_columns}")
    print(f"Samples: {len(X)}")
    print(f"Failure rate: {y.mean():.2%}")
    
    return X, y


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> XGBClassifier:
    """
    Train XGBoost classifier
    
    Args:
        X_train: Training features
        y_train: Training labels
        
    Returns:
        Trained XGBoost model
    """
    print("\nTraining XGBoost model...")
    
    # Calculate scale_pos_weight for imbalanced data
    n_negative = (y_train == 0).sum()
    n_positive = (y_train == 1).sum()
    scale_pos_weight = n_negative / n_positive if n_positive > 0 else 1
    
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    print("Training complete!")
    
    return model


def evaluate_model(model: XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Evaluate model performance
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        
    Returns:
        Dictionary with evaluation metrics
    """
    print("\nEvaluating model...")
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba)
    }
    
    print("\nModel Performance:")
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1_score']:.4f}")
    print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
    
    # Feature importance
    print("\nTop 5 Feature Importances:")
    feature_importance = pd.DataFrame({
        'feature': X_test.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.head(5).iterrows():
        print(f"  {row['feature']}: {row['importance']:.4f}")
    
    return metrics


def save_model(model: XGBClassifier, output_dir: str = 'orchestrator/models'):
    """
    Save trained model
    
    Args:
        model: Trained model
        output_dir: Directory to save model
    """
    os.makedirs(output_dir, exist_ok=True)
    model_path = f"{output_dir}/xgboost_failure.bin"
    
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("XGBoost Failure Prediction Model Training")
    print("=" * 60)
    
    # Load data
    df = load_jenkins_data()
    
    # Prepare features
    X, y = prepare_features(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTrain set: {len(X_train)} samples")
    print(f"Test set:  {len(X_test)} samples")
    
    # Train model
    model = train_model(X_train, y_train)
    
    # Evaluate model
    metrics = evaluate_model(model, X_test, y_test)
    
    # Save model
    save_model(model)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
