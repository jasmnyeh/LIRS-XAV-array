import os
import pandas as pd

result_folder = "/Volumes/XMOUY_SDD3/LizardIsland/MobileArray_data/2023-11-24_morning/localization_results/"
detection_folder = "/Volumes/XMOUY_SDD3/LizardIsland/MobileArray_data/2023-11-24_morning/"

output_df = pd.DataFrame(columns=['idx', 'filename', 'annotations', 'localizations', 'filtered'])
num_files = len(os.listdir(detection_folder))

for i, detection_file in enumerate(sorted(os.listdir(detection_folder))):
    output_df.loc[i, 'idx'] = i + 1
    output_df.loc[i, 'filename'] = detection_file.replace('.Table.1.selections.txt', '')
    output_df.loc[i, 'annotations'] = 0
    output_df.loc[i, 'localizations'] = 0
    output_df.loc[i, 'filtered'] = 0

    print(f"Processing file {i + 1}/{num_files}: {detection_file}")
    filename = detection_file.replace('.Table.1.selections.txt', '')

    for result_file in os.listdir(result_folder):
        if result_file == f"{filename}_filtered_all.csv":
            with open(os.path.join(result_folder, result_file), 'r') as f:
                num_lines = sum(1 for line in f) - 1  # subtract 1 for header
                output_df.loc[i, 'filtered'] += num_lines
        elif result_file == f"{filename}_all.csv":
            with open(os.path.join(result_folder, result_file), 'r') as f:
                num_lines = sum(1 for line in f) - 1  # subtract 1 for header
                output_df.loc[i, 'annotations'] += num_lines
                # count the ones that 'x' is not NaN
                df = pd.read_csv(os.path.join(result_folder, result_file))
                output_df.loc[i, 'localizations'] += df['x'].notna().sum()

print(output_df)
output_df.to_csv(os.path.join(result_folder, "localization_results_summary.csv"), index=False)
                
