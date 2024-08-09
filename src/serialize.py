import re
from typing import List, Union, Dict
from pdulate.items import Patch, Subpatch, Object, Message, Number, Symbol, Array, Comment, ConnectableItem

    
def escape_special_chars(text):
    return re.sub(r'([,$;\\])', r'\\\1', str(text))

def serialize_patch(patch: Patch) -> str:
    lines = [f"#N canvas {patch.x} {patch.y} {patch.width} {patch.height} {patch.font_size};"]
    lines.extend(serialize_content(patch))
    return "\n".join(lines)

def serialize_object(obj: Union[Object, Message, Number, Symbol, Array, Comment, Subpatch]) -> List[str]:
    lines = []

    if isinstance(obj, Subpatch):
        lines.extend(serialize_subpatch(obj))

    elif isinstance(obj, Array):
        lines.append(f"#X array {obj.name} {obj.size} {obj.type} {obj.save_flag} {obj.draw_style};")
        if obj.data:
            # Write actual data in chunks to avoid very long lines
            chunk_size = 100
            for i in range(0, len(obj.data), chunk_size):
                chunk = obj.data[i:i+chunk_size]
                lines.append(f"#A {i} {' '.join(map(str, chunk))};")
        else:
            # If no data, initialize with zeros
            lines.append(f"#A 0 {' '.join(['0'] * obj.size)};")

    elif isinstance(obj, Object):
        escaped_args = [escape_special_chars(arg) for arg in obj.args]
        lines.append(f"#X obj {obj.x} {obj.y} {obj.name} {' '.join(escaped_args)};")

    elif isinstance(obj, Message):
        escaped_message = escape_special_chars(obj.message)
        width_str = f", f {obj.width}" if obj.width else ""
        lines.append(f"#X msg {obj.x} {obj.y} {escaped_message}{width_str};")

    elif isinstance(obj, Number):
        width_str = f", f {obj.width}" if obj.width is not None else ""
        lines.append(f"#X floatatom {obj.x} {obj.y} {obj.size} "
        f"{obj.lower} {obj.upper} {obj.receive} {obj.send} {obj.label} -{width_str};")
    
    elif isinstance(obj, Symbol):
        width_str = f", f {obj.width}" if obj.width is not None else ""
        lines.append(f"#X symbolatom {obj.x} {obj.y} {obj.size} {obj.lower} "
        f"{obj.upper} {obj.receive} {obj.send} {obj.label} -{width_str};")

    elif isinstance(obj, Comment):
        escaped_text = escape_special_chars(obj.text)
        width_str = f", f {obj.width}" if obj.width else ""
        lines.append(f"#X text {obj.x} {obj.y} {escaped_text}{width_str};")

    return lines

def serialize_content(patch: Patch) -> List[str]:
    lines = []
    objects = patch.get_items()
    # Create a map of objects to their indices
    object_index_map = {obj: i for i, obj in enumerate(objects)}
    # Write objects
    for obj in objects:
        lines.extend(serialize_object(obj))
    # Write connections
    lines.extend(serialize_connections(patch, object_index_map))
    return lines

def serialize_subpatch(subpatch: Subpatch) -> List[str]:
    lines = []
    if subpatch.graph_on_parent:
        lines.append(f"#N canvas {subpatch.x} {subpatch.y} "
        f"{subpatch.width} {subpatch.height} (subpatch) 0;")
    else:
        lines.append(f"#N canvas {subpatch.x} {subpatch.y} "
        f"{subpatch.width} {subpatch.height} {subpatch.name} {int(subpatch.graph_on_parent)};")
    
    lines.extend(serialize_content(subpatch))
    
    if subpatch.coords:
        lines.append(f"#X coords {' '.join(map(str, subpatch.coords))};")
    
    if subpatch.graph_on_parent:
        lines.append(f"#X restore {subpatch.external_x} {subpatch.external_y} graph;")
    else:
        lines.append(f"#X restore {subpatch.external_x} {subpatch.external_y} pd {subpatch.name};")

    return lines

def serialize_connections(patch: Subpatch, object_index_map: Dict[ConnectableItem, int]) -> List[str]:
    lines = []
    for obj in patch.get_items():
        if isinstance(obj, ConnectableItem):
            obj_index = object_index_map[obj]
            for outlet, connections in obj.get_outlets():
                for inlet, target in connections:
                    target_index = object_index_map[target]
                    lines.append(f"#X connect {obj_index} {outlet} {target_index} {inlet};")
    return lines
