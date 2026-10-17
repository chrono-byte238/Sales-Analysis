
import pandas as pd
from pathlib import Path


# ==================================================
# 1. LOAD DATA
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_DIR / "data" / "sales_data.csv"

df = pd.read_csv(DATA_PATH)

print("=== FIRST 5 ROWS ===")
print(df.head())

print("\n=== DATASET SHAPE ===")
print(df.shape)

print("\n=== COLUMN NAMES ===")
print(df.columns.tolist())

print("\n=== DATA TYPES ===")
print(df.dtypes)

print("\n=== DATASET INFO ===")
df.info()


# ==================================================
# 2. GENERAL DATA QUALITY
# ==================================================

print("\n=== MISSING VALUES ===")
print(df.isnull().sum())

print("\n=== DUPLICATE ROWS ===")
print("Exact duplicates:", df.duplicated().sum())

print("\n=== STATISTICAL SUMMARY ===")
print(df.describe())

print("\n=== UNIQUE VALUES ===")
for column in [
    "Product_ID",
    "Sales_Rep",
    "Region",
    "Product_Category",
    "Customer_Type",
    "Payment_Method",
    "Sales_Channel",
]:
    print(f"{column}: {df[column].nunique()} unique values")


# ==================================================
# 3. NUMERICAL BOUNDARIES
# ==================================================

print("\n=== NUMERICAL BOUNDARIES ===")

for column in [
    "Sales_Amount",
    "Quantity_Sold",
    "Unit_Cost",
    "Unit_Price",
    "Discount",
]:
    print(f"\n{column}")
    print("Minimum:", df[column].min())
    print("Maximum:", df[column].max())
    print("Zero values:", (df[column] == 0).sum())
    print("Negative values:", (df[column] < 0).sum())

print("\n=== DISCOUNT VALUES ===")
print(sorted(df["Discount"].dropna().unique()))


# ==================================================
# 4. DATE VALIDATION
# ==================================================

# Use a separate Series so the original dataframe
# remains unchanged during exploration.
dates = pd.to_datetime(df["Sale_Date"], errors="coerce")

print("\n=== DATE VALIDATION ===")
print("Invalid dates:", dates.isna().sum())
print("Earliest date:", dates.min())
print("Latest date:", dates.max())

print("\n=== EARLIEST 5 DATES ===")
print(dates.sort_values().head().to_list())

print("\n=== LATEST 10 DATES ===")
print(dates.sort_values().tail(10).to_list())

print(
    "Records dated 2024-01-01:",
    (dates.dt.strftime("%Y-%m-%d") == "2024-01-01").sum()
)


# ==================================================
# 5. REDUNDANT COLUMN CHECK
# ==================================================

expected = df["Region"] + "-" + df["Sales_Rep"]
matches = df["Region_and_Sales_Rep"].eq(expected)

print("\n=== COMBINED COLUMN CHECK ===")
print("Matching rows:", matches.sum(), "out of", len(df))
print("Mismatching rows:", (~matches).sum())


# ==================================================
# 6. ECONOMIC CONSISTENCY INVESTIGATION
# ==================================================

gross_amount = df["Quantity_Sold"] * df["Unit_Price"]

net_amount = gross_amount * (1 - df["Discount"])

total_cost = df["Quantity_Sold"] * df["Unit_Cost"]

print("\n=== UNIT COST VS UNIT PRICE ===")
print(
    "Rows where Unit_Cost > Unit_Price:",
    (df["Unit_Cost"] > df["Unit_Price"]).sum()
)

print("\n=== SALES AMOUNT FORMULA CHECK ===")
print("Observed Sales_Amount mean:",
      round(df["Sales_Amount"].mean(), 2))

print("Calculated gross amount mean:",
      round(gross_amount.mean(), 2))

print("Calculated net amount mean:",
      round(net_amount.mean(), 2))

print(
    "Rows matching gross amount:",
    df["Sales_Amount"].round(2).eq(gross_amount.round(2)).sum()
)

print(
    "Rows matching net amount:",
    df["Sales_Amount"].round(2).eq(net_amount.round(2)).sum()
)

print(
    "Rows where recorded sales amount exceeds calculated cost:",
    (df["Sales_Amount"] > total_cost).sum()
)

print("\n=== CORRELATIONS WITH SALES_AMOUNT ===")
print(
    df[
        [
            "Sales_Amount",
            "Quantity_Sold",
            "Unit_Cost",
            "Unit_Price",
            "Discount",
        ]
    ]
    .corr(numeric_only=True)["Sales_Amount"]
    .sort_values(ascending=False)
    .round(3)
)


# ==================================================
# 7. EXPLORATION SUMMARY
# ==================================================

print("\n=== EXPLORATION SUMMARY ===")
print("Records:", len(df))
print("Columns:", len(df.columns))
print("Missing cells:", df.isnull().sum().sum())
print("Exact duplicate rows:", df.duplicated().sum())
print("Invalid dates:", dates.isna().sum())

print(
    "\nDATA LIMITATION:"
    "\nSales_Amount does not match the tested gross or net"
    "\namount formulas. Its business meaning must be confirmed"
    "\nbefore drawing conclusions about revenue or profit."
)

print("\nExploration completed.")
