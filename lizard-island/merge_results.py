import os
import pandas as pd

result_folder = "/Volumes/XMOUY_SDD3/LizardIsland/MobileArray_data/2023-11-24_morning/localization_results/"
detection_folder = "/Volumes/XMOUY_SDD3/LizardIsland/MobileArray_data/2023-11-24_morning"

for i, detection_file in enumerate(os.listdir(detection_folder)):
    print(f"Processing file {i + 1}/{len(os.listdir(detection_folder))}: {detection_file}")
    filename = detection_file.replace('.Table.1.selections.txt', '')
    df_filtered_all = pd.DataFrame()
    df_all = pd.DataFrame()

    for result_file in os.listdir(result_folder):
        if result_file.startswith(filename):
            if result_file.endswith('_filtered.csv'):
                df_filtered = pd.read_csv(os.path.join(result_folder, result_file))
                df_filtered_all = pd.concat([df_filtered_all, df_filtered], ignore_index=True)
            elif result_file.endswith('.csv'):
                df = pd.read_csv(os.path.join(result_folder, result_file))
                df_all = pd.concat([df_all, df], ignore_index=True)
            print(f"  Processing result file: {result_file}")

    # save the concatenated dataframes to csv files
    df_filtered_all.to_csv(os.path.join(result_folder, f"{filename}_filtered_all.csv"), index=False)
    df_all.to_csv(os.path.join(result_folder, f"{filename}_all.csv"), index=False)