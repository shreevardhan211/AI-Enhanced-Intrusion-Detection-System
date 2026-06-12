"""
AI IDS - Model Training Script
Dataset: UNSW-NB15
Model: Random Forest Classifier
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, "data", "UNSW_NB15_training-set.csv")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")

# ── Feature columns used ───────────────────────────────────────────────────────
FEATURE_COLS = [
    'dur', 'proto', 'service', 'state', 'spkts', 'dpkts',
    'sbytes', 'dbytes', 'rate', 'sttl', 'dttl', 'sload', 'dload',
    'sloss', 'dloss', 'sinpkt', 'dinpkt', 'sjit', 'djit',
    'swin', 'stcpb', 'dtcpb', 'dwin', 'tcprtt', 'synack',
    'ackdat', 'smean', 'dmean', 'trans_depth', 'response_body_len',
    'ct_srv_src', 'ct_state_ttl', 'ct_dst_ltm', 'ct_src_dport_ltm',
    'ct_dst_sport_ltm', 'ct_dst_src_ltm', 'is_ftp_login', 'ct_ftp_cmd',
    'ct_flw_http_mthd', 'ct_src_ltm', 'ct_srv_dst', 'is_sm_ips_ports'
]

LABEL_COL   = 'label'
ATTACK_COL  = 'attack_cat'

ATTACK_MAP = {
    'Normal': 'Normal',
    'Generic': 'Generic',
    'Exploits': 'Exploits',
    'Fuzzers': 'Fuzzers',
    'DoS': 'DoS',
    'Reconnaissance': 'Reconnaissance',
    'Analysis': 'Analysis',
    'Backdoor': 'Backdoor',
    'Shellcode': 'Shellcode',
    'Worms': 'Worms',
}


def load_and_preprocess(path: str):
    print(f"[*] Loading dataset from: {path}")
    df = pd.read_csv(path)
    print(f"[*] Shape: {df.shape}")

    # Keep only available feature cols
    available = [c for c in FEATURE_COLS if c in df.columns]
    missing   = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        print(f"[!] Missing columns (skipped): {missing}")

    X = df[available].copy()
    y = df[LABEL_COL].values if LABEL_COL in df.columns else None
    cats = df[ATTACK_COL].fillna('Normal') if ATTACK_COL in df.columns else None

    # Encode categorical columns
    label_encoders = {}
    for col in X.select_dtypes(include=['object']).columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le

    X = X.fillna(0)

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, cats, available, label_encoders, scaler


def train():
    X, y, cats, features, encoders, scaler = load_and_preprocess(DATA_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"[*] Train: {X_train.shape}  Test: {X_test.shape}")

    print("[*] Training Random Forest …")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        n_jobs=-1,
        random_state=42,
        class_weight='balanced'
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec  = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1   = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    print(f"\n[✓] Accuracy : {acc*100:.2f}%")
    print(f"[✓] Precision: {prec*100:.2f}%")
    print(f"[✓] Recall   : {rec*100:.2f}%")
    print(f"[✓] F1-Score : {f1*100:.2f}%")

    # Attack-category distribution (for dashboard seeding)
    if cats is not None:
        dist = cats.value_counts().to_dict()
        print(f"\n[*] Attack distribution: {dist}")
    else:
        dist = {}

    model_data = {
        'model':     clf,
        'scaler':    scaler,
        'encoders':  encoders,
        'features':  features,
        'metrics': {
            'accuracy':  round(acc  * 100, 2),
            'precision': round(prec * 100, 2),
            'recall':    round(rec  * 100, 2),
            'f1':        round(f1   * 100, 2),
        },
        'attack_dist': dist,
    }

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"\n[✓] Model saved → {MODEL_PATH}")
    return model_data


if __name__ == '__main__':
    train()