import os
import argparse
import shutil
import pysrt
import pandas

def extract_data(data_dir, file):
    """
    Extracts data from Slicer file

    :param data_dir: directory of Slicer data file
    :param file: Slicer data file name
    """

    _,extension = file.split(".")  # get extension

    # Change extension of file to .zip in order to extract
    os.rename(os.path.join(data_dir, file), os.path.join(data_dir, file.replace(f".{extension}", ".zip")))

    if not os.path.exists(os.path.join(data_dir, file.replace(f".{extension}", "_extracted"))):
        # Create extracted version of file
        os.mkdir(os.path.join(data_dir, file.replace(f".{extension}", "_extracted")))

    # Unzip data
    shutil.unpack_archive(
        os.path.join(data_dir, file.replace(f".{extension}", ".zip")),
        os.path.join(data_dir, file.replace(f".{extension}", "_extracted"))
    )

    # Replace original file back to original state
    os.rename(os.path.join(data_dir, file.replace(f".{extension}", ".zip")), os.path.join(data_dir, file))

def parse_srt(srt_path):
    info = []
    file = pysrt.open(srt_path)
    for line in file:
        info.append(line.text)
    return info

def extract_timestamps(vid_path):
    """
    Extracts timestamps of frames from a .mkv video file

    :param vid_path: path of video file
    :return timestamps: list of timestamps
    """

    # Extract tracks from video
    os.system(
        f'mkvextract tracks "{vid_path}" 1:"{vid_path.replace(".mkv", "1.srt")}" 2:"{vid_path.replace(".mkv", "2.srt")}" 3:"{vid_path.replace(".mkv", "3.srt")}"'
    )
    track_1 = parse_srt(vid_path.replace(".mkv", "1.srt"))
    track_2 = parse_srt(vid_path.replace(".mkv", "2.srt"))
    track_3 = parse_srt(vid_path.replace(".mkv", "3.srt"))
    tracks = [track_1, track_2, track_3]

    timestamps = None
    frame_status = []
    for track in tracks:
        if "." in track[0]:
            timestamps = [float(x) for x in track]
        else:
            # Only get frames with a frame status of 0 (frames that were recorded)
            try:
                frame_status = [int(x) for x in track]
            except:
                pass

    # Only select timestamps for frames with a frame status of 0
    timestamps = [timestamps[i] for i in range(len(timestamps)) if frame_status[i] == 0]
    return timestamps

def update_csv_column(file_name, column_name, new_values):
    """
    Updates csv column with new values.
    new_values must be the same length as the number of rows in the given column.

    :param file_name:
    :param column_name:
    :param new_values:
    """
    df = pandas.read_csv(file_name)

    if len(df[column_name]) == len(new_values):
        df[column_name] = new_values
        df.to_csv(file_name, index=False)
        print("Successfully updated timestamps in CSV.")
    else:
        print("Number of frames is not consistent between sequence browser and label file."
              f"\nNumber of frames in CSV: {len(df[column_name])}"
              f"\nNumber of frames in sequence browser: {len(new_values)}"
              "\nAborting.")

def main(data_path, label_file_path):
    videos_file_names = {
        "RGB_above":"ImageRGB_ImageRGB-Sequence.mkv",
        "Depth_above":"ImageDEPTH_ImageDEPT-Sequence.mkv",
        "RGB_right":"Image1RGB_Image1RGB-Sequence.mkv",
        "Depth_right":"Image1DEPTH_Image1DE-Sequence.mkv"
    }

    # Extract timestamps from data file
    data_dir = os.path.dirname(data_path)
    file = os.path.basename(data_path)
    vid_id, *_ = file.split(".")
    extract_data(data_dir, file)
    vid_path = os.path.join(data_dir,f"{vid_id}_extracted",vid_id,"Data",videos_file_names["RGB_above"])
    timestamps = extract_timestamps(vid_path)
    if os.path.exists(os.path.join(data_dir, f"{vid_id}_extracted")):
        shutil.rmtree(os.path.join(data_dir, f"{vid_id}_extracted"))

    # Replace timestamps with new timestamps in CSV label file
    update_csv_column(label_file_path, "Time Recorded", timestamps)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Script that matches the timestamps from a sequence browser in Slicer to a CSV label file."
    )
    parser.add_argument("--data_path", required=True, type=str)
    parser.add_argument("--label_file_path", required=True, type=str)
    args = parser.parse_args()

    data_path = args.data_path
    label_file_path = args.label_file_path

    main(data_path, label_file_path)
