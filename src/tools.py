from typing import List, Dict, Tuple, Optional, Union
import re
from pathlib import Path
from pdulate.items import ConnectableItem, Item, Patch, Object, Subpatch, Array, Comment
from pdulate.parser import Parser
from fnmatch import fnmatch
from itertools import chain

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)

def search_objects(patch: Patch, pattern: str) -> List[Object]:
    """
    Unix shell style search for objects in a patch by name and arguments.

    Args:
        patch (Patch): The Pure Data patch to search within.
        pattern (str): A pattern to match item names and arguments.

    Returns:
        List[Object]: A list of matching objects.
    """
    
    matching_objects = []
    for item in patch.get_items():
        if isinstance(item, Object):
            object_str = f"{item.name} {' '.join(item.args)}".strip()
            if fnmatch(object_str, pattern):
                matching_objects.append(item)
    
    logger.info(f"Found {len(matching_objects)} objects matching {pattern}")
    return matching_objects

def search_comments(patch: Patch, pattern: str) -> List[Comment]:
    """
    Unix shell style search for comments in a patch by text pattern.

    Args:
        patch (Patch): The Pure Data patch to search within.
        pattern (str): A pattern to match comment text.

    Returns:
        List[Comment]: A list of matching comments.
    """
    if not isinstance(patch, Patch):
        raise TypeError("patch must be an instance of Patch")
    
    matching_comments = []
    for item in patch.get_items():
        if isinstance(item, Comment):
            if fnmatch(item.text, pattern):
                matching_comments.append(item)
    
    logger.info(f"Found {len(matching_comments)} comments matching {pattern}")
    return matching_comments

def duplicate(patch: Patch, items: List[Item], x=0, y=0) -> List[Item]:
    """
    Duplicate a list of items and move them (x, y) away from the original.

    Args:
        items (List[ConnectableItem]): A list of items to duplicate.

    Returns:
        List[ConnectableItem]: A list of duplicated items.
    """
    duplicated_items = []
    for item in items:
        if isinstance(item, Object):
            new_item = Object(item.x, item.y, item.name, item.args.copy())
        elif isinstance(item, Subpatch):
            new_item = Subpatch(item.x, item.y, item.width, item.height, item.name, item.graph_on_parent)
        elif isinstance(item, Array):
            new_item = Array(item.x, item.y, item.name, item.size, item.type, item.save_flag, item.draw_style)
            new_item.data = item.data.copy() if item.data else None
        else:
            continue  # Skip unsupported item types
        
        duplicated_items.append(new_item)

    for item in duplicated_items:
        item.x += x
        item.y += y
        patch.add_item(item)
    
    return duplicated_items

def replace(patch: Patch, old_item: Item, new_item: Item, collapse_inlets=False):
    """
    Replace an item in a patch with a new item, preserving connections.

    Args:
        patch (Patch): The patch containing the item to be replaced.
        old_item (Item): The item to be replaced.
        new_item (Item): The new item to replace the old one.
        collapse_inlets (bool): Connect all original sources to the first inlet of new_item.
    """

    new_item.x = old_item.x
    new_item.y = old_item.y 

    # Transfer connections
    if isinstance(old_item, ConnectableItem) and isinstance(new_item, ConnectableItem):
        # Transfer outgoing connections
        for outlet, connections in old_item.get_outlets():
            for inlet, target in connections:
                new_item.connect(outlet, target, inlet)
        
        # Transfer incoming connections
        for inlet, connections in old_item.get_inlets().copy():
            for outlet, source in connections.copy():
                source.connect(outlet, new_item, inlet if not collapse_inlets else 0)

    # Add new item and remove old item
    patch.add_item(new_item)
    patch.remove_item(old_item)

