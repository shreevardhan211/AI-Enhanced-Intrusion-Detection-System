#!/usr/bin/env python3
"""
AI-Enhanced Intrusion Detection System - ML Training Pipeline
Trains a RandomForest model on network traffic data to detect intrusions
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score
)
import pickle
import warnings
import os

warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

class IDSDataGenerator:
    """Generate realistic network traffic dataset for IDS training"""
    
    def __init__(self, n_samples=5000):
        self.n_samples = n_samples
        self.attack_types = ['Normal', 'DoS', 'Probe', 'R2L', 'U2R']
        
    def generate_dataset(self):
        """Generate synthetic but realistic network traffic data"""
        print("[*] Generating network traffic dataset...")
        
        data = []
        
        # Normal traffic (70%)
        normal_count = int(self.n_samples * 0.70)
        for _ in range(normal_count):
            data.append(self._generate_normal_traffic())
        
        # DoS attacks (15%)
        dos_count = int(self.n_samples * 0.15)
        for _ in range(dos_count):
            data.append(self._generate_dos_traffic())
        
        # Probe attacks (8%)
        probe_count = int(self.n_samples * 0.08)
        for _ in range(probe_count):
            data.append(self._generate_probe_traffic())
        
        # R2L attacks (4%)
        r2l_count = int(self.n_samples * 0.04)
        for _ in range(r2l_count):
            data.append(self._generate_r2l_traffic())
        
        # U2R attacks (3%)
        u2r_count = int(self.n_samples * 0.03)
        for _ in range(u2r_count):
            data.append(self._generate_u2r_traffic())
        
        df = pd.DataFrame(data)
        print(f"[✓] Generated {len(df)} samples")
        print(f"[✓] Attack distribution:\n{df['attack_type'].value_counts()}\n")
        
        return df
    
    def _generate_normal_traffic(self):
        """Normal HTTP/HTTPS traffic"""
        return {
            'src_port': np.random.randint(1024, 65535),
            'dst_port': np.random.choice([80, 443, 22, 25]),
            'protocol': np.random.choice([6, 17]),  # TCP, UDP
            'packet_length': np.random.normal(512, 256),
            'packet_count': np.random.poisson(5),
            'duration': np.random.exponential(10),
            'window_size': np.random.randint(512, 65535),
            'ack_count': np.random.poisson(3),
            'syn_count': np.random.poisson(1),
            'rst_count': np.random.poisson(0.1),
            'psh_count': np.random.poisson(2),
            'urg_count': np.random.poisson(0.01),
            'fin_count': np.random.poisson(0.5),
            'flow_rate': np.random.normal(100, 30),
            'bytes_in': np.random.normal(1024, 512),
            'bytes_out': np.random.normal(512, 256),
            'attack_type': 'Normal'
        }
    
    def _generate_dos_traffic(self):
        """DoS attack traffic - high packet count, rapid SYN"""
        return {
            'src_port': np.random.randint(1024, 65535),
            'dst_port': np.random.choice([80, 443, 22]),
            'protocol': 6,  # TCP
            'packet_length': np.random.normal(100, 50),
            'packet_count': np.random.poisson(150),  # Very high
            'duration': np.random.exponential(5),
            'window_size': np.random.randint(100, 1000),
            'ack_count': np.random.poisson(10),
            'syn_count': np.random.poisson(200),  # Many SYNs
            'rst_count': np.random.poisson(5),
            'psh_count': np.random.poisson(1),
            'urg_count': np.random.poisson(0.1),
            'fin_count': np.random.poisson(0.1),
            'flow_rate': np.random.normal(5000, 1000),  # Very high rate
            'bytes_in': np.random.normal(100, 50),
            'bytes_out': np.random.normal(50, 25),
            'attack_type': 'DoS'
        }
    
    def _generate_probe_traffic(self):
        """Probe/scanning traffic - port scanning pattern"""
        return {
            'src_port': np.random.randint(1024, 65535),
            'dst_port': np.random.randint(1, 65535),  # Random ports
            'protocol': np.random.choice([6, 17]),
            'packet_length': np.random.normal(64, 32),
            'packet_count': np.random.poisson(20),
            'duration': np.random.exponential(15),
            'window_size': np.random.randint(512, 2048),
            'ack_count': np.random.poisson(1),
            'syn_count': np.random.poisson(50),  # Many SYNs for scanning
            'rst_count': np.random.poisson(10),
            'psh_count': np.random.poisson(0.1),
            'urg_count': np.random.poisson(0.01),
            'fin_count': np.random.poisson(0.1),
            'flow_rate': np.random.normal(500, 200),
            'bytes_in': np.random.normal(50, 25),
            'bytes_out': np.random.normal(25, 12),
            'attack_type': 'Probe'
        }
    
    def _generate_r2l_traffic(self):
        """Remote to Local attack"""
        return {
            'src_port': np.random.randint(1024, 65535),
            'dst_port': np.random.choice([23, 21, 22]),  # Telnet, FTP, SSH
            'protocol': 6,
            'packet_length': np.random.normal(256, 128),
            'packet_count': np.random.poisson(30),
            'duration': np.random.exponential(30),
            'window_size': np.random.randint(512, 4096),
            'ack_count': np.random.poisson(25),
            'syn_count': np.random.poisson(2),
            'rst_count': np.random.poisson(0.5),
            'psh_count': np.random.poisson(20),  # Data being pushed
            'urg_count': np.random.poisson(0.1),
            'fin_count': np.random.poisson(1),
            'flow_rate': np.random.normal(300, 150),
            'bytes_in': np.random.normal(2048, 1024),
            'bytes_out': np.random.normal(1024, 512),
            'attack_type': 'R2L'
        }
    
    def _generate_u2r_traffic(self):
        """User to Root privilege escalation attack"""
        return {
            'src_port': np.random.randint(1024, 65535),
            'dst_port': np.random.randint(1024, 65535),
            'protocol': 6,
            'packet_length': np.random.normal(512, 256),
            'packet_count': np.random.poisson(15),
            'duration': np.random.exponential(20),
            'window_size': np.random.randint(1024, 8192),
            'ack_count': np.random.poisson(15),
            'syn_count': np.random.poisson(1),
            'rst_count': np.random.poisson(0.2),
            'psh_count': np.random.poisson(10),
            'urg_count': np.random.poisson(5),  # Urgent data
            'fin_count': np.random.poisson(0.1),
            'flow_rate': np.random.normal(200, 100),
            'bytes_in': np.random.normal(3000, 1500),
            'bytes_out': np.random.normal(1500, 750),
            'attack_type': 'U2R'
        }


class IDSModelTrainer:
    """Train and evaluate IDS model"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = None
        
    def prepare_data(self, df):
        """Prepare data for training"""
        print("[*] Preparing data for training...")
        
        # Separate features and target
        X = df.drop('attack_type', axis=1)
        y = df['attack_type']
        
        self.feature_names = X.columns.tolist()
        
        # Encode target labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        print(f"[✓] Features: {self.feature_names}")
        print(f"[✓] Classes: {self.label_encoder.classes_}\n")
        
        return X_scaled, y_encoded, X
    
    def train(self, X_train, y_train):
        """Train RandomForest model"""
        print("[*] Training RandomForest model...")
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            n_jobs=-1,
            random_state=42,
            verbose=1
        )
        
        self.model.fit(X_train, y_train)
        print("[✓] Training complete\n")
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        print("[*] Evaluating model...")
        
        y_pred = self.model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        print(f"\n{'='*60}")
        print(f"{'MODEL PERFORMANCE METRICS':^60}")
        print(f"{'='*60}")
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1-Score:  {f1:.4f}")
        print(f"{'='*60}\n")
        
        print("Classification Report:")
        print(classification_report(y_test, y_pred, 
                                   target_names=self.label_encoder.classes_))
        
        print("\nConfusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        
        # Feature importance
        print("\nTop 10 Important Features:")
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(importance_df.head(10).to_string(index=False))
        
        return accuracy, precision, recall, f1
    
    def save_model(self, filepath):
        """Save trained model"""
        print(f"\n[*] Saving model to {filepath}...")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_names': self.feature_names
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"[✓] Model saved successfully\n")


def main():
    """Main training pipeline"""
    print("="*60)
    print("AI-ENHANCED INTRUSION DETECTION SYSTEM")
    print("Machine Learning Training Pipeline")
    print("="*60 + "\n")
    
    # Create output directory
    os.makedirs('ml', exist_ok=True)
    
    # Generate dataset
    generator = IDSDataGenerator(n_samples=5000)
    df = generator.generate_dataset()
    
    # Save dataset
    df.to_csv('ml/dataset.csv', index=False)
    print("[✓] Dataset saved to ml/dataset.csv\n")
    
    # Prepare data
    trainer = IDSModelTrainer()
    X_scaled, y_encoded, X_original = trainer.prepare_data(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    print(f"[✓] Training set size: {len(X_train)}")
    print(f"[✓] Test set size: {len(X_test)}\n")
    
    # Train model
    trainer.train(X_train, y_train)
    
    # Evaluate model
    trainer.evaluate(X_test, y_test)
    
    # Save model
    trainer.save_model('ml/model.pkl')
    
    print("="*60)
    print("TRAINING COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
