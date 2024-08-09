import os
import argparse
from pathlib import Path
from pdulate.parser import Parser
from pdulate.items import Patch, Subpatch, Object, Message
from pdulate.common import ArrayPatch
from pdulate.serialize import serialize_patch
from pdulate import tools
import soundfile as sf
import resampy
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

AUDIO_EXTENSIONS = ('.wav', '.aiff', '.flac', '.ogg', '.mp3')

def is_audio_file(file_path):
    return file_path.lower().endswith(AUDIO_EXTENSIONS)

def process_audio_file(file_path, target_samplerate):
    try:
        data, samplerate = sf.read(file_path)
        if target_samplerate and samplerate != target_samplerate:
            data = resampy.resample(data, samplerate, target_samplerate, axis=0)
            logger.info(f"Resampled {file_path} from {samplerate} to {target_samplerate} Hz")
        return data
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
        return None

def create_array_patch(name, data, x, y):
    return ArrayPatch(x, y, name, len(data), data.tolist())

def process_path(path, target_samplerate, prefix=''):
    new_arrays = {}
    if os.path.isfile(path) and is_audio_file(path):
        data = process_audio_file(path, target_samplerate)
        if data is not None:
            array_name = Path(path).stem
            if prefix:
                array_name = f"{prefix}_{array_name}"
            if len(data.shape) == 1:  # Mono
                new_arrays[array_name] = create_array_patch(array_name, data, 0, 0)
            else:  # Multi-channel
                for i in range(data.shape[1]):
                    channel_name = f"{array_name}_{i+1}"
                    new_arrays[channel_name] = create_array_patch(channel_name, data[:, i], 0, 0)
                    
    elif os.path.isdir(path):
        dir_name = os.path.basename(path)
        for root, _, files in os.walk(path):
            for file in filter(is_audio_file, files):
                new_arrays.update(process_path(os.path.join(root, file), target_samplerate, dir_name))
    return new_arrays

def load_audio(audio_paths, patch_path, target_samplerate=None):
    # Load or create the patch
    if os.path.exists(patch_path):
        with open(patch_path, 'r') as f:
            content = f.read()
        parser = Parser()
        patch = parser.parse_patch(content)
    else:
        patch = Patch(0, 0, 800, 600)

    # Find or create the "audio_files" subpatch
    old_audio_subpatch = next((item for item in patch.get_items() if isinstance(item, Subpatch) and item.name == "audio_files"), None)
    audio_subpatch = Subpatch(20, 20, 200, 200, "audio_files")
    patch.add_item(audio_subpatch)

    # Process all new audio files
    new_arrays = {}
    for path in audio_paths:
        new_arrays.update(process_path(path, target_samplerate))

    # Update existing arrays
    if old_audio_subpatch:
        for item in old_audio_subpatch.get_items():
            array_patch = ArrayPatch.from_patch(item)
            if array_patch:
                if array_patch.get_name() in new_arrays:
                    new_array_patch = new_arrays.pop(array_patch.get_name())
                    audio_subpatch.add_item(new_array_patch)
                    # tools.replace would consider location and connections - We don't need it
                else:
                    audio_subpatch.add_item(array_patch)
        patch.remove_item(old_audio_subpatch)

    for array_patch in new_arrays.values():
        audio_subpatch.add_item(array_patch)

    # Adjust positions
    x_offset, y_offset = 10, 10
    for item in audio_subpatch.get_items():
        item.set_external_x(x_offset)
        item.set_external_y(y_offset)
        y_offset += 150
        if y_offset > 600:
            y_offset = 10
            x_offset += 210

    # Create a new subpatch for routing and playback if the total number of arrays is <= 128
    old_playback_subpatch = next((item for item in patch.items if isinstance(item, Subpatch) and item.name == "play_file"), None)
    if old_playback_subpatch:
        patch.remove_item(old_playback_subpatch)

    total_arrays = len(audio_subpatch.get_items())
    if total_arrays <= 128:
        playback_subpatch = Subpatch(20, 50, 200, 200, "play_file")
        
        # Create receive object
        receive_obj = Object(10, 10, "inlet", [])
        playback_subpatch.add_item(receive_obj)

        # Numbers go into a [route] object
        route_obj = Object(10, 40, "route", list(range(total_arrays)))
        playback_subpatch.add_item(route_obj)
        receive_obj.connect(0, route_obj, 0)

        # Bang & set array
        tbs_obj = Object(10, 100, 't', ['b', 's'])
        playback_subpatch.add_item(tbs_obj)
        set_msg = Message(40, 140, "set $1")
        playback_subpatch.add_item(set_msg)
        tbs_obj.connect(1, set_msg, 0)

        # Arrays to choose from -> convert & set array
        for i, item in enumerate(audio_subpatch.get_items()):
            msg_obj = Message(10 + i*10, 70, item.get_name())
            playback_subpatch.add_item(msg_obj)
            route_obj.connect(i, msg_obj, 0)
            msg_obj.connect(0, tbs_obj, 0)

        # Connect to a tabplay~ object
        tabplay_obj = Object(10, 170, "tabplay~", [])
        playback_subpatch.add_item(tabplay_obj)
        set_msg.connect(0, tabplay_obj, 0) # Set array
        tbs_obj.connect(0, tabplay_obj, 0) # Bang

        # Send out
        outlet_obj = Object(10, 200, "outlet~", [])
        playback_subpatch.add_item(outlet_obj)
        tabplay_obj.connect(0, outlet_obj, 0)

        # Add the playback subpatch to the main patch
        patch.add_item(playback_subpatch)

    # Serialize and save the modified patch
    modified_content = serialize_patch(patch)
    with open(patch_path, 'w') as file:
        file.write(modified_content)
    logger.info(f"Modified patch saved as {patch_path}")

def main():
    parser = argparse.ArgumentParser(description="Load audio files into a Pure Data patch.")
    parser.add_argument('--sample-rate', type=int, nargs='?', help='Target sample rate for audio files')
    parser.add_argument('patch', type=str, help='Path to the patch file')
    parser.add_argument('audio_path', nargs='+', type=str, help='List of audio files, or directories containing them, to load')

    args = parser.parse_args()
    load_audio(args.audio_path, args.patch, args.sample_rate)

if __name__ == "__main__":
    main()
