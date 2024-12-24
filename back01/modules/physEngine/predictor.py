import traceback
from datetime import datetime, timedelta
import numpy as np
import multiprocessing as mp
from modules.physEngine.core import hBodyPool_Singleton
from modules.physEngine.core import TrajectoryCalculator, hBody
from modules.physEngine.world_constants import WorldPhysConstants
from modules.utils import ConfigLoader, Command
import time
import os


class TrajectoryPredictor_controller:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(
                TrajectoryPredictor_controller, cls).__new__(cls)
            try:
                ctx_manager = mp.Manager()
                cls._instance.shared_dict = ctx_manager.dict()
                cls._instance.predictors = {}
                cls._instance.control_queues = {}
                cls._instance.task_counter = {}
                cls._instance.hBodies = hBodyPool_Singleton()
                cls._instance.predictors_performance = []
                cls._instance.predictors_performance_length = 300
            except Exception as e:
                pass

        return cls._instance

    def is_online(self):
        return self.predictors != {}

    def add_predictor_performance_timestamp(self, timestamp):
        self.predictors_performance.append(timestamp)
        if len(self.predictors_performance) > self.predictors_performance_length:
            self.predictors_performance = self.predictors_performance[-self.predictors_performance_length:]

    def get_predictor_performance_statistics(self):
        if self.predictors_performance == []:
            return 0.0
        return np.mean(self.predictors_performance)

    def get_free_predictor(self):
        predictor_key = min(self.task_counter, key=self.task_counter.get)
        return predictor_key

    def set_physics(self, params):
        for key in self.control_queues:
            self.control_queues[key].put({"type": "set_physics",
                                          "Gconst": params["Gconst"],
                                          "timestep": params["timestep"]})

    def update_physics(self):
        for key in self.control_queues:
            self.control_queues[key].put({"type": "set_physics",
                                          "Gconst": WorldPhysConstants().get_Gconst(),
                                          "timestep": WorldPhysConstants().get_timestep()})

    def prepare_for_predictor_injection(self):
        in_queue = mp.Queue()
        key = len(self.predictors)
        self.control_queues[key] = in_queue
        self.task_counter[key] = 0
        return key

    def launch_new_predictor(self):
        in_queue = mp.Queue()
        mp.set_start_method('spawn')
        predictor_process = mp.Process(target=run_predictor_instance, args=(
            in_queue, self.shared_dict, self.hBodies))
        key = len(self.predictors)
        self.predictors[key] = predictor_process
        self.predictors[key].start()
        self.control_queues[key] = in_queue
        self.task_counter[key] = 0

    def stop_all_predictors(self):
        predictors_keys = list(self.predictors.keys())
        for key in predictors_keys:
            self.stop_predictor(key)

    def stop_predictor(self, key):
        self.control_queues[key].put({"type": "stop"})
        time.sleep(1)
        self.predictors[key].join()
        self.predictors.pop(key)
        self.control_queues.pop(key)
        self.task_counter.pop(key)

    def proceed_command(self, cmd: Command):
        action = cmd.get_action()
        params = cmd.get_params()
        match action:
            case 'terminate_predictor_process':
                predictors_keys = list(self.predictors.keys())
                if len(predictors_keys) > 0:
                    self.stop_predictor(predictors_keys[0])

            case 'add_predictor_process':
                run_predictor_process()

    def update_hbodies_location(self):
        # launch_new_TrajectoryPredictor_controller()
        # self.stop_all_predictors()
        # self.launch_new_predictor()
        # time.sleep(1)
        # self.launch_new_predictor()
        # self.launch_new_predictor()
        # self.update_physics()
        bodies_descr = self.hBodies.export_descr()
        predictors_keys = list(self.predictors.keys())
        for key in predictors_keys:
            self.control_queues[key].put({"type": "update_hbodies",
                                          "data": bodies_descr})

    def login(self, mark):
        try:
            self.shared_dict[f"{mark}_ready"] = True
            self.shared_dict[f"{mark}_predictions"] = []
            self.shared_dict[f"{mark}_time"] = 0
        except Exception as e:
            pass

    def logout(self, mark):
        if f"{mark}_ready" in self.shared_dict:
            self.shared_dict.pop(f"{mark}_ready")
        if f"{mark}_predictions" in self.shared_dict:
            self.shared_dict.pop(f"{mark}_predictions")
        if f"{mark}_time" in self.shared_dict:
            self.shared_dict.pop(f"{mark}_time")

    def upload_task(self, mark, params):
        if not self.is_online():
            return False
        if self.shared_dict[f"{mark}_ready"]:
            key = self.get_free_predictor()
            self.control_queues[key].put({"type": "put",
                                          "mark": mark,
                                          "params": params})
            self.task_counter[key] = self.task_counter[key]+1
            self.shared_dict[f"{mark}_ready"] = False
            return True
        else:
            return False

    def get_prediction(self, mark):
        if f"{mark}_predictions" in self.shared_dict:
            self.add_predictor_performance_timestamp(
                self.shared_dict[f"{mark}_time"])
            return self.shared_dict[f"{mark}_predictions"]
        else:
            pass
            return []


