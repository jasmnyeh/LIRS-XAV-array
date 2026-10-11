import argparse
import os
import sys
import ecosound.core.tools
from ecosound.core.metadata import DeploymentInfo
from ecosound.core.annotation import Annotation
import ecosound
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
sys.path.append('../localization')
import tools
import detection
import localization
import copy

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument("--folder", type=str, default="2023-11-24_morning", help="Date and time of the folder to process")
    p.add_argument("--audio_dir", type=str, default=None, help="Path to the audio files directory")
    p.add_argument("--detections_dir", type=str, default=None, help="Path to the detections directory")
    p.add_argument("--output_dir", type=str, default=None, help="Path to the output directory")
    p.add_argument("--batch_size", type=int, default=30, help="Number of detections to process in each batch")
    return p.parse_args()

def main():
    args = get_args()

    # params
    audio_dir = args.audio_dir if args.audio_dir else f"/Volumes/XMOUY_SDD3/LizardIsland/MobileArray_data/{args.folder}/ST/5147/"
    detections_dir = args.detections_dir if args.detections_dir else f"/Users/jasmineyeh/Desktop/WHOI/Selections/{args.folder}/"
    output_dir = args.output_dir if args.output_dir else f"/Volumes/XMOUY_SDD3/LizardIsland/MobileArray_data/{args.folder}/localization_results/"
    # if not exist then create output_dir
    os.makedirs(output_dir, exist_ok=True)

    # deployment metadata
    deployment_info_file = r'./config/deployment_info.csv'
    Deployment = DeploymentInfo()
    Deployment.read(deployment_info_file)
    print("Loaded deployment metadata", flush=True)

    # hydrophone configs
    hydrophones_config_file = r'./config/hydrophones_config_LIRS-ROV.csv'
    hydrophones_config= pd.read_csv(hydrophones_config_file, skipinitialspace=True, dtype={'name': str, 'file_name_root': str})
    # fix hydrophone data path
    if args.audio_dir:
        hydrophones_config["data_path"] = args.audio_dir
    else:
        hydrophones_config["data_path"] += f"{args.folder}/ST/5147/"
    print("Loaded hydrophone configs", flush=True)

    # detection configs
    detection_config_file = r'./config/detection_config_LIRS-ROV.yaml'
    detection_config = ecosound.core.tools.read_yaml(detection_config_file)
    print("Loaded detection configs", flush=True)

    # localization configs
    localization_config_file = r'./config/localization_config_LIRS-ROV.yaml'
    localization_config = ecosound.core.tools.read_yaml(localization_config_file)
    print("Loaded localization configs", flush=True)

    # create TDOA grid for grid search
    tdoa_grid_file = r'./tdoa_grid.npz'
    localization.GridSearch.create_tdoa_grid(localization_config['GRIDSEARCH']['x_limits_m'],
                                                localization_config['GRIDSEARCH']['y_limits_m'],
                                                localization_config['GRIDSEARCH']['z_limits_m'],
                                                localization_config['GRIDSEARCH']['spacing_m'],
                                                hydrophones_config,
                                                localization_config['TDOA']['ref_channel'],
                                                localization_config['ENVIRONMENT']['sound_speed_mps'],
                                                tdoa_grid_file)

    # load grid of precomputed TDOAs
    tdoa_grid = localization.GridSearch.load_tdoa_grid(tdoa_grid_file)
    print("Created TDOA grid for grid search", flush=True)

    # for all files in detections_dir, find the corresponding audio file in audio_dir and process it
    num_files = len(os.listdir(detections_dir))

    for idx, in_file in enumerate(sorted(os.listdir(detections_dir))):
        print(f"Processing file {idx + 1}/{num_files}: {in_file}")
        audio_file = in_file.replace('.Table.1.selections.txt', '.wav')
        audio_files = tools.find_audio_files(audio_dir+audio_file, hydrophones_config)

        # loading annotations from Raven selection table
        detections = Annotation()
        detections.from_raven(detections_dir+in_file, class_header=None, verbose=True)
        detections.data["audio_channel"] -= 1 # convert to 0-indexed

        # filter detections to only include those from the channel specified in detection_config
        detections = detections.filter(f"audio_channel == {detection_config['AUDIO']['channel']}")
        print(f"Loaded {len(detections)} detections from {in_file}", flush=True)

        # insert deployment metadata
        detections.insert_metadata(deployment_info_file, channel=detection_config['AUDIO']['channel'])
        
        # split detections into batches of args.batch_size detections, or else the memory usage will be too high for the grid search
        full_data = detections.data.copy()
        batch_num = len(detections) // args.batch_size + 1

        for batch_idx in range(batch_num):
            print(f"Processing batch {batch_idx + 1}/{batch_num}", flush=True)
            index = batch_idx * args.batch_size
            detections_batch = copy.deepcopy(detections)
            if batch_idx == batch_num: # last batch, may have less than args.batch_size detections
                detections_batch.data = detections.data[index:]
                detections_batch.data = full_data[index:].reset_index(drop=True)
            else:
                detections_batch.data = full_data[index:index+args.batch_size].reset_index(drop=True)
            
            # Perform localization using grid search
            localizations, PPDs = localization.GridSearch.run_localization(audio_files, detections_batch, tdoa_grid, deployment_info_file, detection_config, hydrophones_config, localization_config, verbose=False)

            save_filename = in_file.replace('.Table.1.selections.txt', f'_batch{batch_idx}')
            # Save localization results to CSV
            localizations.to_csv(output_dir + f'{save_filename}.csv')
            localizations.to_netcdf(output_dir + f'{save_filename}.nc')

            # Filter localization results, leave only those in front of the camera (y > 0.7931)
            if len(localizations) > 0:
                new_localizations = localizations.filter("y > 0.7931") # inplace = True replaces the original datanew_localizations.
                new_localizations.to_csv(output_dir + f'{save_filename}_filtered.csv')
                new_localizations.to_netcdf(output_dir + f'{save_filename}_filtered.nc')
            else:
                print("No localizations in this chunk, skipping")
                continue

if __name__ == "__main__":
    main()