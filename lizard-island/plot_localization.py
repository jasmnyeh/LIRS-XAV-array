import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append('../localization')
import localization

folder = "/Volumes/XMOUY_SDD3/LizardIsland/MobileArray_data/2023-11-24_morning/localization_results/"

def main():

    hydrophones_config_file = r'./config/hydrophones_config_LIRS-ROV.csv'
    hydrophones= pd.read_csv(hydrophones_config_file, skipinitialspace=True, dtype={'name': str, 'file_name_root': str})

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    numeric_columns = [
        "x",
        "y",
        "z",
        "x_err_low",
        "x_err_high",
        "y_err_low",
        "y_err_high",
        "z_err_low",
        "z_err_high",
    ]

    if hydrophones is not None:
        ax.scatter3D(
            hydrophones["x"],
            hydrophones["y"],
            hydrophones["z"],
            s=20,
            color="gainsboro",
            edgecolors="dimgray",
            label=hydrophones["name"],
            alpha=1,
            zorder=3,
        )

    localizations = pd.DataFrame()
    for file in os.listdir(folder):
        if file.endswith("_filtered_all.csv"):
            localizations = pd.concat([localizations, pd.read_csv(os.path.join(folder, file))], ignore_index=True)

    for column in numeric_columns:
        if column in localizations.columns:
            localizations[column] = pd.to_numeric(localizations[column], errors="coerce")
    loc_data = localizations.dropna(subset=["x", "y", "z"])
    ax.scatter3D(
        loc_data["x"],
        loc_data["y"],
        loc_data["z"],
        c="blue",
        # marker=params['loc_marker'].values[0],
        alpha=1,
        # s=2
    )
    # plot uncertainties
    for idx, loc_point in loc_data.iterrows():
        lw = 1
        c = "red"
        alph = 1
        ax.plot3D(
            [loc_point["x_err_low"], loc_point["x_err_high"]],
            [loc_point["y"], loc_point["y"]],
            [loc_point["z"], loc_point["z"]],
            linewidth=lw,
            # linestyle='-',
            color=c,
            alpha=alph,
        )
        ax.plot3D(
            [loc_point["x"], loc_point["x"]],
            [loc_point["y_err_low"], loc_point["y_err_high"]],
            [loc_point["z"], loc_point["z"]],
            linewidth=lw,
            # linestyle='-',
            color=c,
            alpha=alph,
        )
        ax.plot3D(
            [loc_point["x"], loc_point["x"]],
            [loc_point["y"], loc_point["y"]],
            [loc_point["z_err_low"], loc_point["z_err_high"]],
            linewidth=lw,
            # linestyle='-',
            color=c,
            alpha=alph,
        )
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_box_aspect([1, 1, 1])
    fig.tight_layout()

    # save figure
    fig.savefig("./localization_plot_all.png", bbox_inches="tight")

if __name__ == "__main__":
    main()