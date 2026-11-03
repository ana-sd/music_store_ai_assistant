import pandas as pd
import unicodedata
import json

from pathlib import Path


DATA_DIR = Path("data")
INPUT_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "processed"

SCHEMAS = {
    "categories": {
        "primary_key": "category_id",
        "required": ["name"],
        "string": ["name", "description"],
    },
    "customers": {
        "primary_key": "customer_id",
        "required": ["name"],
        "string": ["name", "city"],
    },
    "orders": {
        "primary_key": "order_id",
        "required": ["customer_id", "order_date", "status"],
        "string": ["status", "payment_method", "tracking_code", "notes"],
    },
    "order_items": {
        "required": ["product_id", "quantity"],
    },
    "products": {
        "primary_key": "product_id",
        "required": ["name", "category_id", "price_brl"],
        "string": ["name", "description", "specs", "status"],
    },
    "promotions": {
        "primary_key": "promotion_id",
        "required": ["product_id", "discount_percent"],
        "string": ["description"],
    },
}

# Required fields
REQUIRED_COLS = {
    "categories": ["name"],
    "customers": ["name"],
    "orders": ["customer_id", "order_date", "status"],
    "order_items": ["product_id", "quantity"],
    "products": ["name", "category_id", "price_brl"],
    "promotions": ["product_id", "discount_percent"]
}

# Primary keys
PRIMARY_KEYS = {
    "categories": ["category_id"],
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "products": ["product_id"],
    "promotions": ["promotion_id"]
}

FOREIGN_KEYS = [
    ("products", "category_id", "categories", "category_id"),
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("promotions", "product_id", "products", "product_id")
]

# Text columns to normalize
STRING_COLS = {
    "categories": ["name", "description"],
    "customers": ["name", "city"],
    "orders": ["status", "payment_method", "tracking_code", "notes"],
    "products": ["name", "description", "specs", "status"],
    "promotions": ["description"]
}

# Date columns
DATE_COLS = {
    "orders": ["order_date", "estimated_delivery"],
    "products": ["created_at"]
}

# Controlled categorical columns
CATEGORICAL_COLS = {
    "orders": ["status", "payment_method"],
    "products": ["status"]
}

def normalize(df, name):
    for col in STRING_COLS.get(name, []):
        if col in df.columns:
            df[col] = df[col].astype("string").str.normalize('NFKD').str.strip()

    for col in CATEGORICAL_COLS.get(name, []):
        if col in df.columns:
            df[col] = df[col].str.casefold()

    for col in DATE_COLS.get(name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce"
            )
    df = df.drop_duplicates()

    return df
    
def validate_primary_keys(df, name):
    # Validate primary key uniqueness
    for key in PRIMARY_KEYS.get(name, []):
        if df[key].duplicated().any():
            raise ValueError(
                f"Duplicate primary keys in {name}.{key}"
            )
        if df[key].isna().any() or df[key].eq("").any():
            raise ValueError(
                f"Missing primary keys in {name}.{key}"
            )

def validate_required_fields(df, name):
    for col in REQUIRED_COLS.get(name, []):
        if df[col].isna().any() or df[col].dtype == "object":
            raise ValueError(
                f"Missing values in required field {name}.{col}"
            )

def validate_foreign_keys(processed):
    for table, col, ref_table, ref_col in FOREIGN_KEYS:
        valid_ids = processed[ref_table][ref_col]
        invalid = ~processed[table][col].isin(valid_ids)
        if invalid.any():
            raise ValueError(
                f"Invalid foreign keys in {table}.{col}: "
                f"{processed[table].loc[invalid, col].unique()}"
            )

def validate_values(df, name):
    if name == "products":
        if (df["price_brl"] < 0).any():
            raise ValueError("Negative product prices.")

        if (df["stock_quantity"] < 0).any():
            raise ValueError("Negative stock quantities.")

    elif name == "order_items":
        if (df["quantity"] <= 0).any():
            raise ValueError("Invalid order quantities.")

    elif name == "promotions":
        if not df["discount_percent"].between(0, 100).all():
            raise ValueError("Invalid discount percentages.")

    elif name == "orders":
        if (df["total_brl"] < 0).any():
            raise ValueError("Negative order totals.")

def preprocess(files):
    preprocessed = {}

    for file_path in files:
        name = file_path.stem.rsplit(" - ", 1)[-1]

        if name not in REQUIRED_COLS:
            continue

        df = pd.read_csv(file_path, encoding="utf-8")
        df = normalize(df, name)

        validate_primary_keys(df, name)
        validate_required_fields(df, name)
        validate_values(df, name)

        preprocessed[name] = df

    validate_foreign_keys(preprocessed)

    return preprocessed

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = list(INPUT_DIR.glob("*.csv"))

    print(f"Found {len(files)} files to process")

    # Load and preprocess
    preprocessed = preprocess(files)

    # Save processed files
    for name, df in preprocessed.items():
        df.to_csv(
            OUTPUT_DIR / f"{name}.csv",
            index=False,
            encoding="utf-8"
        )
        print(f"Processed {name}: {len(df)} rows")

    print("Preprocessing completed successfully.")

if __name__ == "__main__":
    main()