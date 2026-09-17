"""
Generate OpenDSS model files (Master.dss, LineCodes.dss, Lines.dss,
Transformers.dss, Loads.dss) for the Fox Chase model from ARCGIS data

Inputs (in same folder):
  fox_chase_houses.xlsx   - one row per house
  transformers.xlsx       - one row per transformer
  service_drops.xlsx      - one row per house-to-transformer secondary line
  laterals.xlsx           - one row per lateral
  primary_feeder.xlsx     - one row

Outputs (written to ./output/):
  Master.dss, LineCodes.dss, Lines.dss, Transformers.dss, Loads.dss
"""
import random

import pandas as pd
import math
import os

from numpy.ma.core import arccos

IN_DIR_GIS = "./gis_data"
OUT_DIR = "DSS_Fox_chase"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------
# Load GIS data
# ---------------------------------------------------------------------
houses = pd.read_excel(f"{IN_DIR_GIS}/fox_chase_houses_TableToExcel_3.xlsx")
house_load_data = pd.read_csv(f"./load_data/house_load_profiles.csv")
house_shape_data = pd.read_csv(f"{IN_DIR_GIS}/building_shapes.csv")
transformers = pd.read_excel(f"{IN_DIR_GIS}/transformers_TableToExcel.xlsx")
service_drops = pd.read_excel(f"{IN_DIR_GIS}/service_drops_TableToExcel_1.xlsx")
laterals = pd.read_excel(f"{IN_DIR_GIS}/laterals_TableToExcel.xlsx")
primary = pd.read_excel(f"{IN_DIR_GIS}/primary_feeder_TableToExcel.xlsx")
feeder_cords = pd.read_excel(f"{IN_DIR_GIS}/feeder_xy.xlsx")


# ---------------------------------------------------------------------
# Assumptions
# ---------------------------------------------------------------------
SUBSTATION_KV = 12.47 # 3-phase line-to-line, standard US primary
LATERAL_KV = SUBSTATION_KV/(math.sqrt(3)) # 12.47 / sqrt(3), single-phase line-to-neutral
SECONDARY_KV = 0.24 # 240V split-phase
RESIDENTIAL_POWER_FACTOR = 0.90 # Assumed 90% PF
FT_TO_KM = 0.0003048

Feeder_line_code = "3P_OH_AL_ACSR_4/0_Penguin_3"
Lateral_line_code = "1P_OH_AL_4/0_Zuzara_2"
service_drop_line_code = "1P_UG_AL_1/0_Brenau_2"


# Assumptions for a 50kV transformer
normhkva_50kv_t = 55.0
emerg_hkva_50kv_t = 75.0
r_primary_50kv_t = 0.266272
r_secondary_50kv_t = 0.532544
loadloss_50kv_t = 0.798816
noloadloss_50kv_t = 0.37


# ---------------------------------------------------------------------
# Lines.dss
# ---------------------------------------------------------------------

def format_line(name, bus1, bus2, length_ft, phases, line_code):
    length_km = length_ft * FT_TO_KM
    return f"New Line.l({name}) Units=km Bus1={bus1} Bus2={bus2} Length={length_km} Phases={phases} Linecode={line_code} "

lines = ["// feeder lines"]

# Define Feeder Lines

lines.append(format_line("source_to_benson", "source_bus.1.2.3", "benson_tap.1.2.3",
                        float(primary.iloc[0]["length_ft"]),3 ,Feeder_line_code))

lines.append(format_line("benson_to_hoffnagle", "benson_tap.1.2.3", "hoffnagle_tap.1.2.3",
                        float(primary.iloc[2]["length_ft"]),3 ,Feeder_line_code))


# Define Lateral lines
lines.append("\n// lateral lines")
for row in laterals.itertuples():
    phase_num = "1" if row.phase == "A" else "2"
    lines.append(format_line(f"lateral_{row.bus_a}_{row.bus_b}", f"{row.bus_a}.{phase_num}.0", f"{row.bus_b}.{phase_num}.0",row.length_ft,1, Lateral_line_code))

