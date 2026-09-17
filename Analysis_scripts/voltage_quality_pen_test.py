"""
Runs the full EV penetration sweep: for each penetration level, solves
all 96 daily timesteps, records the pu voltage at every house's service
drop, then reports the AVERAGE and MINIMUM voltage across all houses -
saving one sheet per penetration level to an Excel workbook.
"""
import opendssdirect as dss
import pandas as pd
from pathlib import Path


DSS_DIR = Path(__file__).resolve().parent.parent / "DSS_Fox_chase"

# House names for plotting later - all 121 houses have baseline load
# regardless of EV eligibility
house_names = [f"house_{i}" for i in range(1, 122)]

penetration_levels = [0.00, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]


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


def get_house_voltage_pu(house_bus):
    """
    Raw voltage at both legs of a house's service drop, converted to pu
    manually (raw volts / 120) - NOT OpenDSS's own pu column, which is
    wrong for these split-phase buses. Returns the lower of the two legs.
    """
    dss.Circuit.SetActiveBus(house_bus)
    raw = dss.Bus.VMagAngle()
    v1 = raw[0]
    v2 = raw[2] if len(raw) > 2 else raw[0]
    return min(v1, v2) / 120.0


# Build master.dss for each pen level
with pd.ExcelWriter("house_voltages_all_penetrations.xlsx") as writer:
    for pen in penetration_levels:
        build_master(pen)
        # Solves starting at 15 minutes.
        dss.Command(f'Compile "{DSS_DIR / "Master_sweep.dss"}"')
        dss.Command("Set mode=daily")
        dss.Command("Set stepsize=15m")
        dss.Command("Set number=1")

        # Solve for 24 hours in 15 minute steps
        timeseries_data = {}  # {hour: {house_name: voltage_pu}}
        for step in range(1, 97):
            dss.Command("Solve")
            hour = step * 0.25
            timeseries_data[hour] = {}
            for name in house_names:
                timeseries_data[hour][name] = round(get_house_voltage_pu(name), 4)

        df = pd.DataFrame.from_dict(timeseries_data, orient="index")
        df.index.name = "hour"
        df["average_voltage_pu"] = df[house_names].mean(axis=1).round(4)
        df["min_voltage_pu"] = df[house_names].min(axis=1).round(4)
        df["max_voltage_pu"] = df[house_names].max(axis=1).round(4)

        sheet_name = f"{pen:.0%}"
        df.to_excel(writer, sheet_name=sheet_name)

        print(f"Wrote sheet: {sheet_name}  (min voltage: {df['min_voltage_pu'].min():.4f} pu)")

print("\nSaved: house_voltages_all_penetrations.xlsx")