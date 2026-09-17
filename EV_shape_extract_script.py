import pandas as pd

INPUT_FILE = "load_data/EV charging load with different charging rate_5 years data.xlsx"
OUTPUT_FILE = "load_data/EV_shapes_daily_96pt.csv"
DAY = 200

df = pd.read_excel(INPUT_FILE, sheet_name="Year_5")

time_col = df.columns[0]
day_mask = df[time_col].str.startswith(f"Day {DAY} -")
day_rows = df[day_mask]

print(f"Rows matched for Day {DAY}: {len(day_rows)}")

medium_cols = [c for c in df.columns if c.startswith("Class_2_L2_Medium_EV")]
print(f"Medium EV columns found: {len(medium_cols)}")

result = day_rows.loc[day_rows.index.repeat(4)].reset_index(drop=True)
result = result[medium_cols]
result.insert(0, "point", [f"pt_{i}" for i in range(96)])
result.to_csv(OUTPUT_FILE, index=False)

print(result.head())