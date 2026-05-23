import sys
import pandas as pd


def show_stats(filepath):
    df = pd.read_csv(filepath)

    print(f"\nFile: {filepath}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")

    print("\n--- Column Types ---")
    print(df.dtypes.to_string())

    print("\n--- Missing Values ---")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("No missing values")
    else:
        print(missing.to_string())

    print("\n--- Numeric Summary ---")
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        print("No numeric columns")
    else:
        print(numeric.describe().round(2).to_string())

    print("\n--- Categorical Columns (top 5 values) ---")
    categorical = df.select_dtypes(include=["object", "category"])
    if categorical.empty:
        print("No categorical columns")
    else:
        for col in categorical.columns:
            print(f"\n{col}:")
            print(df[col].value_counts().head(5).to_string())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python csv_stats.py <path_to_csv>")
        sys.exit(1)
    show_stats(sys.argv[1])
