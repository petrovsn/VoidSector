
from modules.ship.shipPool import ShipPool_Singleton
from modules.physEngine.core import lBodyPool_Singleton
from modules.utils import Command, CommandQueue, ConfigLoader, get_dt_ms, PerformanceCollector
from modules.ship.systems.sm_core import BasicShipSystem
from modules.ship.systems.sm_core import GlobalShipSystemController
from modules.ship.systems.sm_launcher import LauncherSystem
from modules.ship.systems.sm_engine import EngineSystem, NPC_Kraken_EngineSystem
from modules.ship.systems.sm_energy import EnergySystem
from modules.ship.systems.sm_radar import RadarSystem
from modules.ship.systems.sm_resources import ResourcesSystem
from modules.ship.systems.sm_damage import DamageSystem, CrewSystem, NPC_DamageSystem
from modules.ship.systems.sm_RnD import ResearchAndDevSystem
from modules.ship.systems.sm_interact import InteractionSystem
from modules.ship.systems.sm_medicine import MedicineSystem
from datetime import datetime


class CapMarksController:
    def __init__(self):
        self.marks = {}
        self.selected_char = None
        for a in ["A", "B", "C", "D", "E"]:
            self.marks[a] = {
                "position": [0, 0],
                "active": False,
                "selected": False
            }

    def get_description(self):
        return self.marks

    def put_description(self, descr):
        self.marks = descr

    def proceed_command(self, cmd: Command):
        action = cmd.get_action()
        params = cmd.get_params()
        match action:
            case "make_point":
                if self.selected_char not in self.marks:
                    return
                self.marks[self.selected_char] = {
                    "position": params["position"],
                    "active": True
                }
                self.selected_char = None
            case "deactivate_point":
                if params["char"] not in self.marks:
                    return
                self.marks[params["char"]]["active"] = False

            case "select_point":
                if params["char"] not in self.marks:
                    return
                for a in self.marks:
                    self.marks[a]["selected"] = False
                self.selected_char = params["char"]
                self.marks[self.selected_char]["selected"] = True

    def get_marks(self):
        return self.marks


class Ship:
    def __init__(self, pos_x, pos_y, mark_id=None):
        self.mark_id = mark_id if mark_id else str(id(self))

        GlobalShipSystemController().add(self.mark_id, "engine_sm",
                                         EngineSystem(pos_x, pos_y, mark_id))
        GlobalShipSystemController().add(
            self.mark_id, "launcher_sm", LauncherSystem(mark_id))
        GlobalShipSystemController().add(
            self.mark_id, "resources_sm", ResourcesSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "crew_sm", CrewSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "damage_sm", DamageSystem(mark_id))
        GlobalShipSystemController().add(
            self.mark_id, "interact_sm", InteractionSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "radar_sm", RadarSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "energy_sm", EnergySystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "RnD_sm",
                                         ResearchAndDevSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "med_sm", MedicineSystem(mark_id))

        self.systems_state = GlobalShipSystemController().get_status(self.mark_id)
        self.get_system("RnD_sm").upgrade_to_config_state()
        self.get_system("launcher_sm").update_available_projectile()
        self.get_system("energy_sm").set_max_power()
        self.get_system("radar_sm").update_scanrange()
        self.cap_marks = CapMarksController()

    def get_system(self, system_name):
        return GlobalShipSystemController().get(self.mark_id, system_name)

    def get_viewfield(self):
        data = {}
        data["state_data"] = self.systems_state
        data["observer_id"] = self.mark_id
        data["nav_data"] = self.get_system("radar_sm").get_nav_data()
        data["cap_marks"] = self.cap_marks.get_marks()
        return data

    def get_short_description(self):
        data = {
            "hp": self.get_system("damage_sm").get_short_description(),
            "RnD": self.get_system("RnD_sm").get_short_description(),
            "pos": self.get_system("engine_sm").get_position(),
        }
        return data

    def gain_resource(self, resource_name, resource_amount):
        self.get_system("resources_sm").add_resource(
            resource_name, resource_amount)

    def proceed_command(self, command: Command):
        if command.contains_level("cap_marks"):
            self.cap_marks.proceed_command(command)
            return
        res = GlobalShipSystemController().proceed_command(self.mark_id, command)
        if not res:
            self.proceed_related_command(command)

    def proceed_related_command(self, command: Command):
        action = command.get_action()
        prams = command.get_params()
        match action:
            case "destroy": self.destroy()

    def get_state(self):
        pass

    def delete(self):
        launcher = self.get_system("launcher_sm")
        if launcher: launcher.unload()
        GlobalShipSystemController().delete(self.mark_id)

    def set_level(self, ship_level):
        self.get_system("RnD_sm").set_ship_level(ship_level)

    def takes_damage(self, damage_value, damage_type, damage_source=None):
        self.get_system("damage_sm").takes_damage(
            damage_value, damage_type, damage_source)

    def next_step(self):
        tmp_t1 = datetime.now()
        GlobalShipSystemController().next_step(self.mark_id)
        tmp_t2 = datetime.now()
        self.systems_state = GlobalShipSystemController().get_status(self.mark_id)
        tmp_t3 = datetime.now()
        PerformanceCollector().add("Ship.iter_loop.next_step", get_dt_ms(tmp_t1, tmp_t2))
        PerformanceCollector().add("Ship.iter_loop.get_status", get_dt_ms(tmp_t2, tmp_t3))

    def get_description(self):
        result = {"mark_id": self.mark_id,
                  "type": self.__class__.__name__, "systems": {}}
        system_list = GlobalShipSystemController().get_systems_list(self.mark_id)
        for system_name in system_list:
            result["systems"][system_name] = self.get_system(
                system_name).get_description()

        result["capmarks"] = self.cap_marks.get_description()
        return result

    def put_description(self, descr, forced=False):
        system_list = GlobalShipSystemController().get_systems_list(self.mark_id)
        for system_name in system_list:
            try:
                self.get_system(system_name).put_description(
                    descr["systems"][system_name])
            except Exception as e:
                pass
        try:
            self.cap_marks.put_description(descr["capmarks"])
        except Exception as e:
            pass


