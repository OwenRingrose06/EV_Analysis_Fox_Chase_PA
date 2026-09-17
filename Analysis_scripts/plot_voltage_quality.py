import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm

penetration_levels = [0.00, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

colors = cm.viridis([i / (len(penetration_levels) - 1) for i in range(len(penetration_levels))])

# --- Plot 1: average voltage ---
fig1, ax1 = plt.subplots(figsize=(10, 6))
for pen, color in zip(penetration_levels, colors):
    sheet_name = f"{pen:.0%}"
    df = pd.read_excel("house_voltages_all_penetrations.xlsx", sheet_name=sheet_name)
    ax1.plot(df["hour"], df["average_voltage_pu"], label=sheet_name, color=color)

ax1.set_xlabel("Hour of Day")
ax1.set_ylabel("Average House Voltage (pu)")
ax1.set_title("Fox Chase Feeder: Average House Voltage Across the Day, by EV Penetration")
ax1.legend(title="EV Penetration", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig("average_voltage_by_penetration.png", dpi=150)
plt.show()

# --- Plot 2: worst-case (minimum) voltage ---
fig2, ax2 = plt.subplots(figsize=(10, 6))
for pen, color in zip(penetration_levels, colors):
    sheet_name = f"{pen:.0%}"
    df = pd.read_excel("house_voltages_all_penetrations.xlsx", sheet_name=sheet_name)
    ax2.plot(df["hour"], df["min_voltage_pu"], label=sheet_name, color=color)

ax2.set_xlabel("Hour of Day")
ax2.set_ylabel("Minimum House Voltage (pu)")
ax2.set_title("Fox Chase Feeder: Worst-Case House Voltage Across the Day, by EV Penetration")
ax2.legend(title="EV Penetration", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig("worst_voltage_by_penetration.png", dpi=150)
plt.show()