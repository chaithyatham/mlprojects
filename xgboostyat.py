import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder, StandardScaler


class HouseDataLoader:
    """Loads and preprocesses house_data.csv (sqft, zip_code → price)."""

    def __init__(self, path="house_data.csv", test_size=0.2, random_state=42):
        df = pd.read_csv(path)
        self.le = LabelEncoder()
        df["zip_code"] = self.le.fit_transform(df["zip_code"].astype(str))

        X = df[["sqft", "zip_code"]].values.astype(np.float32)
        y = df["price"].values.astype(np.float32)

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

    def encode_zip(self, zip_codes):
        return self.le.transform([str(z) for z in zip_codes])


class XGBoostHouseModel:
    def __init__(self, n_estimators=200, learning_rate=0.1, max_depth=4):
        self.model = XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42,
        )

    def train(self, X_train, y_train, X_val, y_val):
        self.model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=50)

    def predict(self, X):
        return self.model.predict(X)

    def evaluate(self, X_test, y_test):
        preds = self.predict(X_test)
        print(f"[XGBoost]  MAE: ${mean_absolute_error(y_test, preds):,.0f}  |  R²: {r2_score(y_test, preds):.4f}")
        return preds


class _PriceNet(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(1)


class DeepLearningHouseModel:
    def __init__(self, epochs=100, lr=1e-3, batch_size=32):
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.scaler = StandardScaler()
        self.model = None
        # scale target to help training
        self._y_mean = 0.0
        self._y_std = 1.0

    def train(self, X_train, y_train, X_val, y_val):
        X_tr = self.scaler.fit_transform(X_train).astype(np.float32)
        X_v = self.scaler.transform(X_val).astype(np.float32)

        self._y_mean = y_train.mean()
        self._y_std = y_train.std() + 1e-8
        y_tr = ((y_train - self._y_mean) / self._y_std).astype(np.float32)
        y_v = ((y_val - self._y_mean) / self._y_std).astype(np.float32)

        train_ds = TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(y_tr))
        loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)

        self.model = _PriceNet(X_tr.shape[1])
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        loss_fn = nn.MSELoss()

        for epoch in range(1, self.epochs + 1):
            self.model.train()
            for xb, yb in loader:
                optimizer.zero_grad()
                loss_fn(self.model(xb), yb).backward()
                optimizer.step()

            if epoch % 20 == 0:
                self.model.eval()
                with torch.no_grad():
                    val_loss = loss_fn(
                        self.model(torch.from_numpy(X_v)), torch.from_numpy(y_v)
                    ).item()
                print(f"  epoch {epoch:3d}  val_loss={val_loss:.4f}")

    def predict(self, X):
        X_s = self.scaler.transform(X).astype(np.float32)
        self.model.eval()
        with torch.no_grad():
            preds = self.model(torch.from_numpy(X_s)).numpy()
        return preds * self._y_std + self._y_mean

    def evaluate(self, X_test, y_test):
        preds = self.predict(X_test)
        print(f"[DeepLearn] MAE: ${mean_absolute_error(y_test, preds):,.0f}  |  R²: {r2_score(y_test, preds):.4f}")
        return preds


if __name__ == "__main__":
    data = HouseDataLoader("house_data.csv")

    print("=== XGBoost ===")
    xgb = XGBoostHouseModel()
    xgb.train(data.X_train, data.y_train, data.X_test, data.y_test)
    xgb.evaluate(data.X_test, data.y_test)

    print("\n=== Deep Learning ===")
    dl = DeepLearningHouseModel(epochs=100, lr=1e-3)
    dl.train(data.X_train, data.y_train, data.X_test, data.y_test)
    dl.evaluate(data.X_test, data.y_test)

    print("\n=== Sample Predictions ===")
    sqfts = [1500, 2200]
    zips = ["94105", "10001"]
    sample = np.array(
        [[s, z] for s, z in zip(sqfts, data.encode_zip(zips))], dtype=np.float32
    )
    for i, (s, z) in enumerate(zip(sqfts, zips)):
        xgb_p = xgb.predict(sample[i : i + 1])[0]
        dl_p = dl.predict(sample[i : i + 1])[0]
        print(f"  sqft={s}, zip={z}  →  XGBoost: ${xgb_p:,.0f}  |  DL: ${dl_p:,.0f}")
