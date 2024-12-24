from modules.utils import Command, catch_exception, get_dt_ms, PerformanceCollector
import sys
import numpy as np
from modules.physEngine.quests.quest_controller import QuestPointsController
from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController
from modules.physEngine.solar_flare.solar_flar_activator import SolarFlareActivator
from modules.ship.projectile_blueprints import ProjectileConstructorController
from random import randint
from sys import getsizeof
import traceback
from datetime import datetime
from modules.utils import ConfigLoader
from modules.map_controllers.editor import MapEditor
from modules.map_controllers.loader import MapLoader
from modules.ship.ship import ShipPool_Singleton
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.triggers.handler import TriggerHandler
from modules.physEngine.triggers.collector import TriggerQueue
from modules.physEngine.active_objects import ae_Ship
from modules.physEngine.predictor import launch_new_TrajectoryPredictor_controller, TrajectoryPredictor_controller
from modules.physEngine.core import CrossDistancePool
from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.core import hBodyPool_Singleton
import multiprocessing as mp
import time
import asyncio
from random import randrange
from math import *

from enum import Enum
from modules.physEngine.plague2 import PlagueMatrix

class SectorCommandType(Enum):
    MOVE = "spawn"
    PREDICT_DEPTH = "prediction_depth"
    RESTART = "restart"
    AIM = "aim"
    LAUNCH = "launch"
    SET_PHYSICS = "set_physics"


# обертка для процесса, в котором работает сервер.
# in_queue - очередь для команд: спавн, передвижение
# контекст менеджер передается из базового процесса и создается в __main__

class EngineSector_interactor:

    output_template = {
        "observer_id": None,
        "nav_data": {
            "observer_pos": [0, 0],
            "hBodies": {},
            "lBodies": {},
        },

        "state_data": None,

        "performance": {




        }
    }

    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EngineSector_interactor, cls).__new__(cls)
        return cls._instance

    def init_server(self, mp_ctx_manager):
        if mp_ctx_manager:
            self.server = None
            self.in_queue = mp.Queue()
            self.out_sector_data = mp_ctx_manager.dict()
            self.out_sector_data["server_is_alive"] = False
            self.out_sector_data["projectile_blueprints"] = {}
            self.out_sector_data["solar_flare"] = {}
            self.out_sector_data["medicine"] = {}
            self.out_sector_data["quest_points_controller"] = {}
            self.out_sector_data["map_border"] = 1000
            self.out_sector_data["plague_matrix"] = PlagueMatrix().get()

    def get_ships_list(self):
        list_ships = []
        tmp = self.out_sector_data["lBodies"]
        for t in tmp:
            if tmp[t][0] == "ae_ship":
                list_ships.append({
                    "id": t,
                })
        return list_ships

    def get_quest_point_state(self):
        return self.out_sector_data["quest_points_controller"]

    # ============================КОМАНДЫ ДЛЯ CЕРВЕРА=============================================

    def proceed_command(self, command):
        self.in_queue.put(command)

    # =============ИСХОДЯЩИЙ ПОТОК================================================================

    def get_sector_map(self, key=None):
        data = {}
        try:
            if self.out_sector_data["server_is_alive"] == False:
                return EngineSector_interactor.output_template

            if key != None:
                data = self.out_sector_data[f"{key}_field_view"]

            else:
                data = self.out_sector_data["global_field_view"]
                data["ships_state"] = self.out_sector_data["ships_state"]
                data["stations_state"] = self.out_sector_data["stations_state"]

            data["performance"] = self.out_sector_data["performance"]
            data["systems_state"] = self.out_sector_data["systems_state"]
            data["solar_flare"] = self.out_sector_data["solar_flare"]
            data["medicine"] = self.out_sector_data["medicine"]
            data["map_border"] = self.out_sector_data["map_border"]

        except Exception as e:
            return EngineSector_interactor.output_template

        return data

    def get_med_states(self, key):
        key_t = f"{key}_field_view"
        if key_t not in self.out_sector_data:
            return {}
        data = self.out_sector_data[key_t]
        med_data = data["state_data"]["med_sm"]
        return med_data
    
    def get_plague_matrix(self):
        return self.out_sector_data['plague_matrix']

    def get_status(self):
        self.p.join(timeout=0)
        if self.p.is_alive():
            return {"EngineSector": "OK"}

    def get_blueprints(self, mark_id):
        blueprints = self.out_sector_data["projectile_blueprints"]
        if mark_id in blueprints:
            return blueprints[mark_id]
        return {}

    # =============================================================================================
    def start(self):
        self.p = mp.Process(target=self.run_instance, args=(
            self.in_queue, self.out_sector_data,))
        self.p.start()

    def run_instance(self, in_queue, out_sector_data):
        instance = EngineSector(in_queue, out_sector_data)
        instance.start()


