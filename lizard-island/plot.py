# need matplotlib >= 3.11 to support ax.grouped_bar() function!!
import matplotlib.pyplot as plt
import pandas as pd

path = '/Volumes/XMOUY_SDD3/LizardIsland/MobileArray_data/2023-11-24_morning/localization_results/'
df = pd.read_csv(path + 'localization_results_summary.csv')

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.grouped_bar(
    {'Annotations': df['annotations'],
     'Localizations': df['localizations'],
     'Filtered': df['filtered']},
    tick_labels=df['idx'],
)
for container in bars.bar_containers:
    ax.bar_label(container, padding=2, fontsize=8)

ax.set_title('Localization Results Summary')
ax.set_xlabel('File Index')
ax.set_ylabel('Count')
ax.legend()
fig.tight_layout()
fig.savefig(path + 'localization_results_summary.png', dpi=200)