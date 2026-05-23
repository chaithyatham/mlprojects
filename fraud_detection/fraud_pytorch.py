"""
Fraud Detection with PyTorch — annotated for sklearn practitioners
==================================================================
Each section maps a PyTorch concept to its closest sklearn equivalent.
"""

import matplotlib
matplotlib.use("Agg")

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, classification_report,
)

# ──────────────────────────────────────────────────────────────────────────────
# HYPERPARAMETERS
# ──────────────────────────────────────────────────────────────────────────────
BATCH_SIZE = 2048
EPOCHS     = 80
LR         = 1e-3
THRESHOLD  = 0.45    # sigmoid output cutoff for predicted class
DEVICE     = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

torch.manual_seed(42)


# ──────────────────────────────────────────────────────────────────────────────
# 1. DATASET CLASS
# sklearn equivalent: just X_train / y_train numpy arrays fed directly into .fit()
#
# PyTorch needs a Dataset object that knows:
#   - how many samples exist  → __len__
#   - how to fetch one sample → __getitem__
# The DataLoader (step 2) calls these internally during iteration.
# ──────────────────────────────────────────────────────────────────────────────

class FraudDataset(Dataset):
    def __init__(self, X: np.ndarray, y: np.ndarray):
        # Convert numpy arrays → float32 tensors (PyTorch's default float type)
        # sklearn accepts float64 arrays natively; PyTorch prefers float32
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        # sklearn equivalent: X_train.shape[0]
        return len(self.X)

    def __getitem__(self, idx):
        # Returns one (features, label) pair by index.
        # The DataLoader calls this repeatedly and stacks results into batches.
        return self.X[idx], self.y[idx]


# ──────────────────────────────────────────────────────────────────────────────
# 2. DATALOADER
# sklearn equivalent: no direct equivalent — sklearn's .fit() ingests all data
# at once. The closest analogy is SGDClassifier with batch_size, which iterates
# over mini-batches internally. DataLoader makes that iteration explicit.
#
# shuffle=True on train → randomises sample order each epoch (avoids order bias)
# shuffle=False on test → keeps order stable for evaluation
# ──────────────────────────────────────────────────────────────────────────────

def build_loaders(X_train, y_train, X_test, y_test):
    train_loader = DataLoader(
        FraudDataset(X_train, y_train),
        batch_size=BATCH_SIZE,
        shuffle=True,
    )
    test_loader = DataLoader(
        FraudDataset(X_test, y_test),
        batch_size=BATCH_SIZE,
        shuffle=False,
    )
    return train_loader, test_loader


# ──────────────────────────────────────────────────────────────────────────────
# 3. NEURAL NETWORK (nn.Module)
# sklearn equivalent: a custom estimator inheriting BaseEstimator.
# nn.Module is PyTorch's base class for all models — you define the architecture
# in __init__ and the forward pass (prediction logic) in forward().
#
# sklearn: model.predict(X)  →  PyTorch: model(X)  (calls forward() implicitly)
# ──────────────────────────────────────────────────────────────────────────────

class FraudNet(nn.Module):
    def __init__(self, n_features: int):
        super().__init__()

        # nn.Sequential chains layers just like a sklearn Pipeline chains steps.
        # sklearn: Pipeline([("scaler", ...), ("clf", ...)])
        # PyTorch: nn.Sequential(layer1, layer2, ...)
        self.network = nn.Sequential(

            # Block 1 — 30 inputs → 256 hidden units
            nn.Linear(n_features, 256),  # like coef_ weights in LogisticRegression
            nn.BatchNorm1d(256),         # normalises activations per batch; no sklearn equivalent
            nn.ReLU(),                   # activation — introduces non-linearity
            nn.Dropout(0.3),             # randomly zeros 30% of neurons; regularises like C in LR

            # Block 2
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),

            # Block 3
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),

            # Block 4
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),

            # Output — single logit (raw score before sigmoid)
            # BCEWithLogitsLoss (step 4) applies sigmoid internally for numerical stability.
            # sklearn LogisticRegression outputs a probability; here we output a raw logit.
            nn.Linear(32, 1),
        )

    def forward(self, x):
        # squeeze(1): removes the trailing dimension → shape (batch,) instead of (batch, 1)
        return self.network(x).squeeze(1)


# ──────────────────────────────────────────────────────────────────────────────
# 4. TRAINING LOOP
# sklearn equivalent: model.fit(X_train, y_train) — a single call that handles
# everything internally. In PyTorch you write the loop yourself, which gives you
# full control over the gradient update at every step.
#
# Each epoch = one full pass over the training data (like n_iter=1 in SGDClassifier).
# ──────────────────────────────────────────────────────────────────────────────

def train(model, loader, criterion, optimiser):
    """One epoch of training. Returns average loss."""

    # model.train() enables Dropout and BatchNorm's training behaviour.
    # sklearn has no equivalent — its estimators don't have separate train/eval modes.
    model.train()

    total_loss = 0.0
    for X_batch, y_batch in loader:
        X_batch = X_batch.to(DEVICE)
        y_batch = y_batch.to(DEVICE)

        # --- Forward pass ---
        # sklearn: y_pred = model.predict_proba(X_batch)
        logits = model(X_batch)

        # --- Loss ---
        # sklearn: internally computed by the solver (e.g. lbfgs, sgd)
        # BCEWithLogitsLoss = sigmoid + binary cross-entropy in one numerically stable op
        loss = criterion(logits, y_batch)

        # --- Backward pass (compute gradients) ---
        # sklearn: handled invisibly inside .fit()
        optimiser.zero_grad()   # clear gradients from previous batch
        loss.backward()         # compute dLoss/d(every weight) via backprop
        optimiser.step()        # update weights: w = w - lr * gradient

        total_loss += loss.item() * len(X_batch)

    return total_loss / len(loader.dataset)