lines.append("// secondary lines")
# define service drops
for row in service_drops.itertuples():
    lines.append(format_line(f"service_drop_house{row.house_id}", f"{row.transformer_id}lv.1.2", f"house_{row.house_id}.1.2",row.length_ft,2, service_drop_line_code))

# write out to file
with open(f"{OUT_DIR}/Lines.dss", "w") as f:
    f.write("\n".join(lines))

# ---------------------------------------------------------------------
# transformers.dss
# ---------------------------------------------------------------------
def transformer_line(xid, phase, kva, normhkva, emerg_hkva, r_primary, r_secondary, loadloss, noloadloss) :
    return (
        f"New Transformer.tr({xid}-{xid}lv) phases=1 windings=3 "
        f"%loadloss={loadloss} %Noloadloss={noloadloss} normhkva={normhkva} "
        f"wdg=1 conn=wye bus={xid}.{phase} Kv=7.2 kva={kva} EmergHKVA={emerg_hkva} %r={r_primary} "
        f"wdg=2 conn=wye bus={xid}lv.1.0 Kv=0.12 kva={kva} EmergHKVA={emerg_hkva} %r={r_secondary} "
        f"wdg=3 conn=wye bus={xid}lv.0.2 Kv=0.12 kva={kva} EmergHKVA={emerg_hkva} %r={r_secondary} "
        f"XHL=2.4 XLT=2.4 XHT=1.6"
    )
transformers_dss = []
for row in transformers.itertuples():
    phase = "2" if row.street == "Benson" else "1"
    transformers_dss.append(transformer_line(row.transformer_id, phase, row.KVA,
        normhkva_50kv_t, emerg_hkva_50kv_t, r_primary_50kv_t, r_secondary_50kv_t, loadloss_50kv_t, noloadloss_50kv_t))

with open(f"{OUT_DIR}/Transformers.dss", "w") as f:
    f.write("\n".join(transformers_dss))
# ---------------------------------------------------------------------
# Loads.dss
# ---------------------------------------------------------------------
def load_line(house_id, load_kw, shape, pf = 0.9) :
    load_kw = load_kw / 2
    kvar = load_kw * math.tan(math.acos(pf))
    return (
        f"New Load.house_{house_id}_1 conn=wye bus1=house_{house_id}.1 kV=0.12 Vminpu=0.8 Vmaxpu=1.2"
        f" model=1 kW={load_kw} kvar={kvar} Phases=1 daily={shape}\n"
        f"\nNew Load.house_{house_id}_2 conn=wye bus1=house_{house_id}.2 kV=0.12 Vminpu=0.8 Vmaxpu=1.2"
        f" model=1 kW={load_kw} kvar={kvar} Phases=1 daily={shape}\n"
    )
loads_dss = []
for row in house_load_data.itertuples():
    loads_dss.append(load_line(row.ref_id, row.peak_kw,f"{row.matched_bldg_id}_daily"))
with open(f"{OUT_DIR}/Loads.dss", "w") as f:
    f.write("\n".join(loads_dss))

# ---------------------------------------------------------------------
# load_shape.dss
# ---------------------------------------------------------------------
def load_shape(res_stock_building_id, ratios):
    mult_str = " ".join(f"{r:.5f}" for r in ratios)
    return(
        f"New Loadshape.{res_stock_building_id}_daily npts=96 interval=0.25 "
        f"mult=({mult_str})\n"
    )
load_shapes = []
for row in house_shape_data.itertuples():
    ratios = [getattr(row, f"pt_{i}_ratio") for i in range(96)]
    load_shapes.append(load_shape(row.bldg_id, ratios))
with open(f"{OUT_DIR}/LoadShapes.dss", "w") as f:
    f.write("\n".join(load_shapes))
# ---------------------------------------------------------------------
# Buscoords.dss
# ---------------------------------------------------------------------
def bus_cord_line(name, x, y):
    return f"{name} {x} {y}\n"

cord_dss = []

for row in houses.itertuples():
    cord_dss.append(bus_cord_line(f"house_{row.ref_id}", row.POINT_X, row.POINT_Y))

