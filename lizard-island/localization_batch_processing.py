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

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument("--folder", type=str, default="2023-11-24_morning", help="Date and time of the folder to process")
    p.add_argument("--audio_dir", type=str, default=None, help="Path to the audio files directory")
    p.add_argument("--detections_dir", type=str, default=None, help="Path to the detections directory")
    p.add_argument("--output_dir", type=str, default=None, help="Path to the output directory")
    return p.parse_args()

def main():
    args = get_args()

    # params
    audio_dir = args.audio_dir if args.audio_dir else f"/tmp2/b12902135/whoi/audio/{args.folder}/"
    detections_dir = args.detections_dir if args.detections_dir else f"/tmp2/b12902135/whoi/Selections/{args.folder}/"
    output_dir = args.output_dir if args.output_dir else f"/tmp2/b12902135/whoi/localization_results/{args.folder}/"
    # if not exist then create output_dir
    os.makedirs(output_dir, exist_ok=True)

    # start file is the first one in detections_dir, which is the one that has been processed by Raven and has a corresponding selection table
    start_file = sorted(os.listdir(detections_dir))[0][:17] + ".wav"
    print(f"Start file: {start_file}", flush=True)
    nfiles = len(os.listdir(detections_dir))
    print(f"Number of files to process: {nfiles}", flush=True)

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
        hydrophones_config["data_path"] += f"{args.folder}/"
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

    start_file_index = 0
    start_processing = False
    count = 0
    # process nfiles starting from start_file 
    for idx, in_file in enumerate(os.listdir(audio_dir)):
        if in_file == start_file:
            start_file_index = idx
            start_processing = True
        if start_processing and idx < start_file_index + nfiles and in_file.endswith('.wav'):
            print(f"Processing file {count+1}/{nfiles}: {in_file}")

            # Look up data files for all channels
            print(f"Looking up audio files for {audio_dir+in_file}", flush=True)
            audio_files = tools.find_audio_files(audio_dir+in_file, hydrophones_config)

            # loading annotations from Raven selection table
            raven_detections_file = in_file.replace('.wav', '.Table.1.selections.txt')
            detections = Annotation()
            detections.from_raven(detections_dir+raven_detections_file, class_header=None, verbose=True)
            detections.data["audio_channel"] -= 1 # convert to 0-indexed
            # filter detections to only include those from the channel specified in detection_config
            detections = detections.filter(f"audio_channel == {detection_config['AUDIO']['channel']}")
            print(f"Loaded {len(detections)} detections from {raven_detections_file}", flush=True)

            # insert deployment metadata
            detections.insert_metadata(deployment_info_file, channel=detection_config['AUDIO']['channel'])

            # Perform localization using grid search
            localizations, PPDs = localization.GridSearch.run_localization(audio_files, detections, tdoa_grid, deployment_info_file, detection_config, hydrophones_config, localization_config, verbose=False)

            # Save localization results to CSV
            localizations.to_csv(output_dir + f'{in_file}.csv')
            localizations.to_netcdf(output_dir + f'{in_file}.nc')

            # Filter localization results, leave only those in front of the camera (y > 0.7931)
            new_localizations = localizations.filter("y > 0.7931") # inplace = True replaces the original datanew_localizations.
            new_localizations.to_csv(output_dir + f'{in_file}_filtered.csv')
            new_localizations.to_netcdf(output_dir + f'{in_file}_filtered.nc')

            count += 1

if __name__ == "__main__":
    main()