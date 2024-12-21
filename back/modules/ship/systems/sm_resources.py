from modules.ship.systems.sm_damage import CrewSystem
from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.projectiles.projectile_selector import ProjectileSelector
from modules.utils import Command
from modules.physEngine.projectiles.projectiles_core import pjtl_Constructed
from modules.ship.systems.sm_core import BasicShipSystem
from modules.utils import Command
from modules.utils import Command, CommandQueue, ConfigLoader
from modules.ship.systems.sm_core import GlobalShipSystemController

from queue import Queue

from modules.ship.projectile_blueprints import ProjectileConstructorController
import itertools


class Item:
    def __init__(self):
        self.volume = 0
        self.cost = 0


class Stockpile:
    def __init__(self):
        self.storage = {}
        self.capacity = 10001
        self.occupied = 0
        self.items_volume = {}
        self.items_cost = {}

    def set_capacity(self, value):
        if value < self.occupied:
            self.throw_out_of_volume(self.occupied-value)
        self.capacity = value

    def get_description(self):
        return {
            "storage": self.storage,
            "capacity": self.capacity,
            "occupied": self.occupied,
            "items_volume": self.items_volume,
            "items_cost": self.items_cost,
        }

    def put_description(self, descr):
        self.storage = descr["storage"]
        self.capacity = descr["capacity"]
        self.occupied = descr["occupied"]
        self.items_volume = descr["items_volume"]
        self.items_cost = descr["items_cost"]

    def throw_out_of_volume(self, value):
        to_out = {item: 0 for item in self.items_volume}
        tmp_val = 0

        items_it = itertools.cycle(self.items_volume)

        while tmp_val < value:
            item = next(items_it)
            tmp_val = tmp_val+self.items_volume[item]
            to_out[item] = to_out[item]+1

        for item in to_out:
            self.take_item(item, to_out[item])

    def can_be_placed(self, item_name, item_amount):
        return self.capacity - self.occupied >= self.items_volume[item_name]*item_amount

    def init_item(self, item_name, item_volume, item_cost):
        self.storage[item_name] = 0
        self.items_volume[item_name] = item_volume
        self.items_cost[item_name] = item_cost

    def get_volume_and_cost(self, item_name):
        return self.items_volume[item_name], self.items_cost[item_name]

    def add_item(self, item_name, item_amount):
        if item_name not in self.storage:
            return False
        if not self.can_be_placed(item_name, item_amount):
            free_volume = self.capacity - self.occupied
            item_amount = free_volume//self.items_volume[item_name]
            if item_amount == 0:
                return False

        item_volume = self.items_volume[item_name]*item_amount
        self.storage[item_name] = self.storage[item_name]+item_amount
        self.occupied = self.occupied + item_volume
        return True

    def take_item(self, item_name, item_amount):
        if item_name not in self.storage:
            return False
        if self.storage[item_name] < item_amount:
            return False
        self.storage[item_name] = self.storage[item_name]-item_amount
        self.occupied = self.occupied - \
            item_amount*self.items_volume[item_name]
        return True

    def del_item(self, item_name):
        amount = self.storage[item_name]
        self.take_item(item_name, amount)
        self.storage.pop(item_name)
        self.items_volume.pop(item_name)
        self.items_cost.pop(item_name)

    def get_status(self):
        return {
            "storage": self.storage,
            "capacity": self.capacity,
            "self.occupied": self.occupied
        }

    def contains_item(self, item_name):
        try:
            return self.storage[item_name] > 0
        except Exception as e:
            pass  # print("Stockpile.contains_item",repr(e))
        return False

    def get_str_repr(self):
        result = []
        for item_name in self.storage:
            result.append(item_name+f" [{self.storage[item_name]}]")
        return result


class ProductionTask:
    def __init__(self, item_name, production_volume):
        self.item_name = item_name
        self.production_volume = production_volume
        self.producted = 0
        self.complete = False

    def step(self, production_step):
        self.producted = min(self.producted+production_step,
                             self.production_volume)
        self.complete = self.producted == self.production_volume

    def get_progress(self):
        return self.producted/self.production_volume


