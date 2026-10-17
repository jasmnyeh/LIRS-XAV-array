import os
import pandas as pd

# read all csv files in the folder and concatnenate the ones that have values in the 'Annotation' column into a new dataframe with a new column 'filename' that contains the name of the csv
folder_path = "/Volumes/XMOUY_SDD3/LizardIsland/MobileArray_data/Selections/2023-11-24_morning/"
dataframes = []

print(f"Reading CSV files from folder: {folder_path}")
# df = pd.read_csv(os.path.join(folder_path, "5147.231123231849.Table.1.selections.txt"), sep='\t')
# count = df['Annotation'].notna().sum()
# print(f"Number of non-NaN values in 'Annotation' column: {count}")

for filename in os.listdir(folder_path):
    if filename.endswith(".txt"):
        print(f"Processing file: {filename}")
        df = pd.read_csv(os.path.join(folder_path, filename), sep="\t")
        if df['Annotation'].notna().sum() > 0:
            df = df[df['Annotation'].notna()]
            df['filename'] = filename
            dataframes.append(df)

if dataframes:
    result_df = pd.concat(dataframes, ignore_index=True)
    result_df.to_csv("./clear_signals.csv", index=False)