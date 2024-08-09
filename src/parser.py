import re
from typing import List, Dict, Any, Optional, Callable, Union
import logging

from pdulate.items import (
    Item, ConnectableItem, Message, Object, Number, Symbol,
    Array, Comment, Patch, Subpatch
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)

class PdParseError(Exception):
    """Custom exception for Pure Data parsing errors."""
    pass

def unescape_special_chars(text):
    return re.sub(r'\\([,$;\\])', r'\1', text)

class Parser:
    def __init__(self):
        self.clean()

    def clean(self):
        self.subpatch_stack: List[Patch] = []
        self.current_patch: Optional[Patch] = None
        self.expected: Optional[Callable[[str], None]] = None
        self.last_array: Optional[Array] = None

    def parse_patch(self, content: str) -> Patch:
        self.clean()
        self.expected = self.parse_global_canvas

        # Use regex to split the content into items, taking escaped ; into account
        items = re.split(r'(?<!\\);', content)
        for item in items:
            item = item.strip()
            if item:
                try:
                    if self.expected:
                        self.expected(item)
                    else:
                        self.parse_item(item)
                except Exception as e:
                    raise PdParseError(f"Error parsing item: {item[:100]+'...'}") from e

        if len(self.subpatch_stack) != 1:
            raise PdParseError("Mismatched subpatch structure")

        return self.subpatch_stack[0]

    def parse_global_canvas(self, string: str):
        if not string.startswith('#N canvas'):
            raise PdParseError(f"Expected global canvas, got: {string}")

        parts = string.split()
        if len(parts) != 7:
            raise PdParseError(f"Invalid global canvas format: {string}")

        x, y, width, height, font_size = map(int, parts[2:])
        self.current_patch = Patch(x, y, width, height, font_size)
        self.subpatch_stack.append(self.current_patch)
        self.expected = None

    def parse_canvas(self, string: str) -> Subpatch:
        parts = string.split()
        if len(parts) != 8:
            raise PdParseError(f"Invalid subpatch canvas format: {string}")

        x, y, width, height = map(int, parts[2:6])
        name = parts[6]
        graph_on_parent = bool(int(parts[7]))
        new_patch = Subpatch(x, y, width, height, name, graph_on_parent)
        self.current_patch.add_item(new_patch)
        self.subpatch_stack.append(new_patch)
        self.current_patch = new_patch
        return new_patch

    def parse_item(self, string: str) -> Optional[Item]:
        if string.startswith('#N canvas'):
            return self.parse_canvas(string)
        elif string.startswith('#X obj'):
            return self.parse_object(string)
        elif string.startswith('#X msg'):
            return self.parse_message(string)
        elif string.startswith('#X floatatom'):
            return self.parse_number(string)
        elif string.startswith('#X symbolatom'):
            return self.parse_symbol(string)
        elif string.startswith('#X text'):
            return self.parse_comment(string)
        elif string.startswith('#X connect'):
            self.parse_connection(string)
            return None
        elif string.startswith('#X coords'):
            self.parse_coords(string)
            return None
        elif string.startswith('#X array'):
            return self.parse_array(string)
        elif string.startswith('#A'):
            self.parse_array_data(string)
            return None
        elif string.startswith('#X restore'):
            return self.end_subpatch(string)
        else:
            raise PdParseError(f"Unhandled item: {string}")

    def parse_object(self, string: str) -> Object:
        parts = string.split()
        if len(parts) < 5:
            raise PdParseError(f"Invalid object format: {string}")

        x, y = int(parts[2]), int(parts[3])
        name = parts[4]

        args = [unescape_special_chars(arg) for arg in parts[5:]]
        obj = Object(x, y, name, args)
        self.current_patch.add_item(obj)
        return obj
    
    def parse_message(self, string: str) -> Message:
        match = re.match(r"#X msg (-?\d+) (-?\d+) (.+?)(?:, f (-?\d+))?$", string)
        if not match:
            raise PdParseError(f"Invalid message format: {string}")
        x, y, message, width = match.groups()
        message = unescape_special_chars(message)
        msg = Message(int(x), int(y), message)
        if width:
            msg.width = int(width)
        self.current_patch.add_item(msg)
        return msg
        
    def parse_number(self, string: str) -> Number:
        match = re.match(r'#X floatatom (-?\d+) (-?\d+) (\d+) (-?\d+) '
        r'(-?\d+) (-?\d+) (.+?) (.+?) (.+?)(?:, f (-?\d+))?$', string)
        if not match:
            raise PdParseError(f"Invalid number format: {string}")
        x, y, size, lower, upper, receive, send, label, _, width = match.groups()
        num = Number(int(x), int(y), 0.0)  # Default value set to 0.0
        num.size = int(size)
        num.lower = int(lower)
        num.upper = int(upper)
        num.receive = receive
        num.send = send
        num.label = label
        if width:
            num.width = int(width)
        self.current_patch.add_item(num)
        return num

    def parse_symbol(self, string: str) -> Symbol:
        match = re.match(r'#X symbolatom (-?\d+) (-?\d+) (\d+) '
        r'(-?\d+) (-?\d+) (-?\d+) (.+?) (.+?) (.+?)(?:, f (-?\d+))?$', string)
        if not match:
            raise PdParseError(f"Invalid symbol format: {string}")
        x, y, size, lower, upper, receive, send, label, _, width = match.groups()
        sym = Symbol(int(x), int(y), "")  # Default value set to empty string
        sym.size = int(size)
        sym.lower = int(lower)
        sym.upper = int(upper)
        sym.receive = receive
        sym.send = send
        sym.label = label
        if width:
            sym.width = int(width)
        self.current_patch.add_item(sym)
        return sym

    def parse_comment(self, string: str) -> Comment:
        match = re.match(r"#X text (-?\d+) (-?\d+) (.+?)(?:, f (-?\d+))?$", string)
        if not match:
            raise PdParseError(f"Invalid comment format: {string}")
        x, y, text, width = match.groups()
        comment = Comment(int(x), int(y), text)
        if width:
            comment.width = int(width)
        self.current_patch.add_item(comment)
        return comment

    def parse_connection(self, string: str):
        parts = string.split()
        if len(parts) != 6:
            raise PdParseError(f"Invalid connection format: {string}")

        source_id, source_outlet = int(parts[2]), int(parts[3])
        target_id, target_inlet = int(parts[4]), int(parts[5])

        objects = self.current_patch.get_items()

        if source_id >= len(objects) or target_id >= len(objects):
            raise PdParseError(f"Invalid object index in connection: {string}")

        source = objects[source_id]
        target = objects[target_id]

        source.connect(source_outlet, target, target_inlet)

    def parse_coords(self, string: str):
        parts = string.split()
        if len(parts) != 9:
            raise PdParseError(f"Invalid coords format: {string}")

        # Convert to float first, then to int if it's a whole number
        coords = []
        for part in parts[2:]:
            try:
                value = float(part)
                coords.append(int(value) if value.is_integer() else value)
            except ValueError:
                raise PdParseError(f"Invalid coordinate value: {part}")

        if isinstance(self.current_patch, Subpatch):
            self.current_patch.set_coords(*coords)
        else:
            logger.warning(f"Coords found outside of subpatch context: {string}")

    def parse_array(self, string: str) -> Array:
        parts = string.split()
        if len(parts) < 8:
            raise PdParseError(f"Invalid array format: {string}")

        name = parts[2]
        try:
            size = int(float(parts[3])) 
        except ValueError:
            raise PdParseError(f"Invalid size format in array: {string}")
        type = parts[4]
        save_flag = parts[5]
        draw_style = ' '.join(parts[6:])

        array = Array(0, 0, name, size, type, save_flag, draw_style)
        self.current_patch.add_item(array)
        self.last_array = array
        return array

    def parse_array_data(self, string: str):
        if not self.last_array:
            raise PdParseError(f"Unexpected array data: {string}")

        parts = string.split()
        if len(parts) < 2:
            raise PdParseError(f"Invalid array data format: {string}")

        try:
            start_index = int(float(parts[1]))
        except ValueError:
            raise PdParseError(f"Invalid size format in array: {string}")

        data = [float(x) for x in parts[2:]]

        if start_index + len(data) > self.last_array.size:
            logger.warning(f"Array data exceeds declared size. Declared: {self.last_array.size}, Actual: {start_index + len(data)}")

        self.last_array.data[start_index:start_index + len(data)] = data

    def end_subpatch(self, string: str) -> Optional[Subpatch]:
        match = re.match(r"#X restore (-?\d+) (-?\d+)", string)
        if not match:
            raise PdParseError(f"Invalid restore format: {string}")

        external_x, external_y = map(int, match.groups())

        if len(self.subpatch_stack) > 1:
            finished_subpatch = self.current_patch
            finished_subpatch.external_x = external_x
            finished_subpatch.external_y = external_y
            self.subpatch_stack.pop()
            self.current_patch = self.subpatch_stack[-1]
            return finished_subpatch
        else:
            raise PdParseError("Tried to end a subpatch, but no subpatch was active")

