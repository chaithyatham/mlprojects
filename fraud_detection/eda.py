import matplotlib
matplotlib.use("Agg")  # non-interactive backend — saves to file without needing a display
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv("creditcard.csv")
df["Class"] = df["Class"].astype(int)

# ── 1. Shape & types ──────────────────────────────────────────────────────────
print("=" * 60)
print("SHAPE & DTYPES")
print("=" * 60)
print(f"Rows: {df.shape[0]:,}   Columns: {df.shape[1]}")
print(f"\nDtypes:\n{df.dtypes.value_counts().to_string()}")
print(f"\nMissing values: {df.isnull().sum().sum()}")

# ── 2. Class balance ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("CLASS BALANCE")
print("=" * 60)
counts = df["Class"].value_counts().sort_index()
pcts   = df["Class"].value_counts(normalize=True).sort_index() * 100
balance = pd.DataFrame({"Count": counts, "Percent (%)": pcts.round(4)})
balance.index = balance.index.map({0: "Non-Fraud (0)", 1: "Fraud (1)"})
print(balance.to_string())
print(f"\nImbalance ratio  →  1 fraud per {counts[0] / counts[1]:.0f} legit transactions")

# ── 3. Basic statistics ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("BASIC STATISTICS  (Amount & Time)")
print("=" * 60)
print(df[["Time", "Amount"]].describe().round(2).to_string())

print("\nAmount by class:")
print(df.groupby("Class")["Amount"].describe().round(2).to_string())

# ── 4. Visualisations ─────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted")
fig = plt.figure(figsize=(18, 14))
fig.suptitle("Credit Card Fraud — Exploratory Data Analysis", fontsize=16, fontweight="bold", y=1.01)
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# 4a. Class balance bar
ax1 = fig.add_subplot(gs[0, 0])
colors = ["#4C72B0", "#DD8452"]
bars = ax1.bar(["Non-Fraud", "Fraud"], counts.values, color=colors, width=0.5)
ax1.set_title("Class Distribution")
ax1.set_ylabel("Count")
for bar, pct in zip(bars, pcts.values):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 0.5,
             f"{pct:.3f}%", ha="center", va="center", color="white", fontweight="bold")

# 4b. Class balance pie
ax2 = fig.add_subplot(gs[0, 1])
ax2.pie(counts.values, labels=["Non-Fraud", "Fraud"], autopct="%1.3f%%",
        colors=colors, startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 1.5})
ax2.set_title("Class Proportion")

# 4c. Transaction amount by class (log scale)
ax3 = fig.add_subplot(gs[0, 2])
for cls, label, color in [(0, "Non-Fraud", colors[0]), (1, "Fraud", colors[1])]:
    ax3.hist(df[df["Class"] == cls]["Amount"], bins=80, alpha=0.65,
             label=label, color=color, log=True)
ax3.set_title("Transaction Amount Distribution")
ax3.set_xlabel("Amount ($)")
ax3.set_ylabel("Count (log scale)")
ax3.legend()

# 4d. Time of transaction by class
ax4 = fig.add_subplot(gs[1, 0:2])
for cls, label, color in [(0, "Non-Fraud", colors[0]), (1, "Fraud", colors[1])]:
    ax4.hist(df[df["Class"] == cls]["Time"] / 3600, bins=48, alpha=0.6,
             label=label, color=color, density=True)
ax4.set_title("Transaction Time Distribution (density)")
ax4.set_xlabel("Hours since first transaction")
ax4.set_ylabel("Density")
ax4.legend()

# 4e. Amount boxplot by class
ax5 = fig.add_subplot(gs[1, 2])
df_plot = df[df["Amount"] < df["Amount"].quantile(0.99)]  # clip top 1% for readability
sns.boxplot(data=df_plot, x="Class", y="Amount", hue="Class",
            palette=colors, ax=ax5, order=[0, 1], width=0.5, legend=False)
ax5.set_xticks([0, 1])
ax5.set_xticklabels(["Non-Fraud", "Fraud"])
ax5.set_title("Amount by Class (99th pct clip)")

# 4f. Correlation of PCA features with Class (top 10 by absolute value)
ax6 = fig.add_subplot(gs[2, :])
v_cols = [c for c in df.columns if c.startswith("V")]
corr = df[v_cols + ["Amount", "Time"]].corrwith(df["Class"]).sort_values()
colors_corr = ["#DD8452" if v > 0 else "#4C72B0" for v in corr.values]
ax6.bar(corr.index, corr.values, color=colors_corr)
ax6.axhline(0, color="black", linewidth=0.8)
ax6.set_title("Feature Correlation with Class Label (V1–V28, Amount, Time)")
ax6.set_ylabel("Pearson Correlation")
ax6.tick_params(axis="x", rotation=45)

plt.savefig("eda_report.png", dpi=150, bbox_inches="tight")
print("\nPlot saved → eda_report.png")