def run_predictor_instance(in_queue, out_dictionary, hBodies):
    predictor = TrajectoryPredictor(in_queue, out_dictionary, hBodies)
    predictor.start()


def run_predictor_process():
    predictor_controller = TrajectoryPredictor_controller()
    key = predictor_controller.prepare_for_predictor_injection()
    predictor_process = mp.Process(target=run_predictor_instance, args=(
        predictor_controller.control_queues[key], predictor_controller.shared_dict, hBodyPool_Singleton()))
    predictor_process.start()
    predictor_controller.predictors[key] = predictor_process


def launch_new_TrajectoryPredictor_controller():
    predictor_controller = TrajectoryPredictor_controller()
    predictor_controller.stop_all_predictors()
    pass
    run_predictor_process()
    # run_predictor_process()
    # run_predictor_process()
    # run_predictor_process()
    # predictor_controller.launch_new_predictor()
    # predictor_controller.launch_new_predictor()
    # predictor_controller.launch_new_predictor()


# получает на вход обновление скорости в моменте,
# возвращает в контекстный словарь вектор из предсказаний с
# N+1й точки.


class TrajectoryPredictor(TrajectoryCalculator):
    def __init__(self, in_queue, out_dictionary, hBodies):
        self.timestep = WorldPhysConstants().get_timestep()
        super().__init__(np.zeros(2), np.zeros(2))
        self.in_queue = in_queue
        self.out_dictionary = out_dictionary
        self.hBodies = hBodies
        # self.prediction_count_maxlimit = 250
        self._memset_grid(self.prediction_count_maxlimit)
        self.debug_output = False
        self.is_predictor = True

    def get_timestep(self):
        return self.timestep

    def set_predictors_depth(self, depth):
        try:
            real_depth = depth*WorldPhysConstants().get_real2sim_timescale()
            self.timestep = WorldPhysConstants().get_timestep()

            prediction_counts = int(real_depth//self.timestep)
            if prediction_counts > self.prediction_count_maxlimit:
                # pass
                self.timestep = real_depth/self.prediction_count_maxlimit
            self.predictions_count = min(
                self.prediction_count_maxlimit, prediction_counts)
            # self.predictions_count = self.prediction_count_maxlimit

        except Exception as e:
            pass

    # за каждое полученное сообщение в очереди, он считает траекторию с заданных координат
    # каждое сообщение промаркировано mark_id. Пока один запрос не обработан, не стоит
    # присылать другой с тем же mark_id

    def start(self):
        try:
            not_stopped = True
            while not_stopped:
                if not self.in_queue.empty():
                    command = self.in_queue.get()

                    match command["type"]:
                        case "put":

                            mark = command["mark"]
                            self.mark_id = mark
                            self.last_hbody_idx = command["params"]["last_hbody_idx"]
                            self.hbody_idx = command["params"]["hbody_idx"]
                            pos = np.array(command["params"]["pos"])
                            vel = np.array(command["params"]["vel"])
                            self.mass = command["params"]["mass"]
                            # *ConfigLoader().get("world.predictor_timedelay", float)
                            depth = command["params"]["depth"]
                            timestep = datetime.now()
                            self.set_predictors_depth(depth)
                            self.set_position_and_velocity(pos, vel)
                            dt = datetime.now()-timestep
                            preds = self.get_prediction()

                            # выгрузка результатов
                            self.out_dictionary[f"{mark}_predictions"] = preds
                            # освобождение мьютекса для следующей итерации
                            self.out_dictionary[f"{mark}_ready"] = True
                            self.out_dictionary[f"{mark}_time"] = dt.microseconds/1000000

                        case "stop":
                            not_stopped = False
                            break

                        case 'set_physics':
                            WorldPhysConstants().set_Gconst(command["Gconst"])
                            WorldPhysConstants().set_timestep(
                                command["timestep"])

                        case "update_hbodies":
                            descr = command["data"]
                            self.hBodies.import_descr(descr)

                # self.generate_prediction()
        except Exception as e:
            pass

    def get_prediction(self):
        return self.positions[self.predictions_count::-15].tolist()[::-1]

    def set_position_and_velocity(self, pos, vel):
        self.positions[0] = pos
        self.velocities[0] = vel
        for i in range(1, self.predictions_count):
            self.next_step(i)
