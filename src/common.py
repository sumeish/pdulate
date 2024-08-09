from pdulate.items import Object, Subpatch, Array
from typing import List, Optional

class Hsl(Object):
    def __init__(self, x: int, y: int, width: int = 128, height: int = 15,
                 min_value: float = 0, max_value: float = 127, default_value: float = 0,
                 save_flag: int = 1, send: str = "empty", receive: str = "empty",
                 label: str = "empty", x_off: int = -2, y_off: int = -8,
                 font_size: int = 0, label_color: int = 10,
                 bg_color: str = "#fcfcfc", fg_color: str = "#000000",
                 label_color2: str = "#000000", log_flag: int = 0,
                 init_flag: int = 1, steady_flag: int = 1):
        args = [
            str(width), str(height), str(min_value), str(max_value),
            str(default_value), str(save_flag), send, receive, label,
            str(x_off), str(y_off), str(font_size), str(label_color),
            bg_color, fg_color, label_color2, str(log_flag),
            str(init_flag), str(steady_flag)
        ]
        super().__init__(x, y, "hsl", args)

class Vsl(Object):
    def __init__(self, x: int, y: int, width: int = 15, height: int = 128,
                 min_value: float = 0, max_value: float = 127, default_value: float = 0,
                 save_flag: int = 1, send: str = "empty", receive: str = "empty",
                 label: str = "empty", x_off: int = -2, y_off: int = -8,
                 font_size: int = 0, label_color: int = 10,
                 bg_color: str = "#fcfcfc", fg_color: str = "#000000",
                 label_color2: str = "#000000", log_flag: int = 0,
                 init_flag: int = 1, steady_flag: int = 1):
        args = [
            str(width), str(height), str(min_value), str(max_value),
            str(default_value), str(save_flag), send, receive, label,
            str(x_off), str(y_off), str(font_size), str(label_color),
            bg_color, fg_color, label_color2, str(log_flag),
            str(init_flag), str(steady_flag)
        ]
        super().__init__(x, y, "vsl", args)

class Tgl(Object):
    def __init__(self, x: int, y: int, size: int = 15,
                 init_value: int = 0, save_flag: int = 1,
                 send: str = "empty", receive: str = "empty",
                 label: str = "empty", x_off: int = -2, y_off: int = -8,
                 font_size: int = 0, label_color: int = 10,
                 bg_color: str = "#fcfcfc", fg_color: str = "#000000",
                 label_color2: str = "#000000", init_flag: int = 0,
                 steady_flag: int = 1):
        args = [
            str(size), str(init_value), str(save_flag),
            send, receive, label, str(x_off), str(y_off),
            str(font_size), str(label_color), bg_color,
            fg_color, label_color2, str(init_flag), str(steady_flag)
        ]
        super().__init__(x, y, "tgl", args)

class ArrayPatch(Subpatch):
    def __init__(self, x: int, y: int, name: str, size: int, 
                 data: Optional[List[float]] = None,
                 type: str = "float", save_flag: str = "3", 
                 draw_style: str = "0", color1: str = "black", 
                 color2: str = "black"):
        super().__init__(x, y, 200, 140)

        self._array = Array(0, 0, name, size, type, save_flag, f"{color1} {color2}")
        
        # If data is provided, ensure save_flag is set to save content
        if data is not None:
            if size != len(data):
                raise ValueError(f"size: {size} != len(data): {len(data)}")
            self._array.set_data(data)
            
            # Set coords based on the data
            data_min = min(data)
            data_max = max(data)
        else:
            # Default range if no data is provided
            data_min = -1
            data_max = 1
        
        # Set coords as an attribute
        self.set_coords(0, data_max, size, data_min, 200, 140, 1)

    @classmethod
    def from_patch(cls, patch: Subpatch) -> Optional['ArrayPatch']:
        if isinstance(patch, Subpatch) and len(patch.items) == 1 and isinstance(patch.get_items()[0], Array):
            array = patch.get_items()[0]
            return cls(patch.x, patch.y, array.name, array.size, array.data,
                array.type, array.save_flag, array.draw_style)
        return None

    def add_item(self, item):
        raise NotImplementedError("Cannot add items to ArrayPatch")

    def get_name(self):
        return self._array.name

    def get_items(self):
        return [self._array]

    def len(self):
        return self._array.data.len()

    def get_data(self):
        return self._array.data

class Bng(Object):
    def __init__(self, x: int, y: int, size: int = 15,
                 hold: int = 250, interrupt: int = 50,
                 init: int = 0, send: str = "empty", receive: str = "empty",
                 label: str = "", x_off: int = 0, y_off: int = -8,
                 font: int = 10, bg_color: str = "-262144", fg_color: str = "-1",
                 label_color: str = "-1"):
        args = [
            str(size), str(hold), str(interrupt), str(init),
            send, receive, label, str(x_off), str(y_off),
            str(font), bg_color, fg_color, label_color
        ]
        super().__init__(x, y, "bng", args)
