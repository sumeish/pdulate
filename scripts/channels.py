"""
A script replacing all stereo [dac~] objects scattered around in a patch
into enumerated mono [dac~ n] channels (0->inf), which may then be connected
elsewhere, for example via Pipewire, and easily controlled.
"""

from pathlib import Path
from pdulate.tools import search_objects, replace
from pdulate.items import Subpatch, Object
from pdulate.serialize import serialize_patch
from pdulate.parser import Parser
import sys

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)

generous = False

def main():
    if len(sys.argv) < 2:
        print("Please provide a file path as a command-line argument.")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    channels(file_path)

def channels(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)
    except IOError:
        print(f"Error reading file: {file_path}")
        sys.exit(1)

    # Parse the patch
    parser = Parser()
    patch = parser.parse_patch(content)

    # Search for dac~
    all_dacs = search_objects(patch, r'dac~*')

    default_dacs = [dac for dac in all_dacs if not dac.args]

    if not default_dacs:
        logger.info(f"No [dac~] objects found.")
        sys.exit(0)
    
    highest_value = max([ int(arg)  for dac in all_dacs if dac.args for arg in dac.args ] + [0])

    n = highest_value + 1
    for dac in default_dacs:

        active_inlets = list(dac.get_inlets())

        if len(active_inlets) == 0:
            continue
        
        if len(active_inlets) == 1:
            replacement = Object(dac.x, dac.y, "dac~", [str(n)]) 
            _, conns = active_inlets[0]
            for outlet, item in conns:
                item.connect(outlet, replacement, 0)
            patch.add_item(replacement)
            patch.remove_item(dac)
            n += 1

        else:
            identical = True
            first = set(active_inlets[0][1])
            for _, conns in active_inlets[1:]:
                if set(conns) != first:
                    identical = False
                    break

            if identical:
                replacement = Object(dac.x, dac.y, "dac~", [str(n)]) 
                n += 1
            else:
                replacement = Object(dac.x, dac.y, "dac~", [str(n), str(n+1)]) 
                n += 2
            replace(patch, dac, replacement, collapse_inlets=identical)

    # Serialize the modified patch
    modified_content = serialize_patch(patch)

    # save
    new_file_path = file_path.with_name(f"{file_path.stem}.channeled{file_path.suffix}")

    try:
        with open(new_file_path, 'w') as file:
            file.write(modified_content)
        logger.info(f"Modified patch saved as {new_file_path}")
    except IOError:
        logger.error(f"Error writing to file: {new_file_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()