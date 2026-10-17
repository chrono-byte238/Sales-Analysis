
from pathlib import Path
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import pandas as pd


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_DIR / "data" / "sales_data.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "figures"


# --------------------------------------------------
# 2. Load and prepare data
# --------------------------------------------------

def load_data(file_path: Path) -> pd.DataFrame:
    """Load the sales dataset and prepare required columns."""

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)

    df["Sale_Date"] = pd.to_datetime(
        df["Sale_Date"],
        errors="coerce",
    )

    df["Sales_Amount"] = pd.to_numeric(
        df["Sales_Amount"],
        errors="coerce",
    )

    required_columns = ["Region", "Sales_Amount"]

    if df[required_columns].isna().any().any():
        raise ValueError(
            "Missing or invalid values found in required columns."
        )

    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns.")

    return df


# --------------------------------------------------
# 3. Create output directory
# --------------------------------------------------

def create_output_directory() -> None:
    """Create the figures directory if it does not exist."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 4. Plot sales by region
# --------------------------------------------------

def plot_sales_by_region(df: pd.DataFrame) -> None:
    """Create and save a horizontal bar chart of recorded sales by region."""
    
    sales_by_region = (
        df.groupby("Region")["Sales_Amount"]
        .sum()
        .sort_values()
    )

    
    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.barh(
        sales_by_region.index,
        sales_by_region.values,
    )

    ax.set_title("Recorded Sales by Region", fontsize=16, pad=15)
    ax.set_xlabel("Recorded Sales Amount")
    ax.set_ylabel("Region")
    ax.xaxis.set_major_formatter(
    FuncFormatter(lambda value, _: f"{value / 1_000_000:.1f} M")
)
    

    # Reserve space on the right for value labels
    max_sales = sales_by_region.max()
    ax.set_xlim(0, max_sales * 1.15)

    ax.bar_label(
        bars,
        labels=[f"{value:,.0f}" for value in sales_by_region.values],
        padding=5,
        fontsize=10,
    )

    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    fig.tight_layout()

    output_file = OUTPUT_DIR / "sales_by_region.png"

    fig.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight",
    )

    plt.show()
    plt.close(fig)

    print(f"Chart saved to: {output_file}")

   
# --------------------------------------------------
# 5. Plot monthly sales trend
# --------------------------------------------------

def plot_monthly_sales_trend(df: pd.DataFrame) -> None:
    """Plot monthly recorded sales and flag the incomplete final month."""
    
    monthly_sales = (
        df.dropna(subset=["Sale_Date"])
        .assign(Sale_Month=lambda data: data["Sale_Date"].dt.to_period("M"))
        .groupby("Sale_Month")
        .agg(
            Total_Sales=("Sales_Amount", "sum"),
            Record_Count=("Sales_Amount", "size"),
        )
        .reset_index()
    )

    if monthly_sales.empty:
        raise ValueError("No valid dates available for monthly analysis.")

    monthly_sales["Month_Label"] = (
        monthly_sales["Sale_Month"].astype(str)
    )

    # Flag the last month if the latest date is before its calendar end.
    latest_date = df["Sale_Date"].max()
    final_month = monthly_sales["Sale_Month"].iloc[-1]

    incomplete_final_month = (
        pd.notna(latest_date)
        and latest_date.to_period("M") == final_month
        and latest_date.day < latest_date.days_in_month
    )

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        monthly_sales["Month_Label"],
        monthly_sales["Total_Sales"],
        marker="o",
        linewidth=2,
        label="Recorded sales",
    )

    # Highlight the potentially incomplete final month.
    if incomplete_final_month:
        final_label = monthly_sales["Month_Label"].iloc[-1]
        final_sales = monthly_sales["Total_Sales"].iloc[-1]

        ax.scatter(
            final_label,
            final_sales,
            marker="X",
            s=100,
            label="Potentially incomplete month",
            zorder=3,
        )

        ax.annotate(
            "Potentially incomplete",
            xy=(final_label, final_sales),
            xytext=(0, 18),
            textcoords="offset points",
            ha="right",
            fontsize=9,
        )
    ax.set_title("Monthly Recorded Sales", fontsize=16, pad=15)
    ax.set_xlabel("Month")
    ax.set_ylabel("Recorded Sales Amount")

    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value / 1_000_000:.1f} M")
    )

    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend()

    # Reserve vertical space for the annotation and horizontal space
    # for rotated month labels.
    max_sales = monthly_sales["Total_Sales"].max()
    ax.set_ylim(
        min(0, monthly_sales["Total_Sales"].min() * 0.95),
        max_sales * 1.20,
    )

    fig.tight_layout()

    output_file = OUTPUT_DIR / "monthly_sales_trend.png"
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close(fig)

    print(f"Chart saved to: {output_file}")
    print(
        "Potentially incomplete final month:",
        monthly_sales["Month_Label"].iloc[-1]
        if incomplete_final_month
        else "None detected",
    )


# --------------------------------------------------
# 6. Plot sales by product category with data quality note
# --------------------------------------------------


def plot_sales_by_category(df: pd.DataFrame) -> None:
    """Plot recorded sales by product category with a data quality note."""
    
    sales_by_category = (
        df.groupby("Product_Category")["Sales_Amount"]
        .sum()
        .sort_values()
    )

    if sales_by_category.empty:
        raise ValueError("No product category data available.")

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.barh(
        sales_by_category.index,
        sales_by_category.values,
    )

    ax.set_title(
        "Recorded Sales by Product Category",
        fontsize=15,
        pad=18,
    )
    ax.set_xlabel("Recorded Sales Amount")
    ax.set_ylabel("Product Category")

    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value / 1_000_000:.1f} M")
    )

    # Reserve space for value labels.
    max_sales = sales_by_category.max()
    ax.set_xlim(0, max_sales * 1.25)

    ax.bar_label(
        bars,
        labels=[
            f"{value:,.0f}"
            for value in sales_by_category.values
        ],
        padding=5,
        fontsize=10,
    )
    
    # Reserve a dedicated footer area for the data quality note.
    fig.subplots_adjust(bottom=0.22)

    fig.text(
        0.5,
        0.035,
        "Data quality note: product categories vary across Product_IDs.",
        ha="center",
        va="bottom",
        fontsize=9,
        wrap=True,
    )


    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    output_file = OUTPUT_DIR / "sales_by_category.png"

    fig.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight",
    )

    plt.show()
    plt.close(fig)

    print(f"Chart saved to: {output_file}")


# --------------------------------------------------
# 7. Plot by sales channel with data quality note
# --------------------------------------------------


def plot_sales_by_channel(df: pd.DataFrame) -> None:
    """Compare recorded sales by channel with amount and share labels."""

    sales_by_channel = (
        df.groupby("Sales_Channel")["Sales_Amount"]
        .sum()
        .sort_values()
    )

    if sales_by_channel.empty:
        raise ValueError("No sales channel data available.")

    total_sales = sales_by_channel.sum()

    if total_sales == 0:
        raise ValueError("Total recorded sales is zero.")

    shares = sales_by_channel / total_sales * 100

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.barh(
        sales_by_channel.index,
        sales_by_channel.values,
    )

    ax.set_title(
        "Recorded Sales by Channel",
        fontsize=16,
        pad=18,
    )
    ax.set_xlabel("Recorded Sales Amount")
    ax.set_ylabel("Sales Channel")

    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value / 1_000_000:.1f} M")
    )

    # Reserve space for all value labels inside the axes.
    max_sales = sales_by_channel.max()
    ax.set_xlim(0, max_sales * 1.30)

    labels = [
        f"{amount:,.0f} ({share:.1f}%)"
        for amount, share in zip(sales_by_channel.values, shares.values)
    ]

    ax.bar_label(
        bars,
        labels=labels,
        padding=6,
        fontsize=10,
    )

    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    fig.tight_layout()

    output_file = OUTPUT_DIR / "sales_by_channel.png"

    fig.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight",
    )

    plt.show()
    plt.close(fig)

    print(f"Chart saved to: {output_file}")


# --------------------------------------------------
# 8. Main execution
# --------------------------------------------------

def main() -> None:
    """Run the visualization workflow."""

    create_output_directory()

    df = load_data(DATA_FILE)

    plot_sales_by_region(df)
    plot_monthly_sales_trend(df)
    plot_sales_by_category(df)
    plot_sales_by_channel(df)
    
if __name__ == "__main__":
    main()

