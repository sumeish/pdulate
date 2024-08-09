from typing import List, Dict, Tuple, Optional, Union
import logging
from collections.abc import ItemsView


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)

class Item:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.patch = None

class ConnectableItem(Item):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.inlets: Dict[int, List[int, 'ConnectableItem']] = {}
        self.outlets: Dict[int, List[int, 'ConnectableItem']] = {}

    def connect(self, outlet: int, target: 'ConnectableItem', inlet: int):
        """
        Connects the outlet of this item to the inlet of the target item.

        Parameters:
        outlet (int): The outlet index of this item.
        target (ConnectableItem): The target item to connect to.
        inlet (int): The inlet index of the target item.

        Note:
        It is up to the user to ensure that connections are valid in the
        context of their Pure Data patch.

        Raises:
        TypeError: If target is not an instance of ConnectableItem.
        """
        if not isinstance(target, ConnectableItem):
            raise TypeError(
                f"Target must be an instance of ConnectableItem, "
                f"got {type(target).__name__}"
            )

        if outlet not in self.outlets:
            self.outlets[outlet] = []
        if inlet not in target.inlets:
            target.inlets[inlet] = []

        self.outlets[outlet].append((inlet, target))
        target.inlets[inlet].append((outlet, self))
        logger.debug(
            f"Connected {self} outlet {outlet} to {target} inlet {inlet}"
        )

    def disconnect(self, outlet: int, target: 'ConnectableItem', inlet: int):
        conns = self.outlets.get(outlet)
        if conns and (inlet, target) in conns:
            self.outlets[outlet].remove((inlet, target))
            if not self.outlets[outlet]:  # Clean up if the list is empty
                del self.outlets[outlet]
            if (outlet, self) in target.inlets.get(inlet):
                target.inlets[inlet].remove((outlet, self))
                if not target.inlets[inlet]:  # Clean up if the list is empty
                    del target.inlets[inlet]
            logger.debug(
                f"Disconnected {self} outlet {outlet} from {target} inlet {inlet}"
            )
        return

        logger.warning(
            f"No connection found from {self} outlet {outlet} to "
            f"{target} inlet {inlet} to disconnect."
        )

    def get_outlets(self) -> ItemsView[int, List[Tuple[int, 'ConnectableItem']]]:
        """
        Returns an ItemView with active outlets and their associated connections,
        each connections is a tuple (int, Item), where the int represents the inlet
        in the target Item used for the connection.
        """
        return [(outlet, conns) for outlet, conns in self.outlets.items() if conns]

    def get_inlets(self) -> ItemsView[int, List[Tuple[int, 'ConnectableItem']]]:
        """
        Returns an ItemView with active inlets and their associated connections,
        each connections is a tuple (int, Item), where the int represents the outlet
        in the source Item used for the connection.
        """
        return [(inlet, conns) for inlet, conns in self.inlets.items() if conns]

class Message(ConnectableItem):
    def __init__(self, x: int, y: int, message: str, width: Optional[int] = None):
        super().__init__(x, y)
        self.message = message
        self.width = width

    def __repr__(self):
        return f"Message({self.x}, {self.y}, {self.message}, width={self.width})"

class Object(ConnectableItem):
    def __init__(self, x: int, y: int, name: str, args: List[str]):
        super().__init__(x, y)
        self.name = name
        self.args = args

    def __repr__(self):
        return f"Object({self.x}, {self.y}, {self.name}, {self.args})"

class Number(ConnectableItem):
    def __init__(self, x: int, y: int, value: float, width: Optional[int] = None):
        super().__init__(x, y)
        self.value = value
        self.size = 0
        self.lower = 0
        self.upper = 0
        self.receive = "-"
        self.send = "-"
        self.label = "-"
        self.width = width

    def __repr__(self):
        return f"Number({self.x}, {self.y}, {self.value}, size={self.size}, "
        f"lower={self.lower}, upper={self.upper}, receive={self.receive}, "
        f"send={self.send}, label={self.label}, width={self.width})"

class Symbol(ConnectableItem):
    def __init__(self, x: int, y: int, value: str, width: Optional[int] = None):
        super().__init__(x, y)
        self.value = value
        self.size = 0
        self.lower = 0
        self.upper = 0
        self.receive = "-"
        self.send = "-"
        self.label = "-"
        self.width = width

    def __repr__(self):
        return f"Symbol({self.x}, {self.y}, {self.value}, size={self.size}, "
        f"lower={self.lower}, upper={self.upper}, receive={self.receive},"
        f"send={self.send}, label={self.label}, width={self.width})"

    def __repr__(self):
        return f"Symbol({self.x}, {self.y}, {self.value}, width={self.width})"

