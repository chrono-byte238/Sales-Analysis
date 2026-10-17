
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "sales_data.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "tables"


# --------------------------------------------------
# 2. DATA LOADING
# --------------------------------------------------

def load_data(file_path: Path) -> pd.DataFrame:
    """Load the sales dataset."""
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    print("Dataset loaded successfully.")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    return df


# --------------------------------------------------
# 3. DATA PREPARATION
# --------------------------------------------------

def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare a copy of the dataset for analysis."""
    df = df.copy()

    # Convert the date column
    df["Sale_Date"] = pd.to_datetime(
        df["Sale_Date"],
        errors="coerce"
    )

    # Convert quantitative columns
    numeric_columns = [
        "Sales_Amount",
        "Quantity_Sold",
        "Unit_Cost",
        "Unit_Price",
        "Discount",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Stop if preparation introduced missing values
    # in fields required for the core analysis.
    required_columns = [
        "Sale_Date",
        "Sales_Amount",
        "Quantity_Sold",
    ]

    invalid_rows = df[required_columns].isna().any(axis=1)

    if invalid_rows.any():
        raise ValueError(
            f"{invalid_rows.sum()} rows contain invalid "
            "dates or core numeric values."
        )

    # Derived analysis field, not saved to the raw CSV
    df["Sale_Month"] = (
        df["Sale_Date"].dt.to_period("M").astype(str)
    )

    print("Data preparation completed.")

    return df


# --------------------------------------------------
# 4. OVERALL SALES KPIs
# --------------------------------------------------

def calculate_kpis(df: pd.DataFrame) -> dict:
    """Calculate overall sales performance indicators."""
    kpis = {
        "Total recorded sales": df["Sales_Amount"].sum(),
        "Number of transactions": len(df),
        "Total units sold": df["Quantity_Sold"].sum(),
        "Average transaction value": df["Sales_Amount"].mean(),
        "Number of products": df["Product_ID"].nunique(),
        "Number of sales representatives": df["Sales_Rep"].nunique(),
        "Number of regions": df["Region"].nunique(),
    }

    return kpis


def display_kpis(kpis: dict) -> None:
    """Display the overall KPIs."""
    print("\n" + "=" * 45)
    print("OVERALL SALES PERFORMANCE")
    print("=" * 45)

    for name, value in kpis.items():
        if isinstance(value, (int, float)):
            print(f"{name}: {value:,.2f}")
        else:
            print(f"{name}: {value}")


# --------------------------------------------------
# 5. SALES PERFORMANCE BY DIMENSION
# --------------------------------------------------

def analyze_sales_by(
    df: pd.DataFrame,
    dimension: str
) -> pd.DataFrame:
    """Summarize sales performance by a chosen dimension."""

    if dimension not in df.columns:
        raise ValueError(
            f"Column not found in dataset: {dimension}"
        )

    summary = (
        df.groupby(dimension, dropna=False)
        .agg(
            Total_Sales=("Sales_Amount", "sum"),
            Units_Sold=("Quantity_Sold", "sum"),
            Transaction_Count=("Sales_Amount", "size"),
            Average_Sales=("Sales_Amount", "mean"),
        )
        .sort_values(
            by="Total_Sales",
            ascending=False
        )
    )

    summary["Sales_Share_Percent"] = (
        summary["Total_Sales"]
        / df["Sales_Amount"].sum()
        * 100
    )

    return summary


def display_sales_analysis(
    df: pd.DataFrame,
    dimensions: list[str]
) -> None:
    """Display sales summaries for selected dimensions."""

    for dimension in dimensions:
        summary = analyze_sales_by(df, dimension)

        print("\n" + "=" * 60)
        print(f"SALES PERFORMANCE BY {dimension.upper()}")
        print("=" * 60)

        print(
            summary.round(2).to_string()
        )


# --------------------------------------------------
# 7. MONTHLY SALES ANALYSIS
# --------------------------------------------------

def analyze_monthly_sales(
    df: pd.DataFrame
) -> pd.DataFrame:
    """Analyze monthly sales and flag incomplete periods."""

    monthly = (
        df.groupby("Sale_Month")
        .agg(
            Total_Sales=("Sales_Amount", "sum"),
            Units_Sold=("Quantity_Sold", "sum"),
            Transaction_Count=("Sales_Amount", "size"),
        )
        .sort_index()
    )

    monthly["Average_Sales"] = (
        monthly["Total_Sales"]
        / monthly["Transaction_Count"]
    )

    monthly["Month_Over_Month_Percent"] = (
        monthly["Total_Sales"].pct_change().mul(100)
    )

    # Check whether the final observed month is complete.
    latest_date = df["Sale_Date"].max()
    last_month = latest_date.to_period("M").strftime("%Y-%m")

    if latest_date.day < latest_date.days_in_month:
        monthly.loc[
            last_month, "Month_Over_Month_Percent"
        ] = float("nan")

        monthly["Period_Status"] = "Observed month"
        monthly.loc[last_month, "Period_Status"] = (
            "Potentially incomplete"
        )
    else:
        monthly["Period_Status"] = "Observed month"

    return monthly


def display_monthly_analysis(
    df: pd.DataFrame
) -> None:
    """Display monthly sales trends."""

    monthly = analyze_monthly_sales(df)

    print("\n" + "=" * 70)
    print("MONTHLY SALES ANALYSIS")
    print("=" * 70)

    print(monthly.round(2).to_string())


# --------------------------------------------------
# 9. DISCOUNT INSPECTION
# --------------------------------------------------

def inspect_discount(df: pd.DataFrame) -> None:
    """Inspect discount values without assuming their meaning."""

    discount = df["Discount"]

    print("\n" + "=" * 60)
    print("DISCOUNT DATA INSPECTION")
    print("=" * 60)

    # 1. Column information
    print("\n--- Data type ---")
    print(discount.dtype)

    # 2. Missing values
    print("\n--- Missing values ---")
    print(f"Missing: {discount.isna().sum()}")
    print(f"Non-missing: {discount.notna().sum()}")

    # 3. Most frequent raw values
    print("\n--- Most frequent values ---")
    print(
        discount.value_counts(dropna=False).head(20).to_string()
    )

    # 4. Numeric distribution
    numeric_discount = pd.to_numeric(
        discount.astype("string")
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce"
    )

    print("\n--- Numeric summary ---")
    print(numeric_discount.describe().to_string())

    print("\n--- Unique numeric values ---")
    print(numeric_discount.nunique())

    print("\n--- Selected quantiles ---")
    print(
        numeric_discount.quantile(
            [0, 0.25, 0.50, 0.75, 0.90, 1]
        ).to_string()
    )

    # 5. Inspect relationships with price and sales
    print("\n--- Sample records ---")
    columns = [
        "Discount",
        "Unit_Price",
        "Unit_Cost",
        "Quantity_Sold",
        "Sales_Amount",
    ]

    print(df[columns].head(15).to_string(index=False))

    
# --------------------------------------------------
# 10. SALES AMOUNT CONSISTENCY CHECK
# --------------------------------------------------

def check_sales_amount_consistency(
    df: pd.DataFrame
) -> None:
    """Compare recorded sales against candidate formulas."""

    candidates = {
        "Price x Quantity":
            df["Unit_Price"] * df["Quantity_Sold"],

        "Price x Quantity x (1 - Discount)":
            df["Unit_Price"]
            * df["Quantity_Sold"]
            * (1 - df["Discount"]),

        "Price x (1 - Discount)":
            df["Unit_Price"] * (1 - df["Discount"]),
    }

    actual = df["Sales_Amount"]

    print("\n" + "=" * 70)
    print("SALES AMOUNT CONSISTENCY CHECK")
    print("=" * 70)

    for name, predicted in candidates.items():
        difference = actual - predicted

        mae = difference.abs().mean()

        actual_nonzero = actual.abs() > 0
        mape = (
            difference[actual_nonzero].abs()
            / actual[actual_nonzero].abs()
        ).mean() * 100

        correlation = actual.corr(predicted)

        print(f"\nFormula: {name}")
        print(f"Mean absolute error: {mae:,.2f}")
        print(f"Mean absolute percentage error: {mape:,.2f}%")
        print(f"Correlation: {correlation:.4f}")


# --------------------------------------------------
# 11. FINANCIAL RELATIONSHIP DIAGNOSTICS
# --------------------------------------------------

def inspect_financial_relationships(
    df: pd.DataFrame
) -> None:
    """Inspect relationships among financial variables."""

    columns = [
        "Sales_Amount",
        "Unit_Price",
        "Unit_Cost",
        "Quantity_Sold",
        "Discount",
    ]

    print("\n" + "=" * 70)
    print("FINANCIAL VARIABLE SUMMARY")
    print("=" * 70)

    print(df[columns].describe().round(2).to_string())

    print("\n" + "=" * 70)
    print("PEARSON CORRELATION MATRIX")
    print("=" * 70)

    print(
        df[columns]
        .corr(method="pearson")
        .round(3)
        .to_string()
    )

    # Compare recorded sales with the two most relevant fields
    print("\n" + "=" * 70)
    print("SALES AMOUNT VS PRICE AND COST")
    print("=" * 70)

    print(
        df[["Sales_Amount", "Unit_Price", "Unit_Cost"]]
        .corr(method="spearman")
        .round(3)
        .to_string()
    )

    # Inspect individual rows without changing the source data
    sample = df[
        [
            "Product_ID",
            "Sales_Amount",
            "Unit_Price",
            "Unit_Cost",
            "Quantity_Sold",
            "Discount",
        ]
    ].head(10).copy()

    sample["Price_x_Quantity"] = (
        sample["Unit_Price"] * sample["Quantity_Sold"]
    )

    sample["Expected_After_Discount"] = (
        sample["Price_x_Quantity"] * (1 - sample["Discount"])
    )

    print("\n" + "=" * 70)
    print("ROW-LEVEL COMPARISON")
    print("=" * 70)

    print(sample.round(2).to_string(index=False))

    
def inspect_product_consistency(df: pd.DataFrame) -> None:
    """Check whether product attributes remain consistent across rows."""

    product_columns = [
        "Product_ID",
        "Unit_Price",
        "Unit_Cost",
        "Product_Category",
    ]

    print("\n" + "=" * 70)
    print("PRODUCT CONSISTENCY CHECK")
    print("=" * 70)

    unique_values = (
        df.groupby("Product_ID")[["Unit_Price", "Unit_Cost", "Product_Category"]]
        .nunique()
    )

    inconsistent_products = unique_values[
        (unique_values["Unit_Price"] > 1)
        | (unique_values["Unit_Cost"] > 1)
        | (unique_values["Product_Category"] > 1)
    ]

    print(f"Distinct products: {df['Product_ID'].nunique()}")
    print(f"Products with changing attributes: {len(inconsistent_products)}")

    if not inconsistent_products.empty:
        print("\nProducts with inconsistent attributes:")
        print(inconsistent_products.to_string())

        product_ids = inconsistent_products.index.tolist()[:5]
        print("\nExample rows:")
        print(
            df.loc[
                df["Product_ID"].isin(product_ids),
                product_columns,
            ]
            .sort_values("Product_ID")
            .to_string(index=False)
        )
    else:
        print("No product attribute inconsistencies detected.")


def inspect_dataset_integrity(df: pd.DataFrame) -> None:
    """Inspect identifier patterns and categorical consistency."""

    print("\n" + "=" * 70)
    print("DATASET INTEGRITY CHECK")
    print("=" * 70)

    # Number of distinct values in each categorical column
    categorical_columns = [
        "Sales_Rep",
        "Region",
        "Sales_Channel",
        "Customer_Type",
        "Payment_Method",
        "Product_Category",
    ]

    print("\nDistinct values in categorical columns:")
    for column in categorical_columns:
        print(f"{column}: {df[column].nunique()}")

    # Check whether each sales representative appears in multiple regions
    rep_region_counts = (
        df.groupby("Sales_Rep")["Region"].nunique()
    )

    print("\nRegions associated with each sales representative:")
    print(rep_region_counts.to_string())

    # Check date coverage
    print("\nDate coverage:")
    print(f"Earliest date: {df['Sale_Date'].min()}")
    print(f"Latest date: {df['Sale_Date'].max()}")
    print(f"Distinct dates: {df['Sale_Date'].nunique()}")

    # Check repeated product IDs and row frequency
    product_frequency = df["Product_ID"].value_counts()

    print("\nProduct_ID frequency:")
    print(f"Minimum rows per product: {product_frequency.min()}")
    print(f"Maximum rows per product: {product_frequency.max()}")
    print(f"Average rows per product: {product_frequency.mean():.2f}")

    # Check financial logic
    print("\nFinancial logic:")
    print(
        "Rows where Unit_Cost > Unit_Price:",
        int((df["Unit_Cost"] > df["Unit_Price"]).sum()),
    )
    print(
        "Rows where Discount is outside [0, 1]:",
        int((~df["Discount"].between(0, 1)).sum()),
    )



def build_data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize key data quality checks without modifying the source data."""

    # Basic quality checks
    missing_values = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    changing_prices = int(
        (df.groupby("Product_ID")["Unit_Price"].nunique() > 1).sum()
    )
    changing_costs = int(
        (df.groupby("Product_ID")["Unit_Cost"].nunique() > 1).sum()
    )
    changing_categories = int(
        (df.groupby("Product_ID")["Product_Category"].nunique() > 1).sum()
    )

    cost_exceeds_price = int(
        (df["Unit_Cost"] > df["Unit_Price"]).sum()
    )

    
    # Check whether recorded sales match a candidate formula.
    expected_sales = (
        df["Unit_Price"]
        * df["Quantity_Sold"]
        * (1 - df["Discount"])
    )

    valid_sales = (
        df["Sales_Amount"].notna()
        & expected_sales.notna()
        & (df["Sales_Amount"] != 0)
    )

    absolute_errors = (
        df.loc[valid_sales, "Sales_Amount"]
        - expected_sales.loc[valid_sales]
    ).abs()

    mismatch_mask = absolute_errors > 0.01

    sales_formula_mismatches = int(mismatch_mask.sum())
    checked_sales_rows = int(valid_sales.sum())

    mismatch_rate = (
        sales_formula_mismatches / checked_sales_rows * 100
        if checked_sales_rows > 0
        else 0.0
    )

    mean_absolute_error = (
        float(absolute_errors.mean())
        if checked_sales_rows > 0
        else 0.0
    )

    report = [
        {
            "Check": "Missing values",
            "Result": missing_values,
            "Status": "Review" if missing_values > 0 else "Passed",
        },
        {
            "Check": "Duplicate rows",
            "Result": duplicate_rows,
            "Status": "Review" if duplicate_rows > 0 else "Passed",
        },
        {
            "Check": "Products with changing prices",
            "Result": changing_prices,
            "Status": "Review" if changing_prices > 0 else "Passed",
        },
        {
            "Check": "Products with changing costs",
            "Result": changing_costs,
            "Status": "Review" if changing_costs > 0 else "Passed",
        },
        {
            "Check": "Products with changing categories",
            "Result": changing_categories,
            "Status": "Review" if changing_categories > 0 else "Passed",
        },
        {
            "Check": "Rows where cost exceeds price",
            "Result": cost_exceeds_price,
            "Status": "Review" if cost_exceeds_price > 0 else "Passed",
        },
        {
            "Check": "Sales formula mismatches",
            "Result": sales_formula_mismatches,
            "Status": (
                "Review" if sales_formula_mismatches > 0 else "Passed"
            ),
        },
        {
            "Check": "Rows not matching candidate sales formula",
            "Result": checked_sales_rows,
            "Status": "Informational",
        },
        
        {
            "Check": "Candidate formula deviation rate (%)",
            "Result": round(mismatch_rate, 2),
            "Status": "Review" if mismatch_rate > 0 else "Passed",
        },
        {
            "Check": "Mean absolute sales formula error",
            "Result": round(mean_absolute_error, 2),
            "Status": "Informational",
        },

    ]

    quality_report = pd.DataFrame(report)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "data_quality_report.csv"
    quality_report.to_csv(output_file, index=False)

    print("\n" + "=" * 70)
    print("DATA QUALITY REPORT")
    print("=" * 70)
    display_report = quality_report.copy()
    display_report["Result"] = display_report["Result"].map(
    lambda value: (
        f"{value:.2f}" if isinstance(value, float) else str(value)
    )
)
    print(display_report.to_string(index=False))
    print(f"\nReport saved to: {output_file}")

    return quality_report



# --------------------------------------------------
# 12. MAIN EXECUTION
# --------------------------------------------------

def main():
    df = load_data(DATA_FILE)

    inspect_discount(df)
    
    df = prepare_data(df)
    inspect_financial_relationships(df)
    check_sales_amount_consistency(df)
    inspect_product_consistency(df)
    inspect_dataset_integrity (df)
    build_data_quality_report(df)

    kpis = calculate_kpis(df)
    display_kpis(kpis)

    dimensions = [
        "Region",
        "Product_Category",
        "Sales_Rep",
        "Sales_Channel",
        "Customer_Type",
        "Payment_Method",
    ]

    display_sales_analysis(df, dimensions)
    display_monthly_analysis(df)    


if __name__ == "__main__":
    main()

