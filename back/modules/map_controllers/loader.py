
# from modules.physEngine.core import hBodyPool_Singleton
from modules.physEngine.core import hBody, lBodyPool_Singleton, hBodyPool_Singleton
from modules.physEngine.hb_entities import ResourceAsteroid, WormHole
from modules.physEngine.interactable_objects.container import intact_Container, ShipDebris
from modules.physEngine.active_objects import QuantumShadow, SpaceStation
from modules.physEngine.hb_entities import ResourceAsteroid, WormHole
from modules.physEngine.interactable_objects.container import intact_Container, ShipDebris, SpaceStationDebris
from modules.ship.ship import Ship, NPC_Ship
from modules.ship.shipPool import ShipPool_Singleton
from random import randint
from modules.utils import ConfigLoader, Command
from modules.physEngine.predictor import TrajectoryPredictor_controller
# from modules.physEngine.core import lBodyPool_Singleton
import json
from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController
import traceback
from modules.physEngine.zones.meteors_zone import MeteorsCloud
from modules.physEngine.triggers.handler import TriggerHandler
from modules.physEngine.projectiles.mine_master import Mine_type1, Mine_type2
from modules.physEngine.solar_flare.solar_flar_activator import SolarFlareActivator


class MapLoader:
    def __init__(self):
        self.hBodies = hBodyPool_Singleton()
        self.cShips = ShipPool_Singleton()
        self.lBodies = lBodyPool_Singleton()
        self.grid_step = ConfigLoader().get("world.map_step", float)

    def load_interactable(self):
        conteiners_num = 10
        spawn_radius = self.grid_step*3
        for i in range(0):
            pos_x = randint(-spawn_radius, spawn_radius)
            pos_y = randint(-spawn_radius, spawn_radius)
            self.lBodies.add(intact_Container(pos_x, pos_y))

    def proceed_command(self, command: Command):
        action = command.get_action()
        match action:
            case 'load_map': self.load_map_with_name(command.get_params()["map_name"])
            case 'load_main_ship': self.load_main_ship_screen_with_name(command.get_params()["screen_name"])

    def load_main_ship_screen_with_name(self, screen_name):
        main_ship_id = ConfigLoader().get_main_ship_id()
        description = json.load(open(f"ship_screens/{screen_name}", 'r'))
        if main_ship_id in self.cShips.ships:
            self.cShips.ships[main_ship_id].put_description(description)

    def load_map_with_name(self, map_name):



        TriggerHandler().clear_trigger_list()
        self.cShips.clear()
        TriggerHandler().proceed_triggers_list()
        self.hBodies.clear()
        self.lBodies.clear()


        EntityIDGroupsController().clear()

        # Gconst = ConfigLoader().get("world.gravity_constant",float)
        # WorldPhysConstants().set_Gconst(Gconst)
        # TrajectoryPredictor_controller().update_physics()

        try:
            map_data = json.load(open(f"maps/{map_name}"))
            for hbody_id in map_data["hBodies"]:
                hbody_object = self.get_hbody_from_description(
                    map_data["hBodies"][hbody_id])
                if hbody_object:
                    self.hBodies.add(hbody_object)

            for lbody_id in map_data["lBodies"]:
                is_ship, lbody_object = self.get_lbody_from_description(
                    lbody_id, map_data["lBodies"][lbody_id])
                if lbody_object:
                    self.lBodies.add(lbody_object)

            if "cShips" in map_data:
                for ship_id in map_data["cShips"]:
                    ship_obj = self.get_ship_from_description(
                        ship_id, map_data["cShips"][ship_id])
                    if ship_obj:
                        self.cShips.spawn(ship_obj)
            if "SolarFlareActivator" in map_data:
                SolarFlareActivator().put_description(
                    map_data["SolarFlareActivator"])

        except Exception as e:
            pass
            print(traceback.format_exc())
            self.hBodies.clear()
            self.cShips.clear()
            self.lBodies.clear()
        TriggerHandler().clear_trigger_list()
        TrajectoryPredictor_controller().update_hbodies_location()

    def get_hbody_from_description(self, descr):
        try:
            match descr["type"]:
                case "hBody":
                    object = hBody(0, 0)
                case "ResourceAsteroid":
                    object = ResourceAsteroid(0, 0)
                case 'WormHole':
                    object = WormHole(0, 0)

            object.put_description(descr, forced=True)
            return object
        except Exception as e:
            pass  # print("map loader", repr(e))
        return None

    def get_ship_from_description(self, mark_id, descr):
        result = None
        match descr["type"]:
            case "Ship":
                result = Ship(900000, 900000, mark_id=mark_id)

            case "NPC_Ship":
                result = NPC_Ship(900000, 900000, mark_id=mark_id)

        if result:
            result.put_description(descr)
        return result

    def get_lbody_from_description(self, mark_id, descr):
        pos_x = descr["pos"][0]
        pos_y = descr["pos"][1]
        is_ship = False  # controllable ship
        result = None
        match descr["type"]:
            # case "ae_Ship":
            #    result = Ship(pos_x,pos_y, mark_id=mark_id)
            #    is_ship = True
            # case "NPC_Ship":
            #    result = NPC_Ship(pos_x,pos_y, mark_id=mark_id)
            #    is_ship = True
            case 'ShipDebris':
                result = ShipDebris(pos_x, pos_y, mark_id)

            case 'MeteorsCloud':
                result = MeteorsCloud(pos_x, pos_y)

            case 'QuantumShadow':
                result = QuantumShadow(pos_x, pos_y)

            case 'SpaceStation':
                result = SpaceStation(pos_x, pos_y, mark_id)

            case 'WormHole':
                result = WormHole(pos_x, pos_y)

            case 'SpaceStationDebris':
                result = SpaceStationDebris(pos_x, pos_y, mark_id)

            case 'Mine_type1':
                result = Mine_type1(pos_x, pos_y)

            case 'Mine_type2':
                result = Mine_type2(pos_x, pos_y)

        if result:
            result.put_description(descr, True)

        return is_ship, result

        ship1 = Ship(pos_x, pos_y, mark_id=mark_id)
        return ship1

    def load_map(self):
        # self.load_map_with_name("triangle3.json")
        """self.hBodies.clear()

        count = randint(1,4)

        scale = 1
        area_radius = int(scale*self.grid_step)
        for i in range(count):
                        pos_x = randint(-area_radius,area_radius)
                        pos_y = randint(-area_radius,area_radius)
                        self.hBodies.add(hBody(pos_x, pos_y,200))"""

        """for pos_x, pos_y, gr in [(-2*self.grid_step,0,self.grid_step),
                                                                                                                                                (2*self.grid_step,0,self.grid_step),
                                                                                                                                                (0,0,self.grid_step)]:
                                                self.hBodies.add(ResourceAsteroid(pos_x, pos_y,gr))

                                for pos_x, pos_y, gr in [
                                                                                                                                                (-self.grid_step,-0.866*2*self.grid_step,self.grid_step),
                                                                                                                                                (self.grid_step,-0.866*2*self.grid_step,self.grid_step),
                                                                                                                                                (-self.grid_step,0.866*2*self.grid_step,self.grid_step),
                                                                                                                                                (self.grid_step, 0.866*2*self.grid_step,self.grid_step),
                                                                                                                                                ]:
                                                self.hBodies.add(hBody(pos_x, pos_y,gr))"""
        # TrajectoryPredictor_controller().update_hbodies_location()

    def load_ships(self):
        ConfigLoader().update()
        self.cShips.clear()
        self.lBodies.clear()
