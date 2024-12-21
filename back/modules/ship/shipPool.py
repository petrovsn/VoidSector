from modules.physEngine.core import lBodyPool_Singleton
from modules.utils import Command, CommandQueue, ConfigLoader
from modules.ship.systems.sm_core import BasicShipSystem


class ShipPool_Singleton:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShipPool_Singleton, cls).__new__(cls)
            cls._instance.ships = {}
            cls._instance.__current = 0
        return cls._instance

    def get(self, mark_id):
        if mark_id in self.ships:
            return self.ships[mark_id]
        return None

    def __getitem__(self, key):
        return self.ships[key]

    def __next__(self):
        return self.ships.__next__()

    def spawn(self, ShipEntity):
        self.ships[ShipEntity.mark_id] = ShipEntity

    def proceed_command(self, command: Command):
        try:
            target_id = command.get_target_id("ship")
            if target_id in self.ships:
                self.ships[target_id].proceed_command(command)
        except Exception as e:
            print(repr(e))

    def next_step(self):
        cmd_queue = CommandQueue()
        while not cmd_queue.is_empty():
            self.proceed_command(cmd_queue.get_next())
        for target_id in self.ships:
            self.ships[target_id].next_step()

    def clear(self):
        ship_list = list(self.ships.keys())
        for k in ship_list:
            self.delete(k)

    def delete(self, mark_id):
        if mark_id in self.ships:
            self.ships[mark_id].delete()
            self.ships.pop(mark_id)

    def get_ships_description(self):
        result = {}
        for shipname in self.ships:
            result[shipname] = self.ships[shipname].get_description()
        return result
