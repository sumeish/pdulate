# Pdulate

An incomplete and probably buggy library for manipulating Pure Data files, made to automate repetitive boring organizational tasks. Scripts utilizing this library are included, serving as examples, but they can also be installed and used as shown bellow.

## Installation
```bash
git clone https://github.com/sumeish/pdulate.git
cd pdulate
pip install .
```
For an easy access to included scripts, install with CLI support:
```bash
pip install .[cli]
```
You can then use them with:
```bash
pdu command [args...]
```
To enable autocompletion in bash:
```bash
pip install argcomplete
activate-global-python-argcomplete --user
echo 'eval "$(register-python-argcomplete pdu)"' >> ~/.bashrc
```

## Scripts
Currently two scripts are included:

### Channels

[scripts/channels.py]() takes a path to a Pure Data patch and converts all used \[dac~\] (with no arguments) objects scattered throughout your patch into properly enumerated ones, transforming your easy-to-sketch patch, into a clear, easy-to-mix, suitable for transfer (e.g. through Pipewire) patch. If some \[dac~\] objects do have arguments, the enumeration will start above it to avoid interference.

### Load_audio

[load_audio]() takes a path to a Pure Data patch and one or more paths to audio files (wav, aiff, flac, ogg and mp3 are all accepted) and directories containing them. It adds all the audio files to the specified patch or the newly create one. Optionally you can specify a sample rate for conversion. 

For example:

```bash
python scripts/load_audio.py --sample-rate=44100 patch.pd file1.wav file2.flac
```
Or, if scripts are installed, simply:
```bash
pdu --sample-rate=44100 patch file1.wav file2.flac
```
You can use [find]() and [xargs]() to load all files matching a pattern:
```bash
find sounds -ipath '*soft*' | xargs -0 pdu load_audio --sample-rate=96000 patch.pd
```

## License

This is free and unencumbered software released into the public domain.