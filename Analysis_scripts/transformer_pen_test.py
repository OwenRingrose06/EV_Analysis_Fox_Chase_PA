"""
Runs the full EV penetration sweep: for each penetration level, solves
all 96 daily timesteps, records peak loading % for every transformer,
then reports both the WORST transformer and the AVERAGE peak loading
across all 20 transformers - saving one row per penetration level to
a CSV for plotting.
"""
import opendssdirect as dss
import math
import pandas as pd
from pathlib import Path

DSS_DIR = Path(__file__).resolve().parent.parent / "DSS_Fox_chase"

#Transformer Name for plotting later
xfmr_names = [f"tr({p}{i}-{p}{i}lv)" for p in ["b", "h"] for i in range(1, 11)]

penetration_levels = [0.00, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

KVA_RATING = 50.0

def build_master(pen_level):
    """
    Writes a temp Master file for a given pen level
    Uses the Master.dss file as a template.
    """
    with open(DSS_DIR / "Master.dss") as f:
        lines = f.read().split("\n")
    out_lines = []
    for l in lines:
        if "EV_load_shapes.dss" in l or "EV_loads_" in l:
            continue
        out_lines.append(l)
        if l.strip().startswith("Redirect Loads.dss") and pen_level > 0:
            out_lines.append("Redirect EV_load_shapes.dss")
            out_lines.append(f"Redirect EV_loads_{pen_level}.dss")
    with open("../DSS_Fox_chase/Master_sweep.dss", "w") as f:
        f.write("\n".join(out_lines))

results = []

# Build master.dss for each pen level
with pd.ExcelWriter("transformer_loading_all_penetrations.xlsx") as writer:
    for pen in penetration_levels:
        build_master(pen)
        # Solves starting at 15 minutes.
        dss.Command(f'Compile "{DSS_DIR / "Master_sweep.dss"}"')
        dss.Command("Set mode=daily")
        dss.Command("Set stepsize=15m")
        dss.Command("Set number=1")

        # Solve for 24 hours in 15 minute steps
        timeseries_data = {}  # {hour: {xfmr_name: loading_pct}}
        for step in range(1, 97):
            dss.Command("Solve")
            hour = step * 0.25
            timeseries_data[hour] = {}
            for name in xfmr_names:
                dss.Circuit.SetActiveElement(f"Transformer.{name}")
                powers = dss.CktElement.Powers()
                n = dss.CktElement.NumConductors()
                p1 = sum(powers[0:2 * n:2])
                q1 = sum(powers[1:2 * n:2])
                s1 = math.sqrt(p1 ** 2 + q1 ** 2)
                timeseries_data[hour][name] = (s1/KVA_RATING) * 100.0
        df = pd.DataFrame.from_dict(timeseries_data, orient="index")
        df.index.name = "hour"
        df["average_loading_pct"] = df[xfmr_names].mean(axis=1).round(2)
        df["total_load"] = df[xfmr_names].sum(axis=1).round(2)
        df["total_load_kw"] = (df["total_load"]/100) * KVA_RATING
        df["Max_load_percentage"] = df[xfmr_names].max(axis=1).round(2)


        sheet_name = f"{pen:.0%}"
        df.to_excel(writer, sheet_name=sheet_name)

    print(f"Wrote sheet: {sheet_name}")

print("\nSaved: transformer_loading_all_penetrations.xlsx")