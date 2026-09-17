import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm

penetration_levels = [0.00, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

fig, ax = plt.subplots(figsize=(10, 6))

colors = cm.viridis([i / (len(penetration_levels) - 1) for i in range(len(penetration_levels))])

for pen, color in zip(penetration_levels, colors):
    sheet_name = f"{pen:.0%}"
    df = pd.read_excel("transformer_loading_all_penetrations.xlsx", sheet_name=sheet_name)
    ax.plot(df["hour"], df["average_loading_pct"], label=sheet_name, color=color)

ax.set_xlabel("Hour of Day")
ax.set_ylabel("Average Transformer Loading (%)")
ax.set_title("Fox Chase Feeder: Average Transformer Loading Across the Day, by EV Penetration")
ax.axhline(100, color="red", linestyle="--", linewidth=1, label="Rated capacity")
ax.legend(title="EV Penetration", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig("average_loading_by_penetration.png", dpi=150)
plt.show()

fig, ax = plt.subplots(figsize=(10, 6))

colors = cm.viridis([i / (len(penetration_levels) - 1) for i in range(len(penetration_levels))])

for pen, color in zip(penetration_levels, colors):
    sheet_name = f"{pen:.0%}"
    df = pd.read_excel("transformer_loading_all_penetrations.xlsx", sheet_name=sheet_name)
    ax.plot(df["hour"], df["total_load"], label=sheet_name, color=color)

ax.set_xlabel("Hour of Day")
ax.set_ylabel("Total Feeder Load (kW)")
ax.set_title("Fox Chase Feeder: Total Load Across the Day, by EV Penetration")
ax.legend(title="EV Penetration", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig("total_load_by_penetration.png", dpi=150)
plt.show()

fig, ax = plt.subplots(figsize=(10, 6))

colors = cm.viridis([i / (len(penetration_levels) - 1) for i in range(len(penetration_levels))])

for pen, color in zip(penetration_levels, colors):
    sheet_name = f"{pen:.0%}"
    df = pd.read_excel("transformer_loading_all_penetrations.xlsx", sheet_name=sheet_name)
    ax.plot(df["hour"], df["Max_load_percentage"], label=sheet_name, color=color)

ax.set_xlabel("Hour of Day")
ax.set_ylabel("Peak Transformer Load(%)")
ax.set_title("Peak Transformer Load over Time by EV penetration")
ax.legend(title="EV Penetration", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig("Wost_load_by_penetration.png", dpi=150)
plt.show()

fig, ax = plt.subplots(figsize=(10, 6))
for pen, color in zip(penetration_levels, colors):
    sheet_name = f"{pen:.0%}"
    df = pd.read_excel("transformer_loading_all_penetrations.xlsx", sheet_name=sheet_name)
    ax.plot(df["hour"], df["tr(b2-b2lv)"], label=sheet_name)

ax.set_xlabel("Hour of Day")
ax.set_ylabel("Loading of transformer B2 (%)")
ax.set_title("Transformer B2 Loading over Time")
ax.legend(title="EV Penetration", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig("transformer_B2_loading.png", dpi=150)
plt.show()