class Array(Object):
    def __init__(self, x: int, y: int, name: str, size: int, type: str, save_flag: str, draw_style: str):
        super().__init__(x, y, name, [str(size), type, save_flag, draw_style])
        self.size = size
        self.type = type
        self.save_flag = save_flag
        self.draw_style = draw_style
        self.data: List[float] = [0.0] * size

    def set_data(self, data: List[float]):
        if len(data) != self.size:
            raise ValueError(f"Data size ({len(data)}) does not match array size ({self.size})")
        self.data = data

    def __repr__(self):
        data_repr = f"[{self.data[0]:.3f}, ..., {self.data[-1]:.3f}]" if self.data else "[]"
        return f"Array({self.x}, {self.y}, {self.name}, size={self.size}, type={self.type}, save_flag={self.save_flag}, draw_style={self.draw_style}, data={data_repr})"

class Comment(Item):
    def __init__(self, x: int, y: int, text: str, width: Optional[int] = None):
        super().__init__(x, y)
        self.text = text
        self.width = width

    def __repr__(self):
        return f"Comment({self.x}, {self.y}, {self.text}, width={self.width})"

class Patch:
    def __init__(self, x: int, y: int, width: int, height: int, font_size=12):
        self.items: List[Item] = []
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font_size = font_size

    def add_item(self, item: Item):
        self.items.append(item)
        item.patch = self
        logger.debug(f"Added {item} to patch")

    def add_items(self, items: List[Item]):
        for item in items:
            self.add_item(item)

    def remove_item(self, item: Item):
        if isinstance(item, ConnectableItem):
            # Remove incoming connections
            for inlet, connections in item.get_inlets():
                for outlet, source in connections.copy():
                    source.disconnect(outlet, item, inlet)

            # Remove outgoing connections
            for outlet, connections in item.get_outlets():
                for inlet, target in connections.copy():
                    item.disconnect(outlet, target, inlet)

        self.items.remove(item)
        logger.debug(f"Removed {item} from patch")

    def get_location(self) -> Tuple[int, int]:
        return self.x, self.y

    def set_location(self, x: int, y: int):
        self.x = x
        self.y = y

    def get_size(self) -> Tuple[int, int]:
        return self.width, self.height

    def get_font_size(self) -> Optional[int]:
        return self.font_size

    def set_font_size(self, font_size):
        self.font_size = font_size

    def set_size(self, width: int, height: int):
        self.width = width
        self.height = height

    def get_items(self) -> List[Item]:
        return self.items
        
    def __repr__(self):
        return (f"Patch(location=({self.x}, {self.y}), size=({self.width}, {self.height}), "
                f"fonts-size={self.font_size}, items={len(self.items)})")

class Subpatch(ConnectableItem, Patch):
    def __init__(self, x: int, y: int, width: int, height: int, name: str='(subpatch)', graph_on_parent=False):
        ConnectableItem.__init__(self, x, y)
        Patch.__init__(self, 0, 0, width, height)  # Internal coordinates start at (0, 0)
        self.name = name
        self.graph_on_parent: bool = graph_on_parent
        self.coords: Optional[List[Union[int, float]]] = None
        self.external_x = x  # External coordinates
        self.external_y = y  # External coordinates

    def set_coords(self, x1: Union[int, float], y1: Union[int, float], 
                   x2: Union[int, float], y2: Union[int, float], 
                   width: int, height: int, graph_on_parent: int):
        self.coords = [x1, y1, x2, y2, width, height, graph_on_parent]
        self.graph_on_parent = bool(graph_on_parent)

    def get_coords(self) -> Optional[List[Union[int, float]]]:
        return self.coords

    def is_graph_on_parent(self) -> bool:
        return self.graph_on_parent

    def set_graph_on_parent(self, graph_on_parent: bool):
        self.graph_on_parent = graph_on_parent

    def get_name(self) -> str:
        return self.name

    def set_external_x(self, x):
        self.external_x = x

    def set_external_y(self, y):
        self.external_y = y

    def set_name(self, name: str):
        self.name = name

    def __repr__(self):
        coords_str = f", coords={self.coords}" if self.coords else ""
        return (f"Subpatch(location=({self.external_x}, {self.external_y}), size=({self.width}, {self.height}), "
                f"name={self.name}, graph_on_parent={self.graph_on_parent}{coords_str}, "
                f"items={len(self.items)})")