class EngineSector:
    @catch_exception
    def __init__(self, in_queue: mp.Queue, out_sector_data):
        self.in_queue = in_queue
        self.out_sector_data = out_sector_data
        # представление
        self.hBodies = hBodyPool_Singleton()  # статичные астероиды.
        # Хранятся в синглетоне

        self.lBodies: lBodyPool_Singleton = lBodyPool_Singleton()

        # cShips for ControlledShips
        self.cShips = ShipPool_Singleton()

        self.triggerHandler = TriggerHandler()

        self.distancePool = CrossDistancePool()
        self.solarFlareActivator = SolarFlareActivator()
        self.quest_points_controller = QuestPointsController()

        self.trajectoryPredictor_controller = TrajectoryPredictor_controller()

        self.map_loader = MapLoader()
        self.map_editor = MapEditor()
        launch_new_TrajectoryPredictor_controller()
        # инициализация
        self.map_loader.load_map()
        # self.map_loader.load_ships()

        self.event_loop = asyncio.new_event_loop()
        self.event_loop.create_task(self.read_input_data())
        self.event_loop.create_task(self.update_bodies())
        self.event_loop.create_task(self.update_quest_poits_state())
        self.event_loop.create_task(self.update_ships_state())
        self.event_loop.create_task(self.update_station_state())
        self.event_loop.create_task(self.update_plague_matrix())

        self.event_loop.create_task(self.map_autosaver())
        self.global_field_view = {
            "observer_id": None,
            "nav_data": {
                "observer_id": None,
                "observer_pos": [0, 0],
                "hBodies": self.hBodies.get_bodies_description(),
                "lBodies": self.lBodies.get_bodies_description(),




            },
        }

        self.out_sector_data["global_field_view"] = self.global_field_view
        self.simulation_is_runned = True

    def start(self):
        self.event_loop.run_forever()

    # ===========================РАЗДЕЛ ДЛЯ КОРУТИН В ЦИКЛЕ ДВИЖКА СЕКТОРА============================================

    """command = {
                                "level":"ship", "server",
                                "target_id": "id",
                                "command": "aim"
                                "params": {

                                }
                }"""

    async def read_input_data(self):
        while True:
            await asyncio.sleep(0.02)
            while not self.in_queue.empty():
                command = Command(self.in_queue.get())
                self.proceed_command(command)

    def proceed_command(self, command: Command):
        try:
            if command.contains_level("predictor"):
                launch_new_TrajectoryPredictor_controller()
                # self.trajectoryPredictor_controller.proceed_command(command)
            if command.contains_level("server"):
                self.proceed_server_command(command)
            elif command.contains_level("ship"):
                self.cShips.proceed_command(command)
            elif command.contains_level("map_editor"):
                self.map_editor.proceed_command(command)
            elif command.contains_level("map_loader"):
                self.map_loader.proceed_command(command)
                self.out_sector_data["map_border"] = self.hBodies.get_max_distance(
                )
            elif command.contains_level("solar_flare"):
                self.solarFlareActivator.proceed_command(command)
            elif command.contains_level("config_loader"):
                ConfigLoader().proceed_command(command)

            elif command.contains_level("hBodiesPool"):
                self.hBodies.proceed_command(command)
            elif command.contains_level("medicine"):
                self.medicineController.proceed_command(command)
            elif command.contains_level("qp_controller"):
                QuestPointsController().proceed_command(command)

            elif command.contains_level("station_controller"):
                self.proceed_station_command(command)

        except Exception as e:
            print("SectorServer Command Execution", repr(e), )
            traceback.print_exc(file=sys.stdout)

    def proceed_station_command(self, command: Command):
        try:
            action = command.get_action()
            params = command.get_params()
            target = params["target"]
            if action == "activate_station_defence":
                if target in self.lBodies.bodies:
                    self.lBodies[target].activate_station_defence()
            if action == "destroy_station":
                if target in self.lBodies.bodies:
                    self.lBodies[target].self_destroy()
            if action == "set_map_border":
                self.out_sector_data["map_border"] = params["value"]

        except Exception as e:
            pass#print("SectorServer", repr(e))

    def proceed_server_command(self, command: Command):
        try:
            action = command.get_action()
            params = command.get_params()
            if action == SectorCommandType.SET_PHYSICS:
                WorldPhysConstants().set_Gconst(command["Gconst"])
                WorldPhysConstants().set_timestep(command["timestep"])
                TrajectoryPredictor_controller().set_physics(command)
            if action == "restart":
                self.map_loader.load_map()
                self.map_loader.load_ships()
            if action == "reload_predictors":
                TrajectoryPredictor_controller().update_hbodies_location()
            if action == "pause":
                self.simulation_is_runned = False
            if action == "run":
                self.simulation_is_runned = True

        except Exception as e:
            pass#print("SectorServer", repr(e))

    # ==========ФИЗИКА===============================================================================================

    async def update_bodies(self):
        t1 = datetime.now()
        desiredFPS = 30
        time_interval = 1/desiredFPS
        self.out_sector_data["server_is_alive"] = True
        while True:
            try:
                dt = datetime.now() - t1
                t1 = datetime.now()

                if self.simulation_is_runned:
                    tmp_t0 = datetime.now()
                    self.distancePool.update()
                    tmp_t1 = datetime.now()
                    self.lBodies.iter_loop()  # обработка движения
                    tmp_t2 = datetime.now()
                    self.hBodies.iter_loop()  # обработка активности станций
                    tmp_t3 = datetime.now()
                    # обработка активированных триггеров
                    self.triggerHandler.proceed_triggers_list()
                    tmp_t4 = datetime.now()
                    self.cShips.next_step()  # шаг расчёта для систем кораблей
                    tmp_t5 = datetime.now()
                    self.solarFlareActivator.step()

                # обновления админского поля зрения
                tmp_t6 = datetime.now()
                self.global_field_view["nav_data"]["hBodies"] = self.hBodies.get_bodies_description(
                )
                tmp_t7 = datetime.now()
                self.global_field_view["nav_data"]["lBodies"] = self.lBodies.get_bodies_description(
                )
                self.global_field_view["nav_data"]["visible_ships"] = EntityIDGroupsController(
                ).get("id_labels_detectable")
                tmp_t8 = datetime.now()
                self.out_sector_data["global_field_view"] = self.global_field_view

                # обновления поля зрения для каждого корабля
                tmp_t9 = datetime.now()

                for ae_ship_id in self.cShips.ships:
                    field_view = self.cShips.ships[ae_ship_id].get_viewfield()
                    self.out_sector_data[f"{ae_ship_id}_field_view"] = field_view
                tmp_t10 = datetime.now()

                # оценка производительности
                dt = datetime.now() - t1
                calculation_time = dt.microseconds/1000000
                delay_time = max(0, time_interval-calculation_time)
                # self.out_sector_data["time2processFrame"] = dt.microseconds/1000

                performance_p1 = {
                    "predictors_step_time": TrajectoryPredictor_controller().get_predictor_performance_statistics(),
                    "real_calculation_time": calculation_time,
                    "free_awaiting_time": time_interval-calculation_time,
                    "frame_size[bytes]": get_size(self.global_field_view),
                    "distancePool_time": get_dt_ms(tmp_t0, tmp_t1),
                    "lbodies_time": get_dt_ms(tmp_t1, tmp_t2),
                    "hbodies_time": get_dt_ms(tmp_t2, tmp_t3),
                    "trigger_time": get_dt_ms(tmp_t3, tmp_t4),
                    "cships_time": get_dt_ms(tmp_t4, tmp_t5),
                    # "admin_view": get_dt_ms(tmp_t6, tmp_t8),
                    "ships_view": get_dt_ms(tmp_t9, tmp_t10),




                }

                performanse_p2 = PerformanceCollector().get()

                performanse = dict(performance_p1, **performanse_p2)

                self.out_sector_data["performance"] = performanse

                PerformanceCollector().clear()

                self.out_sector_data["systems_state"] = {
                    "map_locked": str(not self.hBodies.realtime_update)
                }
                self.out_sector_data["solar_flare"] = self.solarFlareActivator.get_status(
                )
                self.out_sector_data["projectile_blueprints"] = ProjectileConstructorController(
                ).blueprints

                self.map_border_check_trigger()
                WorldPhysConstants().next_step()

                await asyncio.sleep(delay_time)
            except Exception as e:
                #print(e)
                pass
                print(traceback.format_exc())

    def map_border_check_trigger(self):
        for ship_id in self.cShips.ships:
            pos = self.lBodies[ship_id].get_position_np()
            distance2ship = np.linalg.norm(pos)
            if distance2ship > self.out_sector_data["map_border"]:
                new_speed = -pos/distance2ship
                self.lBodies[ship_id].set_velocity(new_speed)

    # ===============================================================================================================

    async def update_ships_state(self):
        while True:
            await asyncio.sleep(1)
            ships_stats = {}
            for ae_ship_id in self.cShips.ships:
                ships_stats[ae_ship_id] = self.cShips.ships[ae_ship_id].get_short_description(
                )
            self.out_sector_data["ships_state"] = ships_stats

    async def update_station_state(self):
        while True:
            try:
                await asyncio.sleep(1)
                stations_stats = {}
                for station_idx in EntityIDGroupsController().get("is_station"):
                    stations_stats[station_idx] = self.lBodies[station_idx].get_short_description(
                    )
                self.out_sector_data["stations_state"] = stations_stats
            except Exception as e:
                pass#print("update_station_state", repr(e))

    async def update_quest_poits_state(self):
        while True:
            await asyncio.sleep(1)
            self.out_sector_data["quest_points_controller"] = self.quest_points_controller.get_state(
            )

    async def map_autosaver(self):
        cnter = 0
        while True:
            await asyncio.sleep(60*1)
            self.map_editor.save_main_ship(f"auto_save_#{cnter}")
            self.map_editor.save_main_ship(f"auto_save_latest")
            cnter = cnter+1
            if cnter > 9:
                cnter = 0


    #=================================================================================================================
                
    async def update_plague_matrix(self):
        while True:
            actual_matrix = PlagueMatrix().get()
            self.out_sector_data["plague_matrix"] = actual_matrix
            await asyncio.sleep(1)

def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size
