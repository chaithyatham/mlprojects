import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

RANDOM_STATE = 42
TEST_SIZE    = 0.20
OUTPUT_DIR   = "."

# ── 1. Load ───────────────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv("creditcard.csv")
df["Class"] = df["Class"].astype(int)

X = df.drop(columns=["Class"])
y = df["Class"]

print(f"Raw shape       : {X.shape}")
print(f"Fraud cases     : {y.sum():,}  ({y.mean()*100:.4f}%)")

# ── 2. Scale Amount and Time (V1–V28 are already PCA-scaled) ─────────────────
print("\nScaling Amount and Time...")
scaler = StandardScaler()
X = X.copy()
X[["Amount", "Time"]] = scaler.fit_transform(X[["Amount", "Time"]])

# ── 3. Train / test split (before SMOTE — never oversample test set) ──────────
print("Splitting 80/20...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)

print(f"  Train : {X_train.shape[0]:,} rows  | Fraud: {y_train.sum():,}")
print(f"  Test  : {X_test.shape[0]:,} rows   | Fraud: {y_test.sum():,}")

# ── 4. SMOTE on training set only ─────────────────────────────────────────────
print("\nApplying SMOTE to training set...")
smote = SMOTE(random_state=RANDOM_STATE)
X_train_res, y_train_res = smote.fit_resample(X_train, y_train)

print(f"  Before SMOTE : {len(y_train):,} samples | Fraud: {y_train.sum():,} ({y_train.mean()*100:.2f}%)")
print(f"  After  SMOTE : {len(y_train_res):,} samples | Fraud: {y_train_res.sum():,} ({y_train_res.mean()*100:.2f}%)")

# ── 5. Save ───────────────────────────────────────────────────────────────────
print("\nSaving processed arrays...")
np.save(f"{OUTPUT_DIR}/X_train.npy", X_train_res.to_numpy(dtype="float32"))
np.save(f"{OUTPUT_DIR}/y_train.npy", y_train_res.to_numpy(dtype="float32"))
np.save(f"{OUTPUT_DIR}/X_test.npy",  X_test.to_numpy(dtype="float32"))
np.save(f"{OUTPUT_DIR}/y_test.npy",  y_test.to_numpy(dtype="float32"))

# Save feature names for reference
pd.Series(X.columns.tolist()).to_csv(f"{OUTPUT_DIR}/feature_names.csv", index=False, header=False)

print("\nSaved files:")
for fname in ["X_train.npy", "y_train.npy", "X_test.npy", "y_test.npy", "feature_names.csv"]:
    import os
    size_kb = os.path.getsize(f"{OUTPUT_DIR}/{fname}") / 1024
    print(f"  {fname:<22} {size_kb:>8.1f} KB")

print("\nPreprocessing complete.")
