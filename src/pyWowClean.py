import pandas as pd
from pathlib import Path

INPUT_PATH = Path.home() / "Desktop" / "HW2" / "raiderio_runs_saron_final.csv"
OUTPUT_PATH = Path.home() / "Desktop" / "HW2" / "raiderio_runs_saron_clean.csv"

ILVL_COLS = ["tank_ilvl", "healer_ilvl", "dps_1_ilvl", "dps_2_ilvl", "dps_3_ilvl"]
MISSING_DROP_THRESHOLD = 3
TIME_BUCKET_MS = 60_000  # group by 60-second clear-time buckets for imputation


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset="keystone_run_id", keep="first")
    print(f"[Dedup] Removed {before - len(df)} duplicate runs. {len(df)} remaining.")
    return df


def drop_sparse_rows(df: pd.DataFrame) -> pd.DataFrame:
    for col in ILVL_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    missing_per_row = df[ILVL_COLS].isna().sum(axis=1)
    before = len(df)
    df = df[missing_per_row < MISSING_DROP_THRESHOLD].copy()
    print(f"[Drop]  Removed {before - len(df)} rows with >= {MISSING_DROP_THRESHOLD} missing ilvls. {len(df)} remaining.")
    return df


def add_grouping_cols(df: pd.DataFrame) -> pd.DataFrame:
    df["completed_at"] = pd.to_datetime(df["completed_at"], utc=True)
    df["_year"] = df["completed_at"].dt.year
    df["_week"] = df["completed_at"].dt.isocalendar().week.astype(int)
    df["_time_bucket"] = (df["clear_time_ms"] / TIME_BUCKET_MS).round().astype("Int64")
    return df


def impute_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    n_missing = df[col].isna().sum()
    if n_missing == 0:
        return df
    print(f"  [{col}] {n_missing} missing — imputing...")

    def fill(df: pd.DataFrame, keys: list) -> pd.DataFrame:
        missing_mask = df[col].isna()
        if not missing_mask.any():
            return df
        means = (
            df.loc[~df[col].isna()]
            .groupby(keys)[col]
            .mean()
            .reset_index()
            .rename(columns={col: "_imp"})
        )
        df = df.merge(means, on=keys, how="left")
        filled = missing_mask & df["_imp"].notna()
        df.loc[filled, col] = df.loc[filled, "_imp"]
        return df.drop(columns=["_imp"])

    # Level 1: same year + week + mythic_level + 60s time bucket
    df = fill(df, ["_year", "_week", "mythic_level", "_time_bucket"])
    # Level 2: same year + week + mythic_level (relax time bucket)
    df = fill(df, ["_year", "_week", "mythic_level"])
    # Level 3: mythic_level only (last resort)
    df = fill(df, ["mythic_level"])

    still = df[col].isna().sum()
    if still:
        print(f"  [{col}] WARNING: {still} values still missing after all fallbacks.")
    return df


def impute_ilvls(df: pd.DataFrame) -> pd.DataFrame:
    print("[Impute] Missing ilvls per column before imputation:")
    for col in ILVL_COLS:
        print(f"  {col}: {df[col].isna().sum()}")
    for col in ILVL_COLS:
        df = impute_col(df, col)
    return df


def main():
    df = pd.read_csv(INPUT_PATH)
    print(f"[Load]  {len(df)} rows, {len(df.columns)} columns")

    if "clear_time_ms" not in df.columns:
        raise ValueError("clear_time_ms column not found — re-scrape with the updated pyWowStats.py first.")

    df = deduplicate(df)
    df = drop_sparse_rows(df)
    df = add_grouping_cols(df)
    df = impute_ilvls(df)

    df = df.drop(columns=["_year", "_week", "_time_bucket"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n[Done]  Saved {len(df)} clean rows → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