@torch.no_grad()  # disables gradient tracking — saves memory and compute during eval
def evaluate(model, loader):
    """Returns loss, probabilities, and true labels for the full loader."""

    # model.eval() disables Dropout and switches BatchNorm to running stats.
    # sklearn: no equivalent — predict() always behaves the same way.
    model.eval()

    criterion = nn.BCEWithLogitsLoss()
    total_loss = 0.0
    all_probs, all_labels = [], []

    for X_batch, y_batch in loader:
        X_batch = X_batch.to(DEVICE)
        y_batch = y_batch.to(DEVICE)

        logits = model(X_batch)
        total_loss += criterion(logits, y_batch).item() * len(X_batch)

        # torch.sigmoid converts logits → probabilities in [0, 1]
        # sklearn: model.predict_proba(X)[:, 1]
        all_probs.append(torch.sigmoid(logits).cpu().numpy())
        all_labels.append(y_batch.cpu().numpy())

    probs  = np.concatenate(all_probs)
    labels = np.concatenate(all_labels)
    return total_loss / len(loader.dataset), probs, labels


# ──────────────────────────────────────────────────────────────────────────────
# 5. EVALUATION METRICS
# sklearn equivalent: classification_report, roc_auc_score — identical API,
# same functions used here since PyTorch has no built-in metrics module.
# ──────────────────────────────────────────────────────────────────────────────

def print_metrics(labels, probs, threshold=THRESHOLD):
    preds = (probs >= threshold).astype(int)

    precision = precision_score(labels, preds, zero_division=0)
    recall    = recall_score(labels, preds,    zero_division=0)
    f1        = f1_score(labels, preds,        zero_division=0)
    auc       = roc_auc_score(labels, probs)

    print(f"  Precision : {precision:.4f}  (of all flagged transactions, how many were truly fraud)")
    print(f"  Recall    : {recall:.4f}  (of all actual frauds, how many did we catch)")
    print(f"  F1 Score  : {f1:.4f}  (harmonic mean of precision and recall)")
    print(f"  ROC-AUC   : {auc:.4f}  (ranking quality across all thresholds)")
    print()
    print(classification_report(labels, preds, target_names=["Non-Fraud", "Fraud"]))


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Device : {DEVICE}\n")

    # --- Load preprocessed arrays (produced by preprocess.py) ---
    X_train = np.load("X_train.npy")
    y_train = np.load("y_train.npy")
    X_test  = np.load("X_test.npy")
    y_test  = np.load("y_test.npy")

    print(f"Train  : {X_train.shape}  fraud={int(y_train.sum()):,}")
    print(f"Test   : {X_test.shape}   fraud={int(y_test.sum()):,}\n")

    # --- Build loaders, model, loss, optimiser ---
    train_loader, test_loader = build_loaders(X_train, y_train, X_test, y_test)

    model = FraudNet(n_features=X_train.shape[1]).to(DEVICE)

    # BCEWithLogitsLoss: binary cross-entropy for 0/1 labels
    # sklearn equivalent: log_loss (but sklearn minimises it internally)
    criterion = nn.BCEWithLogitsLoss()

    # Adam optimiser: adaptive learning rate per parameter
    # sklearn equivalent: solver="adam" in MLPClassifier
    # weight_decay adds L2 regularisation — like penalty="l2", C=1/weight_decay in sklearn
    optimiser = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-5)

    # Halve LR if val loss doesn't improve for 3 epochs
    # sklearn: no built-in scheduler; closest is learning_rate="adaptive" in SGDClassifier
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimiser, mode="min", patience=3, factor=0.5
    )

    # --- Training loop ---
    print(f"{'Epoch':>5}  {'Train Loss':>10}  {'Val Loss':>9}  {'Val AUC':>8}  {'LR':>9}")
    print("─" * 52)

    for epoch in range(1, EPOCHS + 1):
        train_loss = train(model, train_loader, criterion, optimiser)
        val_loss, probs, labels = evaluate(model, test_loader)
        val_auc = roc_auc_score(labels, probs)
        scheduler.step(val_loss)
        lr = optimiser.param_groups[0]["lr"]
        print(f"{epoch:>5}  {train_loss:>10.4f}  {val_loss:>9.4f}  {val_auc:>8.4f}  {lr:>9.6f}")

    # --- Final evaluation ---
    print("\n" + "=" * 60)
    print("FINAL METRICS ON HELD-OUT TEST SET")
    print("=" * 60 + "\n")
    _, probs, labels = evaluate(model, test_loader)
    print_metrics(labels, probs, threshold=THRESHOLD)

    # --- Save model weights ---
    # sklearn: joblib.dump(model, "model.pkl")
    # PyTorch: save only the state_dict (weights), not the whole object
    torch.save(model.state_dict(), "fraud_net_weights.pt")
    print("Weights saved → fraud_net_weights.pt")
    print("\nTo reload:")
    print("  model = FraudNet(n_features=30).to(device)")
    print("  model.load_state_dict(torch.load('fraud_net_weights.pt'))")
    print("  model.eval()")
