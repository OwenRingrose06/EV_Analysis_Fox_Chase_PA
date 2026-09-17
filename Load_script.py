"""
Downloads baseline load data from NREL ResStock, matched to Fox Chase
houses by type and square footage.
Author: Owen Ringrose
"""
import pandas as pd
import numpy as np
import subprocess
from pathlib import Path

base = "s3://oedi-data-lake/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2025/resstock_amy2018_release_1/timeseries_individual_buildings/by_state/upgrade=0/state=PA/"

DOWNLOAD_DIR = Path("resstock_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

RANDOM_SEED = 42
N_NEAREST_CANDIDATES = 3  # pick randomly among the k nearest sqft matches, not just the closest

meta_file = pd.read_parquet(
    "load_data/PA_upgrade0.parquet",
    columns=["bldg_id", "in.sqft..ft2", "in.county_name", "in.geometry_building_type_recs", "in.vacancy_status"]
)

# restrict to Philadelphia County, occupied units only
phila = meta_file[
    (meta_file["in.county_name"] == "Philadelphia County") &
    (meta_file["in.vacancy_status"] != "Vacant")
]

houses = pd.read_excel("./gis_data/fox_chase_houses_TableToExcel_3.xlsx")


def classify(desc):
    d = str(desc).upper()
    if "APT" in d:
        return "Multi-Family with 2 - 4 Units"
    elif d.startswith("S/D") or d.startswith("SEMI/DET"):
        return "Single-Family Attached"
    elif d.startswith("DET"):
        return "Single-Family Detached"
    return "UNKNOWN"


houses["resstock_type"] = houses["building_code_description"].apply(classify)

_rng = np.random.default_rng(RANDOM_SEED)


def find_match(row, candidates_df, k=N_NEAREST_CANDIDATES):
    candidates = candidates_df[candidates_df["in.geometry_building_type_recs"] == row["resstock_type"]].copy()
    candidates["sqft_diff"] = (candidates["in.sqft..ft2"] - row["total_livable_area"]).abs()
    nearest_k = candidates.nsmallest(k, "sqft_diff")
    chosen = nearest_k.sample(n=1, random_state=_rng.integers(0, 2 ** 31 - 1))
    return chosen["bldg_id"].values[0]


houses["matched_bldg_id"] = houses.apply(find_match, candidates_df=phila, axis=1)

unique_ids = houses["matched_bldg_id"].unique()
print(f"Unique real buildings needed: {len(unique_ids)}")


def download_if_missing(bid):
    dest = DOWNLOAD_DIR / f"{bid}-0.parquet"
    if dest.exists():
        print(f"  {dest.name} already downloaded, skipping")
        return
    subprocess.run(["aws", "s3", "cp", "--no-sign-request", f"{base}{bid}-0.parquet", str(dest)])


for bid in unique_ids:
    download_if_missing(bid)


def clean_baseline(bldg_id):
    """Removes EV charging from baseline load; also computes a dryer-excluded
    column used only for peak-day selection, since individual buildings can
    have an unrealistically large single-appliance spike that would otherwise
    distort which day gets picked as the feeder's coincident peak."""
    df = pd.read_parquet(DOWNLOAD_DIR / f"{bldg_id}-0.parquet")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["baseline_kw"] = (df["out.electricity.total.energy_consumption..kwh"]
                          - df["out.electricity.ev_charging.energy_consumption..kwh"]) / 0.25
    df["baseline_kw_no_dryer"] = (df["baseline_kw"]
                                   - df["out.electricity.clothes_dryer.energy_consumption..kwh"] / 0.25)
    return df


building_profiles = {bid: clean_baseline(bid) for bid in unique_ids}


def compute_true_coincident_peak(houses_df, building_profiles):
    """Finds the real timestamp where the whole house population's combined
    (dryer-excluded) load is highest - this becomes the anchor day used for
    every house's shape and magnitude below."""
    combined = None
    for _, h in houses_df.iterrows():
        bid = h["matched_bldg_id"]
        col = building_profiles[bid][["timestamp", "baseline_kw_no_dryer"]].rename(
            columns={"baseline_kw_no_dryer": f"house_{h['ref_id']}"})
        col = col.set_index("timestamp")
        combined = col if combined is None else combined.add(col, fill_value=0)

    combined["total_kw"] = combined.sum(axis=1)
    peak_time = combined["total_kw"].idxmax()
    peak_date = peak_time.date()
    print(f"Coincident peak (dryer excluded): {peak_time}, {combined['total_kw'].max():.1f} kW")
    return combined, peak_date


combined_load, coincident_date = compute_true_coincident_peak(houses, building_profiles)
coincident_timestamp = combined_load["total_kw"].idxmax()


def get_within_day_peak_profile(df, coincident_timestamp):
    """Anchors magnitude and shape to each building's own peak within the
    real coincident day, kept at 96-point 15-min resolution so short spikes
    aren't diluted by hourly averaging."""
    day_date = pd.to_datetime(coincident_timestamp).date()
    day = df[df["timestamp"].dt.date == day_date].copy()
    if day.empty:
        print(f"  WARNING: missing data for {day_date}, skipping")
        return None, None

    peak_kw = day["baseline_kw"].max()
    day = day.sort_values("timestamp")
    ratios = (day["baseline_kw"] / peak_kw).tolist()

    if len(ratios) != 96:
        print(f"  WARNING: expected 96 points, got {len(ratios)} for {day_date}")

    if peak_kw > 12.0:
        print(f"  NOTE: within-day peak is {peak_kw:.1f} kW - worth a manual check")

    return peak_kw, ratios


shape_rows = []
for bid, df in building_profiles.items():
    peak_kw, ratios = get_within_day_peak_profile(df, coincident_timestamp)
    if peak_kw is None:
        continue
    row = {"bldg_id": bid, "peak_kw": peak_kw, "coincident_day": str(coincident_date)}
    row.update({f"pt_{i}_ratio": v for i, v in enumerate(ratios)})
    shape_rows.append(row)

shapes_df = pd.DataFrame(shape_rows)
shapes_df.to_csv("building_shapes.csv", index=False)
print(f"\nSaved building_shapes.csv ({len(shapes_df)} unique buildings)")
print(shapes_df[["bldg_id", "peak_kw"]])

peak_lookup = dict(zip(shapes_df["bldg_id"], shapes_df["peak_kw"]))
houses["peak_kw"] = houses["matched_bldg_id"].map(peak_lookup)

house_out_cols = ["ref_id", "resstock_type", "matched_bldg_id", "peak_kw"]
houses[house_out_cols].to_csv("house_load_profiles.csv", index=False)
print(f"\nSaved house_load_profiles.csv ({len(houses)} houses)")