NPC_Ships_levels = {
    "Otto": 3,
    "Rattling": 1,
    "Venom": 2,
    "Vixen": 2,
    "Punisher": 2,
    "Galileo": 1
}


class NPC_Ship(Ship):
    def __init__(self, pos_x, pos_y, mark_id=None):
        
        self.mark_id = mark_id if mark_id else str(id(self))
        GlobalShipSystemController().add(self.mark_id, "engine_sm", EngineSystem(
            pos_x, pos_y, mark_id, ship_subtype="NPC_Ship"))
        GlobalShipSystemController().add(
            self.mark_id, "launcher_sm", LauncherSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "resources_sm",
                                         ResourcesSystem(mark_id, True))
        GlobalShipSystemController().add(
            self.mark_id, "damage_sm", NPC_DamageSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "radar_sm", RadarSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "energy_sm",
                                         EnergySystem(mark_id, NPC=True))
        GlobalShipSystemController().add(self.mark_id, "RnD_sm",
                                         ResearchAndDevSystem(mark_id, True))
        self.systems_state = GlobalShipSystemController().get_status(self.mark_id)
        self.get_system("launcher_sm").update_available_projectile()
        self.get_system("radar_sm").update_scanrange()
        self.get_system("RnD_sm").upgrade_to_config_state()
        self.get_system("energy_sm").set_NpcEnergy()
        if self.mark_id in NPC_Ships_levels:
            self.set_level(NPC_Ships_levels[self.mark_id])
        else:
            self.set_level(2)
        self.cap_marks = CapMarksController()

    def get_viewfield(self):
        data = {}
        data["state_data"] = self.systems_state
        data["observer_id"] = self.mark_id
        data["nav_data"] = self.get_system("radar_sm").get_nav_data()
        return data


class NPC_Kraken(Ship):
    def __init__(self, pos_x, pos_y, mark_id=None):
        self.mark_id = mark_id if mark_id else str(id(self))
        GlobalShipSystemController().add(self.mark_id, "engine_sm",
                                         NPC_Kraken_EngineSystem(pos_x, pos_y, mark_id, ship_subtype="Kraken"))
        GlobalShipSystemController().add(
            self.mark_id, "damage_sm", NPC_DamageSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "radar_sm", RadarSystem(mark_id))
        GlobalShipSystemController().add(self.mark_id, "energy_sm",
                                         EnergySystem(mark_id, NPC=True))
        GlobalShipSystemController().add(self.mark_id, "RnD_sm",
                                         ResearchAndDevSystem(mark_id))
        self.systems_state = GlobalShipSystemController().get_status(self.mark_id)
        self.get_system("radar_sm").update_scanrange()
        # self.get_system("RnD_sm").upgrade_to_config_state()

    def get_viewfield(self):
        data = {}
        data["state_data"] = self.systems_state
        data["observer_id"] = self.mark_id
        data["nav_data"] = self.get_system("radar_sm").get_nav_data()
        return data
