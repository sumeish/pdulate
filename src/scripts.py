import sys
import os
import argparse
from pathlib import Path

# Import scripts
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

def main():
    parser = argparse.ArgumentParser(description="pdulate CLI")
    subparsers = parser.add_subparsers(dest='command')

    # Subparser for the "channels" command
    parser_channels = subparsers.add_parser('channels', help='Process a file with channels')
    parser_channels.add_argument('file_path', type=str, help='Path to the file')

    # Subparser for the "loadaudio" command
    parser_loadaudio = subparsers.add_parser('load-audio', help='Load audio files into a Pure Data patch.')
    parser_loadaudio.add_argument('--sample-rate', type=int, nargs='?', help='Target sample rate for conversions')
    parser_loadaudio.add_argument('patch', type=str, help='Path to the patch file')
    parser_loadaudio.add_argument('path', nargs='+', type=str, help='List of audio files an dirrectories containing them to load')

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except:
        pass
    args = parser.parse_args()

    if args.command == 'channels':
        from scripts.channels import channels
        channels(Path(args.file_path))
    elif args.command == 'load-audio':
        from scripts.load_audio import load_audio
        load_audio(args.path, args.patch, args.sample_rate)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