for row in transformers.itertuples():
    cord_dss.append(bus_cord_line(f"{row.transformer_id}", row.POINT_X, row.POINT_Y))
    cord_dss.append(bus_cord_line(f"{row.transformer_id}lv", row.POINT_X, row.POINT_Y))

for row in feeder_cords.itertuples():
    cord_dss.append(bus_cord_line(f"{row.bus}", row.POINT_X, row.POINT_Y))

with open(f"{OUT_DIR}/BusCoords.dss", "w") as f:
    f.write("\n".join(cord_dss))

# ---------------------------------------------------------------------
# EV_load_shapes.dss
# ---------------------------------------------------------------------

ev_df = pd.read_csv("load_data/EV_shapes_daily_96pt.csv")

ev_shape_lines = []
ev_valid_nums = []

for col in ev_df.columns:
    if col.startswith("Class_2"):
        ratios = ev_df[col] / ev_df[col].max()
        if ev_df[col].max() > 0:
            ev_shape_lines.append(load_shape(col, ratios.tolist()))
            ev_valid_nums.append((col, ev_df[col].max()))

with open(f"{OUT_DIR}/EV_load_shapes.dss", "w") as f:
    f.write("\n".join(ev_shape_lines))

# ---------------------------------------------------------------------
# EV_loads files
# ---------------------------------------------------------------------
eligible_house_ids = house_load_data[house_load_data["resstock_type"] != "Multi-Family with 2 - 4 Units"]["ref_id"].tolist()
penetration_levels = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

def create_ev_load_line(house_id, kw, kvar, shape_name):
    return (
        f"New Load.ev_{house_id} bus1=house_{house_id}.1.2 kV=0.24 "
        f"kW={kw:.3f} kvar={kvar:.3f} Phases=2 daily={shape_name}"
    )

# ---------------------------------------------------------------------
# EV_loads files
# ---------------------------------------------------------------------
eligible_house_ids = house_load_data[house_load_data["resstock_type"] != "Multi-Family with 2 - 4 Units"]["ref_id"].tolist()
penetration_levels = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

def create_ev_load_line(house_id, kw, kvar, shape_name):
    return (
        f"New Load.ev_{house_id} bus1=house_{house_id}.1.2 kV=0.24 "
        f"kW={kw:.3f} kvar={kvar:.3f} Phases=2 daily={shape_name}"
    )

def build_adoption_order(eligible_house_ids, house_load_data, seed=42):
    """
    Groups eligible houses by their transformer, shuffles each group once,
    then round-robins across transformers to build one fixed adoption
    order. Taking a prefix of this list at any penetration % gives you
    adoption that is both NESTED (lower-penetration adopters remain
    adopters at every higher penetration) and STRATIFIED (spread evenly
    across transformers, rather than left to random clustering).
    """
    rng = random.Random(seed)
    houses_by_xfmr = {}
    for hid in eligible_house_ids:
        xfmr = house_load_data.loc[house_load_data["ref_id"] == hid, "transformer_id"].iloc[0]
        houses_by_xfmr.setdefault(xfmr, []).append(hid)

    for xfmr in houses_by_xfmr:
        rng.shuffle(houses_by_xfmr[xfmr])

    ordered = []
    max_len = max(len(h) for h in houses_by_xfmr.values())
    for i in range(max_len):
        for xfmr, houses in houses_by_xfmr.items():
            if i < len(houses):
                ordered.append(houses[i])
    return ordered

adoption_order = build_adoption_order(eligible_house_ids, houses)

# Assign each house's charger (kW + shape)]
house_charger_assignment = {
    house_id: random.choice(ev_valid_nums) for house_id in adoption_order

}

def create_ev_load_file(pen_level):
    n_adopters = int(pen_level * len(adoption_order))
    houses_nums = sorted(adoption_order[:n_adopters])
    ev_load_lines = []
    for house_num in houses_nums:
        kw = house_charger_assignment[house_num]
        ev_load_lines.append(create_ev_load_line(house_num, kw[1], 0, f"{kw[0]}_daily"))
    with open(f"{OUT_DIR}/EV_loads_{pen_level}.dss", "w") as f:
        f.write("\n".join(ev_load_lines))


for pen_level in penetration_levels:
    create_ev_load_file(pen_level)