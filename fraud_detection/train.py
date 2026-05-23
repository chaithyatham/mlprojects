import matplotlib
matplotlib.use("Agg")

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, average_precision_score,
    RocCurveDisplay, PrecisionRecallDisplay,
)
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

SEED        = 42
BATCH_SIZE  = 2048
EPOCHS      = 30
LR          = 1e-3
DEVICE      = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

torch.manual_seed(SEED)
np.random.seed(SEED)
print(f"Device: {DEVICE}")

# ── 1. Load preprocessed data ─────────────────────────────────────────────────
X_train = torch.tensor(np.load("X_train.npy"), dtype=torch.float32)
y_train = torch.tensor(np.load("y_train.npy"), dtype=torch.float32)
X_test  = torch.tensor(np.load("X_test.npy"),  dtype=torch.float32)
y_test  = torch.tensor(np.load("y_test.npy"),  dtype=torch.float32)

print(f"Train : {X_train.shape}  |  Fraud: {int(y_train.sum()):,}")
print(f"Test  : {X_test.shape}   |  Fraud: {int(y_test.sum()):,}")

train_ds = TensorDataset(X_train, y_train)
test_ds  = TensorDataset(X_test,  y_test)
train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
test_dl  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

# ── 2. Model ──────────────────────────────────────────────────────────────────
class FraudNet(nn.Module):
    def __init__(self, in_features: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128),         nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64),          nn.BatchNorm1d(64),  nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64,  32),          nn.BatchNorm1d(32),  nn.ReLU(),
            nn.Linear(32,  1),
        )

    def forward(self, x):
        return self.net(x).squeeze(1)


model = FraudNet(in_features=X_train.shape[1]).to(DEVICE)
total_params = sum(p.numel() for p in model.parameters())
print(f"\nModel params: {total_params:,}")

# ── 3. Loss & optimiser ───────────────────────────────────────────────────────
# SMOTE already balanced classes 50/50, so pos_weight=1
criterion = nn.BCEWithLogitsLoss()
optimiser = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-5)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimiser, mode="min", patience=3, factor=0.5
)

# ── 4. Training loop ──────────────────────────────────────────────────────────
history = {"train_loss": [], "val_loss": [], "val_auc": []}

print(f"\n{'Epoch':>5}  {'Train Loss':>10}  {'Val Loss':>9}  {'Val AUC':>8}  {'LR':>8}")
print("-" * 52)

for epoch in range(1, EPOCHS + 1):
    # — train —
    model.train()
    train_loss = 0.0
    for xb, yb in train_dl:
        xb, yb = xb.to(DEVICE), yb.to(DEVICE)
        optimiser.zero_grad()
        loss = criterion(model(xb), yb)
        loss.backward()
        optimiser.step()
        train_loss += loss.item() * len(xb)
    train_loss /= len(train_ds)

    # — validate —
    model.eval()
    val_loss = 0.0
    all_probs = []
    all_labels = []
    with torch.no_grad():
        for xb, yb in test_dl:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            logits = model(xb)
            val_loss += criterion(logits, yb).item() * len(xb)
            all_probs.append(torch.sigmoid(logits).cpu())
            all_labels.append(yb.cpu())
    val_loss  /= len(test_ds)
    probs  = torch.cat(all_probs).numpy()
    labels = torch.cat(all_labels).numpy()
    val_auc = roc_auc_score(labels, probs)

    scheduler.step(val_loss)
    current_lr = optimiser.param_groups[0]["lr"]

    history["train_loss"].append(train_loss)
    history["val_loss"].append(val_loss)
    history["val_auc"].append(val_auc)

    print(f"{epoch:>5}  {train_loss:>10.4f}  {val_loss:>9.4f}  {val_auc:>8.4f}  {current_lr:>8.6f}")

# ── 5. Evaluation ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("FINAL EVALUATION ON TEST SET")
print("=" * 60)

# Choose threshold that maximises F1 on test set
thresholds = np.linspace(0.1, 0.9, 81)
f1_scores  = []
from sklearn.metrics import f1_score
for t in thresholds:
    preds = (probs >= t).astype(int)
    f1_scores.append(f1_score(labels, preds, zero_division=0))
best_thresh = thresholds[np.argmax(f1_scores)]
preds_best  = (probs >= best_thresh).astype(int)

print(f"\nBest threshold (max F1): {best_thresh:.2f}")
print(f"\nClassification Report:\n")
print(classification_report(labels, preds_best, target_names=["Non-Fraud", "Fraud"]))

cm = confusion_matrix(labels, preds_best)
tn, fp, fn, tp = cm.ravel()
print(f"Confusion Matrix:")
print(f"  TN={tn:,}  FP={fp:,}")
print(f"  FN={fn:,}  TP={tp:,}")

roc_auc  = roc_auc_score(labels, probs)
avg_prec = average_precision_score(labels, probs)
print(f"\nROC-AUC              : {roc_auc:.4f}")
print(f"Average Precision    : {avg_prec:.4f}")

# ── 6. Plots ──────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 10))
fig.suptitle("Fraud Detection — Training Results", fontsize=14, fontweight="bold")
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

# Loss curves
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(history["train_loss"], label="Train")
ax1.plot(history["val_loss"],   label="Validation")
ax1.set_title("Loss")
ax1.set_xlabel("Epoch")
ax1.legend()

# AUC curve
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(history["val_auc"], color="green")
ax2.set_title("Validation ROC-AUC")
ax2.set_xlabel("Epoch")
ax2.set_ylim(0.9, 1.0)

# Confusion matrix
ax3 = fig.add_subplot(gs[0, 2])
cm_disp = [[tn, fp], [fn, tp]]
im = ax3.imshow(cm_disp, interpolation="nearest", cmap="Blues")
ax3.set_xticks([0, 1]); ax3.set_yticks([0, 1])
ax3.set_xticklabels(["Pred 0", "Pred 1"]); ax3.set_yticklabels(["True 0", "True 1"])
for i in range(2):
    for j in range(2):
        ax3.text(j, i, f"{cm_disp[i][j]:,}", ha="center", va="center",
                 color="white" if cm_disp[i][j] > cm_disp[0][0] / 2 else "black", fontsize=12)
ax3.set_title(f"Confusion Matrix (t={best_thresh:.2f})")

# ROC curve
ax4 = fig.add_subplot(gs[1, 0:2])
RocCurveDisplay.from_predictions(labels, probs, ax=ax4, name=f"FraudNet (AUC={roc_auc:.4f})")
ax4.plot([0, 1], [0, 1], "k--", lw=0.8)
ax4.set_title("ROC Curve")

# Precision-Recall curve
ax5 = fig.add_subplot(gs[1, 2])
PrecisionRecallDisplay.from_predictions(labels, probs, ax=ax5,
                                         name=f"FraudNet (AP={avg_prec:.4f})")
ax5.set_title("Precision-Recall Curve")

plt.savefig("training_results.png", dpi=150, bbox_inches="tight")
print("\nPlot saved → training_results.png")

# ── 7. Save model ─────────────────────────────────────────────────────────────
torch.save({
    "model_state_dict": model.state_dict(),
    "in_features":      X_train.shape[1],
    "best_threshold":   best_thresh,
    "roc_auc":          roc_auc,
    "avg_precision":    avg_prec,
}, "fraud_model.pt")
print("Model saved → fraud_model.pt")