class ProductionQueue:
    def __init__(self):
        self.queue = []

    def add(self, item_name):
        if self.queue != []:
            if self.queue[-1][0] == item_name:
                self.queue[-1][1] = self.queue[-1][1]+1
                return

        self.queue.append([item_name, 1])

    def is_empty(self):
        return self.queue == []

    def get_item_by_idx(self, item_idx):
        item_name = self.queue[item_idx][0]
        if item_idx == 0:
            if self.queue[item_idx][1] == 1:
                self.queue = self.queue[1:]
                return item_name
        self.queue[item_idx][1] = self.queue[item_idx][1]-1

        if self.queue[item_idx][1] == 0:
            self.queue.pop(item_idx)
        return item_name

    def get_next_item(self):
        if self.queue == []:
            return None
        return self.get_item_by_idx(0)

    def remove(self, item_name, item_idx):
        item_idx = int(item_idx)
        if self.queue[int(item_idx)][0] == item_name:
            self.get_item_by_idx(item_idx)

    def clear(self):
        self.queue = []


class ResourcesSystem(BasicShipSystem):
    def __init__(self, mark_id, NPC=False):
        super().__init__(mark_id, "resources_sm")
        self.capacity_levels = ConfigLoader().get("sm_resources.capacity_levels", list)

        self.NPC = NPC
        self.stockpile_raw = Stockpile()
        self.stockpile_raw.init_item("metal", 1, 1)

        self.stockpile_items = Stockpile()

        self.projectile_constructor = ProjectileConstructorController()
        self.projectile_constructor.initiate_ship_blueprints(self.mark_id, NPC)
        self.update_blueprints()

        self.production_queue = ProductionQueue()
        self.production_step = WorldPhysConstants().get_onetick_step(20, 5)
        self.production_task: ProductionTask = None
        self._crew_sm: CrewSystem = None

        # self.stockpile_items.set_capacity(self.capacity_levels[self.upgrade_level])
        # self.stockpile_raw.set_capacity(self.capacity_levels[self.upgrade_level])
        # self.stockpile_raw.add_item("metal",self.capacity_levels[self.upgrade_level])

    
        self.stockpile_raw.add_item("metal", 10000)

    def get_description(self):
        result = super().get_description()
        result['materials_row'] = self.stockpile_raw.get_description()
        result['stockpile_items'] = self.stockpile_items.get_description()
        result['projectile_constructor'] = self.projectile_constructor.get_description(
            self.mark_id)
        return result

    def put_description(self, descr):
        super().put_description(descr)
        self.stockpile_raw.put_description(descr['materials_row'])
        self.stockpile_items.put_description(descr['stockpile_items'])
        self.projectile_constructor.put_description(
            self.mark_id, descr['projectile_constructor'])

    @property
    def crew_sm(self):
        if not self._crew_sm:
            self.crew_sm = GlobalShipSystemController().get(self.mark_id, "crew_sm")
        return self._crew_sm

    @crew_sm.setter
    def crew_sm(self, value):
        self._crew_sm = value

    def update_blueprints(self, bp_name=None):
        bp_list = self.projectile_constructor.get_blueprints_list(self.mark_id)
        if bp_name:
            bp_list = [bp_name]
        for pjtl_name in bp_list:
            cost = self.projectile_constructor.get_cost(
                self.mark_id, pjtl_name)
            details = self.projectile_constructor.get_volume(
                self.mark_id, pjtl_name)
            self.stockpile_items.init_item(pjtl_name, details, cost)

            #if not self.NPC:
            if len(bp_list) > 1:
                self.stockpile_items.add_item(pjtl_name, 30)
            #else:
            #    self.stockpile_items.add_item(pjtl_name, 30)

    def next_step(self):
        if self.production_task:
            crew_acc = self.crew_sm.get_crew_acceleration_in_system(
                "engine_sm") if self.crew_sm else 0
            self.production_task.step(
                self.production_step*self.power*(1+crew_acc))
            if self.production_task.complete:
                self.stockpile_items.add_item(
                    self.production_task.item_name, 1)
                self.trigger_launcher_update()
                self.production_task = None

        else:
            item_name = self.production_queue.get_next_item()
            if item_name:
                if (self.stockpile_items.can_be_placed(item_name, 1)):
                    item_volume, item_cost = self.stockpile_items.get_volume_and_cost(
                        item_name)
                    if (self.stockpile_raw.storage["metal"] >= item_cost):
                        result = self.spend_resource("metal", item_cost)
                        if result:
                            self.production_task = ProductionTask(
                                item_name, item_volume)

    def get_available_projectiles(self):
        items_list = self.stockpile_items.get_str_repr()
        return items_list

    def get_blueprint(self, blueprint_name):
        return self.projectile_constructor.get_blueprint(self.mark_id, blueprint_name)

    def get_status(self):
        status = super().get_status()
        status["stockpile_raw"] = self.stockpile_raw.storage
        status["stockpile_raw_capacity"] = self.stockpile_raw.capacity
        status["stockpile_raw_occupied"] = self.stockpile_raw.occupied

        status["stockpile_items"] = self.stockpile_items.storage
        status["stockpile_items_capacity"] = self.stockpile_items.capacity
        status["stockpile_items_occupied"] = self.stockpile_items.occupied

        status["items_volume"] = self.stockpile_items.items_volume
        status['items_cost'] = self.stockpile_items.items_cost
        status["production_task"] = ""
        status["production_progress"] = 0
        status["production_queue"] = self.production_queue.queue
        if self.production_task:
            status["production_task"] = self.production_task.item_name
            status["production_progress"] = self.production_task.get_progress()
        return status

    def proceed_command(self, command: Command):
        super().proceed_command(command)
        action = command.get_action()
        params = command.get_params()
        match action:
            case "change_amount":
                res_name = params["resource_name"]
                res_amount = params["resource_amount"]
                self.add_resource(res_name, res_amount)

            case "produce_item":
                item_name = params["item_name"]
                items_in_producing_pack = ConfigLoader().get("sm_resources.items_in_producing_pack", int)
                for i in range(items_in_producing_pack):
                    self.production_queue.add(item_name)

            case "remove_item_from_production_queue":
                item_name = params["item_name"]
                item_idx = params["item_idx"]
                self.production_queue.remove(item_name, item_idx)

            case 'cancel_item_production':
                self.production_task = ""
                self.production_progress = 0

            case "clear_production":
                self.production_queue.clear()

            case "save_projectile_blueprint":
                bp_name = command.get_params()["bp_name"]
                if bp_name:
                    bp_content = command.get_params()["bp_content"]
                    self.save_projectile_blueprint(bp_name, bp_content)

            case "delete_projectile_blueprint":
                bp_name = command.get_params()["bp_name"]
                if bp_name:
                    self.delete_projectile_blueprint(bp_name)

    def delete_projectile_blueprint(self, bp_name):
        available_bps = self.projectile_constructor.get_blueprints_list(
            self.mark_id)
        if bp_name not in available_bps:
            return
        volume, cost = self.stockpile_items.get_volume_and_cost(bp_name)
        current_amount = self.stockpile_items.storage[bp_name]
        metal_cost = current_amount*cost*0.5
        self.stockpile_items.del_item(bp_name)
        self.stockpile_raw.add_item("metal", metal_cost)
        self.trigger_launcher_update()

    def save_projectile_blueprint(self, bp_name, bp_content):
        available_bps = self.projectile_constructor.get_blueprints_list(
            self.mark_id)
        if bp_name in available_bps:
            volume, cost = self.stockpile_items.get_volume_and_cost(bp_name)
            current_amount = self.stockpile_items.storage[bp_name]
            metal_cost = current_amount*cost*0.5
            self.stockpile_items.del_item(bp_name)
            self.stockpile_raw.add_item("metal", metal_cost)
        self.projectile_constructor.append_blueprint(
            self.mark_id, bp_name, bp_content)
        self.update_blueprints(bp_name)
        self.trigger_launcher_update()

    def trigger_launcher_update(self):
        GlobalShipSystemController().get(
            self.mark_id, "launcher_sm").update_available_projectile()

    def spend_resource(self, resource_name, resource_amount):
        stockpile: Stockpile = self.get_appropriate_stockpile(resource_name)
        result = stockpile.take_item(resource_name, resource_amount)
        return result

    def add_resource(self, resource_name, resource_amount):
        stockpile: Stockpile = self.get_appropriate_stockpile(resource_name)
        result = stockpile.add_item(resource_name, resource_amount)
        self.get_system("launcher_sm").update_available_projectile()
        return result

    def get_appropriate_stockpile(self, resource_name):
        if resource_name in self.stockpile_items.storage:
            return self.stockpile_items
        elif resource_name in self.stockpile_raw.storage:
            return self.stockpile_raw
        else:
            assert False, "no appropriate storage"

    def upgrade(self):
        super().upgrade()
        
        self.stockpile_items.set_capacity(
            self.capacity_levels[self.upgrade_level])
        self.stockpile_raw.set_capacity(
            self.capacity_levels[self.upgrade_level])
        
        if self.NPC:
            self.add_resource("metal",1000000)
        else:
            self.get_system("med_sm").upgrade()

        

    def downgrade(self):
        super().downgrade()
        
        self.stockpile_items.set_capacity(
            self.capacity_levels[self.upgrade_level])
        self.stockpile_raw.set_capacity(
            self.capacity_levels[self.upgrade_level])
        
        if self.NPC:
            self.add_resource("metal",1000000)
        else:
            self.get_system("med_sm").downgrade()
