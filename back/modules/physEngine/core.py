import math
import math as m
import copy
from modules.utils import Command, PerformanceCollector
import sys
import traceback
import random
import numpy as np
from modules.physEngine.world_constants import WorldPhysConstants
from modules.utils import ConfigLoader
# Астероиды, прибиты гвоздями к небу

from modules.physEngine.triggers.collector import TriggerQueue
from modules.physEngine.marks_collector import MarksCollector
from modules.utils import ConfigLoader, PerformanceCollector, get_dt_ms
from datetime import datetime
from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController


class basic_Body:
    def __init__(self, mark_id=None):
        self.hBodies = hBodyPool_Singleton()
        self.lBodies = lBodyPool_Singleton()
        self.mark_id = mark_id if mark_id else str(id(self))
        self.marker_type = self.__class__.__name__
        self.radar_visibility = 1
        self.radar_levels = [
            (0, "hbody"),
        ]
        self.type = self.__class__.__name__
        pass

    def set_visibility(self, value):
        self.radar_visibility = 1

    def get_position_np(self):
        return np.zeros(2)

    def get_entities_ids_list_in_range(self, bodies_dict, distance, include_myself=True):
        result = []
        for body_id in bodies_dict:
            if (not include_myself) and (body_id == self.mark_id):
                continue
            dist2body = self.get_distance2entity(body_id)
            if dist2body < distance:
                result.append(body_id)
        return result

    def get_entities_ids_list_in_interval(self, bodies_dict, distance1, distance2, include_myself=True):
        result = []
        for body_id in bodies_dict:
            if (not include_myself) and (body_id == self.mark_id):
                continue
            dist2body = self.get_distance2entity(body_id)
            if distance2 >= dist2body >= distance1:
                result.append(body_id)
        return result

    def get_entities_ids_list_outof_range(self, bodies_dict, distance, include_myself=True):
        result = []
        for body_id in bodies_dict:
            if (not include_myself) and (body_id == self.mark_id):
                continue
            dist2body = self.get_distance2entity(body_id)
            if dist2body >= distance:
                result.append(body_id)
        return result

    def get_entities_ids_from_list_in_range(self, body_ids, distance, include_myself=True):

        result = []
        for body_id in body_ids:
            if (not include_myself) and (body_id == self.mark_id):
                continue
            try:
                dist2body = self.get_distance2entity(body_id)
                if dist2body < distance:
                    result.append(body_id)
            except Exception as e:
                pass  # print(e)

        return result

    def get_entities_ids_from_list_in_interval(self, body_ids, distance1, distance2, include_myself=True):
        result = []
        for body_id in body_ids:
            if (not include_myself) and (body_id == self.mark_id):
                continue
            dist2body = self.get_distance2entity(body_id)
            if distance2 >= dist2body >= distance1:
                result.append(body_id)
        return result

    def get_entities_in_sector(self, body_ids, body_dict, arc_1, arc_2, distance=None, hard=False):
        result = []
        for body_id in body_ids:
            if distance:
                dist2body = 9000000
                if hard:
                    dist2body = self.get_distance2entity_hard(
                        body_dict[body_id])
                else:
                    dist2body = self.get_distance2entity(body_id)
                if dist2body > distance:
                    continue
            body_pos_vec = body_dict[body_id].get_position_np(
            )-self.get_position_np()
            angle_tar = CalculationUtilites.get_abs_angle_degrees_from_zero(
                body_pos_vec)
            if CalculationUtilites.is_in_sector(angle_tar, arc_1, arc_2):
                result.append(body_id)
        return result

    def get_entities_ids_from_category_in_range(self, category_name, distance, include_myself=True):
        body_ids = EntityIDGroupsController().get(category_name)
        result = self.get_entities_ids_from_list_in_range(
            body_ids, distance, include_myself)
        return result

    def check_entity_in_range(self, key, distance):
        return self.get_distance2entity(key) < distance

    def get_distance2entity(self, key):
        distance = CrossDistancePool().get(self.mark_id, key)
        if distance:
            return distance
        bpool = self.lBodies
        if key in self.hBodies.bodies:
            bpool = self.hBodies
        if key not in bpool.bodies:
            return 9000000
        return self.get_distance2entity_hard(bpool[key])

    def get_distance2position(self, position):
        return np.linalg.norm(position-self.get_position_np())

    def get_distance2entity_hard(self, any_body):
        req_pos = any_body.get_position_np()
        return np.linalg.norm(req_pos-self.get_position_np())

    def get_angle_between(self, position):
        vector = self.get_position_np()-position
        vector_zero = np.array([1, 0])
        alpha_rad = CalculationUtilites.get_radangle_between(
            vector, vector_zero)
        return alpha_rad

    def get_radial_coordinates(self, position):
        vector = position-self.get_position_np()
        vector_zero = np.array([1, 0])
        alpha_rad = CalculationUtilites.get_radangle_between(
            vector, vector_zero)
        return alpha_rad, np.linalg.norm(vector)

    def get_decart_relative_coordinates(self, alpha_rad, distance):
        vector = np.array([distance, 0])
        vector_rotated = CalculationUtilites.rotate_vecto_rad(
            vector, alpha_rad)
        return self.get_position_np()+vector_rotated

    def get_scan_level(self, scan_source, scan_power, close_radar_distance):
        distance = np.linalg.norm(scan_source-self.get_position_np())

        if distance > scan_power:
            return -1
        if distance <= close_radar_distance:
            return -1
        # distance/scan_power - какова дистанция в процентах от максимального радиуса радара. 1 - на пределе видимости, 0 - в упор.
        # scan_level - обратная величина. 0 - на пределе, 1 - на границе обычного радара
        # временное решение!
        # маркер - это процент расстояния от границ обычного радара до дальнего
        # за границами дальнего не видно ничего и никак.
        # видимость - это насколько в процентах хорошо видно.
        # scan_level = scan_level*3
        # Видимость 1 - без штрафов и бонусов. Видимость 0.5 - тебя видно в два раза хуже
        scan_level = 1-(distance-close_radar_distance) / \
            (scan_power-close_radar_distance)
        scan_level = scan_level*self.radar_visibility
        return scan_level

    def get_radar_mark(self, scan_source, scan_power, close_radar_distance):
        scan_level = self.get_scan_level(
            scan_source, scan_power, close_radar_distance)

        mark = None
        for level in self.radar_levels:
            if scan_level > level[0]:
                mark = level[1]

        return mark

    def put_description(self, descr, forced):
        pass


class hBody(basic_Body):
    def __init__(self, x, y, r=100, m=10):
        super().__init__()
        self.lBodies = lBodyPool_Singleton()
        self.position = np.array([x, y])
        self.gravity_well_radius = r
        self.mass = ConfigLoader().get("world.mass_coeff", float)*self.gravity_well_radius
        self.critical_r = ConfigLoader().get("world.critical_r_percentage", float) * \
            self.gravity_well_radius
        self.gravity_well_linear_percentage = ConfigLoader().get(
            "world.gravity_well_linear_percentage", float)
        self.mark_id = str(id(self))
        self.lbodies_in_gwell = []

        self.is_cached = False
        self.cached_lbodies = []
        # "h_body"
        
        pass

    def set_mass(self,mass):
        self.mass = mass

    def export_descr(self):
        return ({
            'pos_x': self.position[0],
            'pos_y': self.position[1],
            'mass': self.mass,
            'gravity_well_radius': self.gravity_well_radius,
            'mark_id': self.mark_id,
            'type': self.type,
            'marker_type': self.marker_type,
        })

    def import_descr(self, json_descr):
        self.position[0] = json_descr["pos_x"]
        self.position[1] = json_descr["pos_y"]
        self.mass = json_descr["mass"]
        self.gravity_well_radius = json_descr["gravity_well_radius"]
        self.critical_r = ConfigLoader().get("world.critical_r_percentage", float) * \
            self.gravity_well_radius
        self.mark_id = json_descr["mark_id"]
        self.marker_type = json_descr["type"]

    def get_position(self):  # возвращает [x,y,r]
        return [self.position[0].item(), self.position[1].item()]

    def get_position_np(self):
        return self.position

    def set_position_np_manual(self, position, clockwise=False):
        self.position = position

    def get_distance2position_from_border(self, position):
        return self.get_distance2position(position)-self.gravity_well_radius

    def get_description(self, requester_id=None):
        return {
            "mark_id": self.mark_id,
            "type": self.type,
            "pos": [self.position[0].item(), self.position[1].item()],
            "mass": self.mass,
            "gr": self.gravity_well_radius,
            'critical_r': self.critical_r,
            'marker_type': self.marker_type,
        }

    def put_description(self, json_descr, forced=False):
        self.marker_type = json_descr["marker_type"]
        self.position = np.array(json_descr["pos"])
        self.gravity_well_radius = json_descr["gr"]
        self.mass = ConfigLoader().get("world.mass_coeff", float)*self.gravity_well_radius
        self.critical_r = ConfigLoader().get("world.critical_r_percentage", float) * \
            self.gravity_well_radius

        # self.critical_r = ConfigLoader().get("world.critical_r_percentage", float)*self.gravity_well_radius
        if forced:
            self.mass = json_descr["mass"]
            if "critical_r" in json_descr:
                self.critical_r = json_descr["critical_r"]
            self.mark_id = json_descr["mark_id"]
            self.type = json_descr["type"]

    def is_position_in_gravity_well(self, pos):
        distance = np.linalg.norm(self.position - pos)
        return distance < self.gravity_well_radius

    def add_in_gwell(self, mark_id):
        if mark_id not in self.lbodies_in_gwell:
            self.lbodies_in_gwell.append(mark_id)

    def del_from_gwell(self, mark_id):
        if mark_id in self.lbodies_in_gwell:
            self.lbodies_in_gwell.remove(mark_id)

    def get_lbodies_in_gwell(self):
        return self.lbodies_in_gwell

    def cache_static_lbodies(self, force=False):
        if not force:
            if self.is_cached:
                return
            self.is_cached = True
        to_del = []
        for lbody_idx in self.lbodies_in_gwell:
            if hasattr(self.lBodies[lbody_idx], "do_cache"):
                if self.lBodies[lbody_idx].is_cachable:
                    self.lBodies[lbody_idx].do_cache()
                    self.cached_lbodies.append(self.lBodies[lbody_idx])
                    to_del.append(lbody_idx)

        for lbody_idx in to_del:
            self.lBodies.delete(lbody_idx, no_delmark = True)

    def uncache_static_lbodies(self, force=False):
        if not force:
            if not self.is_cached:
                return
            self.is_cached = False
        for lbody in self.cached_lbodies:
            self.lBodies.add(lbody)
            self.lBodies[lbody.mark_id].do_uncache()
        self.cached_lbodies = []

    def check_cached_bodies(self):
        ships = self.get_entities_ids_from_category_in_range("is_ships", 1000)
        if not ships:
            self.cache_static_lbodies()
        else:
            self.uncache_static_lbodies()

    def step(self):
        bodies_ids = self.get_entities_ids_from_list_in_range(
            self.lbodies_in_gwell, self.critical_r, False)
        for body_id in bodies_ids:
            TriggerQueue().add("hBodyCollision",
                               self.mark_id, {"target": body_id})

    def get_random_stable_point(self):
        distance = random.uniform(
            self.critical_r+1, self.gravity_well_radius*self.gravity_well_linear_percentage-1)
        angle = random.uniform(0, 360)
        position = CalculationUtilites.rotate_vector(
            np.array([distance, 0]), angle)+self.position
        return position


# всё что летает(корабли и ракеты)
# не может висеть с нулевой скоростью


# базоый класс для объектов и для их траекторий
# моделирует тело без движков, которое просто летит под действием сил грацитации
# вычислительная сложность за итерацию - О(1)
class TrajectoryCalculator(basic_Body):
    def __init__(self, pos, vel, mark_id=None):
        super().__init__(mark_id)
        self.predictions_count = 3  # минимальное значение
        self.prediction_count_maxlimit = 250
        self.hBodies = hBodyPool_Singleton()
        self.lBodies = lBodyPool_Singleton()
        self.mass = 1.0
        self.hbody_idx = None
        self.last_hbody_idx = None

        self.positions = np.zeros(
            [self.predictions_count, 2], dtype=np.float32)
        self.velocities = np.zeros(
            [self.predictions_count, 2], dtype=np.float32)
        # текущая в момент времени позиция лежит по индексу 1
        # по индексу ноль - координаты на прошлом шаге
        self.debug_output = False
        self.is_predictor = False
        self.set_position_and_velocity_init(pos, vel)
        self._surrounding_update_frame = WorldPhysConstants().current_frame()
        self._surrounding_hbodies = []

    def set_position_and_velocity_init(self, pos, vel):
        for i in range(self.predictions_count):
            self.positions[i] = pos
            self.velocities[i] = vel

    def set_position_np_manual(self, position, clockwise=False):
        self.positions[0] = position
        vel = CalculationUtilites.get_stable_velocity(position)
        if clockwise:
            vel = vel*-1
        self.velocities[0] = vel

        for i in range(1, self.predictions_count):
            self.next_step(i)

    def _get_surrounding_hbodies_ids(self):
        self._surrounding_update_frame = WorldPhysConstants().current_frame()
        if self.hbody_idx:
            return [self.hbody_idx]
        return self.hBodies.get_index_assosiated_idx_list(self.last_hbody_idx)

    def get_surrounding_hbodies_ids(self):
        if WorldPhysConstants().current_frame() != self._surrounding_update_frame:
            self._surrounding_hbodies = self._get_surrounding_hbodies_ids()
        return self._surrounding_hbodies

    def _memset_grid(self, n_cells: int):
        pos_backup = self.positions[:2]
        vel_backup = self.velocities[:2]
        predictions_count = min(n_cells, self.prediction_count_maxlimit)
        self.positions = np.zeros([predictions_count, 2], dtype=np.float32)
        self.velocities = np.zeros([predictions_count, 2], dtype=np.float32)
        self.positions[:2] = pos_backup
        self.velocities[:2] = vel_backup

    def get_timestep(self):
        return WorldPhysConstants().get_timestep()

    def get_Gconst(self):
        return WorldPhysConstants().get_Gconst()

    def set_position_and_velocity(self, pos, vel):
        self.positions[0] = pos
        self.velocities[0] = vel
        for i in range(1, self.predictions_count):
            self.next_step(i)

    def set_velocity(self, vel):
        self.velocities[0] = vel
        for i in range(1, self.predictions_count):
            self.next_step(i)

    def update_predictions(self):
        self.velocities[:-1] = self.velocities[1:]
        self.positions[:-1] = self.positions[1:]
        self.next_step(self.predictions_count-1)

    def next_step(self, n_iter):
        assert n_iter != 0, "can not be first step in grid"
        acceleration = self.get_acceleration(self.positions[n_iter-1])
        self.velocities[n_iter] = self.velocities[n_iter-1] + \
            acceleration*self.get_timestep()
        self.positions[n_iter] = self.positions[n_iter-1] + \
            self.velocities[n_iter]*self.get_timestep()

    def get_acceleration(self, position):
        return self.get_acceleration_gravity(position)

    def set_current_dwell(self, new_hbody_idx):
        if self.hbody_idx == new_hbody_idx:
            return
        self.delete_self_from_dwell()
        self.hbody_idx = new_hbody_idx
        self.add_self_in_dwell()

    def add_self_in_dwell(self):
        if self.is_predictor:
            return
        if self.hbody_idx in self.hBodies.bodies:
            self.hBodies[self.hbody_idx].add_in_gwell(self.mark_id)

    def delete_self_from_dwell(self):
        if self.is_predictor:
            return
        if self.hbody_idx in self.hBodies.bodies:
            self.hBodies[self.hbody_idx].del_from_gwell(self.mark_id)

    def get_acceleration_gravity(self, position):
        self.last_hbody_idx = self.hbody_idx if self.hbody_idx else self.last_hbody_idx
        need_update_hbody_idx = False

        tmp_hbody_idx = self.hbody_idx
        if self.hbody_idx:
            is_hbody_idx_actual = self.hBodies.is_position_in_gravity_well(
                position, self.hbody_idx)
            if not is_hbody_idx_actual:
                self.delete_self_from_dwell()
                self.hbody_idx = None
                need_update_hbody_idx = True
        else:
            need_update_hbody_idx = True

        if need_update_hbody_idx:
            tmp_hbody_idx = self.hBodies.get_gravity_affected_body_idx(
                position, self.last_hbody_idx)
            is_hbody_idx_actual = self.hBodies.is_position_in_gravity_well(
                position, tmp_hbody_idx)
            if is_hbody_idx_actual:
                self.set_current_dwell(tmp_hbody_idx)

        vector = self.hBodies.get_single_gravity(
            position, self.mass, tmp_hbody_idx)

        # if self.hbody_idx:
        # vector = self.hBodies.get_single_gravity(position, self.mass,self.hbody_idx )
        # return vector
        # else:
        # vector = self.hBodies.get_summary_gravity(position, self.mass, self.last_hbody_idx) #если вне гравитационного колодца

        #if self.debug_output:

        #    if np.linalg.norm(vector) == 0:
                # print("get_acceleration_gravity", self.hbody_idx, self.last_hbody_idx)
        #       pass
        return vector

    def update_position(self):
        self.update_predictions()

    def get_position(self):
        return [round(a, 2) for a in self.positions[1].tolist()]

    def get_position_np(self):
        return self.positions[1]

    def get_velocity_np(self):
        return self.velocities[1]

    def get_abs_velocity(self):
        # mag = np.sqrt(self.velocities[1].dot(self.velocities[1]))
        c1 = float(self.velocities[1][0])
        c2 = float(self.velocities[1][1])
        return math.sqrt(c1*c1+c2*c2)
        # return float(np.linalg.norm(self.velocities[1]))

    def get_prediction(self):
        return []
        # return self.positions[::].tolist()

    def stabilize_orbit(self, offset=0):
        position_tmp = self.get_position_np()
        related_hbody: hBody = self.hBodies.get_gravity_affected_body(
            position_tmp)
        if not related_hbody:
            return
        alpha_rad, distance = related_hbody.get_radial_coordinates(
            position_tmp)
        position_new = related_hbody.get_decart_relative_coordinates(
            alpha_rad, distance+offset)
        stable_velocity_vector = CalculationUtilites.get_stable_velocity(
            position_new, self.velocities[1])
        self.set_position_and_velocity(position_new, stable_velocity_vector)


class CrossDistancePool:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrossDistancePool, cls).__new__(cls)
            cls._instance.lBodies = lBodyPool_Singleton()
            cls._instance.hBodies = hBodyPool_Singleton()
            cls._instance.distances = {}

        return cls._instance

    def update(self):
        self.distances = {}
        avg_hbody_count = []
        for lbody_idx in self.lBodies.bodies:
            for lbody2_idx in self.lBodies.bodies:
                key = (lbody_idx, lbody2_idx)
                key_alt = (lbody2_idx, lbody_idx)
                if key_alt not in self.distances:
                    distance = self.lBodies.bodies[lbody_idx].get_distance2entity_hard(
                        self.lBodies.bodies[lbody2_idx])
                    self.distances[key] = distance

            req_hbodies_idx = self.lBodies.get(
                lbody_idx).get_surrounding_hbodies_ids()
            avg_hbody_count.append(len(req_hbodies_idx))
            # ChunkController().get_active_hbodies(): #self.hBodies.bodies:
            for hbody_idx in req_hbodies_idx:
                if hbody_idx:
                    distance = self.lBodies[lbody_idx].get_distance2entity_hard(
                        self.hBodies[hbody_idx])
                    key = (lbody_idx, hbody_idx)
                    self.distances[key] = distance
        PerformanceCollector().add("avg_hbody_count", np.mean(
            avg_hbody_count if avg_hbody_count else [0]))

    def get(self, mark_1, mark_2):
        try:
            if mark_1 == mark_2:
                return 0
            if self.distances == {}:
                self.update()
            if (mark_1, mark_2) in self.distances:
                return self.distances[(mark_1, mark_2)]
            return self.distances[(mark_2, mark_1)]
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            pass  # print(traceback.print_tb(exc_traceback))
        return None


class lBodyPool_Singleton:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(lBodyPool_Singleton, cls).__new__(cls)
            cls._instance.bodies = {}
            cls._instance.bodies_description = {}

        return cls._instance

    def __getitem__(self, key):
        return self.bodies[key]

    def clear(self):
        EntityIDGroupsController().clear()
        self.bodies = {}

    def get(self, mark_id):
        if mark_id in self.bodies:
            return self.bodies[mark_id]
        return None

    def if_body_exists(self, body_id):
        return body_id in self.bodies

    def add(self, body_object):
        lbody_id = body_object.mark_id
        self.bodies[lbody_id] = body_object

    def get_ships_ids(self):
        ids = []
        for k in self.bodies:
            body = self.bodies[k]
            if body.type == "ae_ship":
                ids.append(body.mark_id)
        return ids

    def delete(self, body_id, no_delmark = False):
        if body_id in self.bodies:
            self.bodies.pop(body_id)

        for hbodi_id in hBodyPool_Singleton().bodies:
            hBodyPool_Singleton().bodies[hbodi_id].del_from_gwell(body_id)

        if not no_delmark:
            EntityIDGroupsController().remove(body_id)

    def iter_loop(self):
        self.bodies_description = {}
        self.stats = {}

        tmp_t1 = datetime.now()
        for i in self.bodies:
            self.bodies[i].update_position()

        tmp_t2 = datetime.now()

        for i in self.bodies:
            self.bodies_description[i] = self.bodies[i].get_description()
        tmp_t3 = datetime.now()

        PerformanceCollector().add("lBodyPool.iter_loop.update_position",
                                   get_dt_ms(tmp_t1, tmp_t2))
        PerformanceCollector().add("lBodyPool.iter_loop.get_description",
                                   get_dt_ms(tmp_t2, tmp_t3))

    def update_description(self):
        self.bodies_description = {}
        for i in self.bodies:
            self.bodies_description[i] = self.bodies[i].get_description()

    def get_bodies_description(self):
        return self.bodies_description


class hBodyPool_Singleton:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(hBodyPool_Singleton, cls).__new__(cls)
            cls._instance.bodies = {}
            cls._instance.gravity_well_linear_percentage = ConfigLoader().get(
                "world.gravity_well_linear_percentage", float)
            cls._instance.realtime_update = True
            cls._instance.bodies_description = None
            cls._instance._index = {}
        return cls._instance

    def if_body_exists(self, mark_id):
        return mark_id in self.bodies


    def get_max_distance(self):
        distance = 0
        body_idx = None
        for body_idx in self.bodies:
            pos = self.bodies[body_idx].get_position_np()
            tmp_dist = np.linalg.norm(pos)
            if tmp_dist > distance:
                distance = tmp_dist
        if not body_idx: return 10000
        return distance+self.bodies[body_idx].gravity_well_radius+200

    def proceed_command(self, command: Command):
        action = command.get_action()
        match action:
            case "set_realtime_update":
                self.realtime_update = command.get_params()["value"]
                self.bodies_description = self.get_live_description()

            case "cache_static_lbodies":
                self.cache_static_lbodies()

            case 'uncache_static_lbodies':
                self.uncache_static_lbodies()

    def __getitem__(self, key):
        return self.bodies[key]

    def __iter__(self):
        return iter(self.bodies)

    def clear_index(self):
        self.index = {}

    def cache_static_lbodies(self):
        for body_idx in self.bodies:
            self.bodies[body_idx].cache_static_lbodies(force=True)

    def uncache_static_lbodies(self):
        for body_idx in self.bodies:
            self.bodies[body_idx].uncache_static_lbodies(force=True)

    @property
    def index(self):
        if not self._index:
            self.generate_index()
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    def get_index_assosiated_idx_list(self, idx):
        # return self.bodies
        try:
            return copy.deepcopy(self.index[idx])
        except Exception as e:
            pass
            # pass#print("get_index_assosiated_idx_list", repr(e))
        return self.bodies

    def generate_index(self):
        self.clear_index()
        for body_idx in self.bodies:
            self.generate_index_for_single_body(body_idx)
        pass  # print("index generated")

    def generate_index_for_single_body(self, body_idx):
        tmp = []
        for body_idx2 in self.bodies:
            distance = self.bodies[body_idx].get_distance2entity_hard(
                self.bodies[body_idx2])
            gravity_connection_distance = self.bodies[body_idx].gravity_well_radius + \
                self.bodies[body_idx2].gravity_well_radius
            if distance < gravity_connection_distance*2:
                tmp.append(body_idx2)
                if body_idx2 in self._index:
                    self._index[body_idx2].append(body_idx)
        self._index[body_idx] = tmp

    def export_descr(self):
        result = {}
        for body_idx in self.bodies:
            result[body_idx] = self.bodies[body_idx].export_descr()
        return result

    def import_descr(self, json_descr):
        self.bodies = {}
        for k in json_descr:
            body = hBody(0, 0, 1, 1)
            body.import_descr(json_descr[k])
            self.add(body)
        self.generate_index()
        self.update_description()

    def add(self, hbody):
        self.bodies[hbody.mark_id] = hbody
        self.generate_index_for_single_body(hbody.mark_id)

    def get(self, body_id):
        if body_id in self.bodies:
            return self.bodies[body_id]
        return None

    def delete(self, body_id):
        if body_id in self.bodies:
            self.bodies.pop(body_id)
        self.generate_index()
        self.update_description()

    def get_gravity_affected_body(self, pos):
        for k in self.bodies:
            if self.bodies[k].is_position_in_gravity_well(pos):
                return self.bodies[k]
        return None

    def get_gravity_affected_body_idx(self, pos, last_hbody_idx=None):
        # если last_hbody_idx == None, вернет словарь всех тел
        # если нет - вернет список соседей
        list_idx = self.get_index_assosiated_idx_list(last_hbody_idx)
        for k in list_idx:
            if self.bodies[k].is_position_in_gravity_well(pos):
                return k
        # ес

        if last_hbody_idx:
            distance_to_last_hbody = np.linalg.norm(
                self.bodies[last_hbody_idx].get_position_np()-pos)
            last_hbody_gr = self.bodies[last_hbody_idx].gravity_well_radius
            if distance_to_last_hbody < last_hbody_gr+500:
                return last_hbody_idx

        # ультимативная штука
        last_hbody_idx = self.get_closest_hbody(pos)
        return last_hbody_idx

    def get_closest_hbody(self, pos):
        distance = 999999999999999999999999
        req_hbody_idx = None
        for hbody_idx in self.bodies:
            hb_pos = self.bodies[hbody_idx].get_position_np()
            tmp_dist = np.linalg.norm(pos-hb_pos)
            if tmp_dist < distance:
                distance = tmp_dist
                req_hbody_idx = hbody_idx
        return req_hbody_idx

    def get_single_gravity(self, position, mass, hbody_idx):
        if not hbody_idx:
            return np.zeros(2)
        dPos = self.bodies[hbody_idx].position-position
        gravity_well_radius = self.bodies[hbody_idx].gravity_well_radius
        r = max(np.linalg.norm(dPos), 20)
        F = WorldPhysConstants().get_Gconst() * \
            (mass*self.bodies[hbody_idx].mass)/(r*r)

        distance_2_center = r/gravity_well_radius
        if self.gravity_well_linear_percentage <= distance_2_center <= 1:
            F = F*((1-distance_2_center)/(1-self.gravity_well_linear_percentage))

        Fproj = CalculationUtilites.get_projections(F, dPos)/mass
        return Fproj

    def get_summary_gravity(self, pos, mass, last_hbody_idx=None):
        list_idx = self.get_index_assosiated_idx_list(last_hbody_idx)
        summaryFproj = np.zeros(2)
        for k in list_idx:
            summaryFproj = summaryFproj+self.get_single_gravity(pos, mass, k)
        return summaryFproj

    def get_bodies_positions(self):
        hBodies_dict = {}
        for i in self.bodies:
            hBodies_dict[i] = self.bodies[i].get_position()
        return hBodies_dict

    def get_live_description(self):
        hBodies_dict = {}
        for i in self.bodies:
            hBodies_dict[i] = self.bodies[i].get_description()
        return hBodies_dict

    def update_description(self):
        if not self.realtime_update:
            self.bodies_description = self.get_live_description()

    def get_bodies_description(self):

        if self.realtime_update:
            return self.get_live_description()
        else:
            if not self.bodies_description:
                self.update_description()
        return self.bodies_description

    def is_position_in_gravity_well(self, pos, hbody_idx):
        try:
            return self.bodies[hbody_idx].is_position_in_gravity_well(pos)
        except Exception as e:
            #exc_type, exc_value, exc_traceback = sys.exc_info()
            pass  # print(traceback.print_tb(exc_traceback))
            return False

    def clear(self):
        self.bodies = {}
        self.update_description()
        self.clear_index()

    def get_uncached_hbodies_list(self):
        ships = EntityIDGroupsController().get("is_ships")
        hbodies_2_prepare = []
        for ship_id in ships:
            ship_body = lBodyPool_Singleton().get(ship_id)
            if ship_body.hbody_idx:
                hbodies_2_prepare.append(ship_body.hbody_idx)
            else:
                hbodies_2_prepare.append(ship_body.last_hbody_idx)

        hbodies_2_prepare2 = []
        for hbodi_id in hbodies_2_prepare:
            if hbodi_id:
                new_bodies = self.get_index_assosiated_idx_list(hbodi_id)
                hbodies_2_prepare2 = hbodies_2_prepare2+new_bodies

        return set(hbodies_2_prepare+hbodies_2_prepare2)

    def iter_loop(self):
        need_2_uncache = self.get_uncached_hbodies_list()
        a = len(self.bodies)
        for k in self.bodies:
            if k in need_2_uncache:
                self.bodies[k].uncache_static_lbodies()
            else:
                self.bodies[k].cache_static_lbodies()
            self.bodies[k].step()


class CalculationUtilites:
    hBodies = hBodyPool_Singleton()
    # проекция скаляра F на вектор

    def get_projections(F, vector):
        dx = vector[0]
        dy = vector[1]
        r = np.linalg.norm(vector)
        if r == 0:
            return np.array([0, 0], dtype=np.float32)
        Fx = F*dx/r
        Fy = F*dy/r
        return np.array([Fx, Fy], dtype=np.float32)

    #

    def get_stable_velocity(pos, vec=np.zeros(2)):
        hbody = CalculationUtilites.hBodies.get_gravity_affected_body(pos)
        if not hbody:
            return np.array([0, 0])
        mass = hbody.mass
        radius = pos-hbody.position
        radius_scalar = max(1, np.linalg.norm(radius))
        tangent = CalculationUtilites.rotate_vector(radius, 90)
        V_scalar = m.sqrt(WorldPhysConstants().get_Gconst()*mass/radius_scalar)
        V_vector = CalculationUtilites.get_projections(V_scalar, tangent)
        if np.linalg.norm(vec) != 0:
            cos_alpha = CalculationUtilites.get_cosangle_between(V_vector, vec)
            if cos_alpha < 0:
                V_vector = V_vector*-1
        return V_vector

    def rotate_vecto_rad(vector, angler):
        x = vector[0]
        y = vector[1]
        newx = x*m.cos(angler) - y*m.sin(angler)
        newy = x*m.sin(angler) + y*m.cos(angler)
        return np.array([newx, newy])

    def rotate_vector(vector, angle):
        x = vector[0]
        y = vector[1]
        angler = angle*m.pi/180
        newx = x*m.cos(angler) - y*m.sin(angler)
        newy = x*m.sin(angler) + y*m.cos(angler)
        return np.array([newx, newy])

    def get_cosangle_between(vector1, vector2):
        cos_alpha = np.dot(vector1, vector2) / \
            (np.linalg.norm(vector1)*np.linalg.norm(vector2))
        return cos_alpha

    def get_radangle_between(vector1, vector2):
        cos_alpha = CalculationUtilites.get_cosangle_between(vector1, vector2)
        alpha_rad = np.arccos(cos_alpha)
        vector3_ort = CalculationUtilites.rotate_vector(vector2, 90)
        cos_alpha_ort = CalculationUtilites.get_cosangle_between(
            vector1, vector3_ort)
        if cos_alpha_ort < 0:
            alpha_rad = -alpha_rad

        return alpha_rad

    def get_abs_angle_degrees_from_zero(vector1):
        vector2 = np.array([1, 0])
        cos_alpha = CalculationUtilites.get_cosangle_between(vector1, vector2)
        alpha_rad = np.arccos(cos_alpha)
        vector3_ort = CalculationUtilites.rotate_vector(vector2, 90)
        cos_alpha_ort = CalculationUtilites.get_cosangle_between(
            vector1, vector3_ort)
        if cos_alpha_ort < 0:
            alpha_rad = 3.14*2-alpha_rad

        return alpha_rad*180/3.14

    def degress2rads(value):
        return value*3.14/180

    def is_in_sector(value, arc1, arc2):
        arc1 = (arc1+360*2) % 360
        arc2 = (arc2+360*2) % 360
        value = (value+360*2) % 360
        if arc1 < arc2:
            arc2 = arc2-360
        if arc1 < value:
            value = value-360
        return arc2 < value < arc1

    def get_intersection_for_2_circles(pos1, rad1, pos2, rad2):
        # https://algolist.ru/maths/geom/intersect/circlecircle2d.php#:~:text=%2D2ax%2D2by%20%3D%20R2,%2D%20a2%20%2D%20b2.&text=ax%2Bby%3DC%2C%20%D0%B3%D0%B4%D0%B5,%D0%A1%20%2D%20%D0%BD%D0%BE%D0%B2%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D0%B7%D0%BD%D0%B0%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%B2%D1%8B%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F%20%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%B0.
        d = np.linalg.norm(pos1-pos2)
        if d == 0:
            return None
        a = (rad1**2 - rad2**2 + d**2)/(2*d)
        discr = rad1**2 - a**2
        if discr < 0:
            return None
        h = math.sqrt(discr)
        pos3 = pos1+a*(pos2-pos1)/d
        p4_1_x = pos3[0]+h*(pos2[1]-pos1[1])/d
        p4_1_y = pos3[1]-h*(pos2[0]-pos1[0])/d

        p4_2_x = pos3[0]-h*(pos2[1]-pos1[1])/d
        p4_2_y = pos3[1]+h*(pos2[0]-pos1[0])/d

        return np.array([p4_1_x, p4_1_y]), np.array([p4_2_x, p4_2_y])


class hBodyStatsCalculator:
    def get_stats(body_descr):
        ConfigLoader().update()
        results = {}
        mass = body_descr["mass"]
        Rgr = body_descr["gr"]
        Rcr = body_descr["critical_r"]
        Rmd = (Rgr+Rcr)/2
        for rname, rval in [
            ("_Rcr", Rcr),
            ("_Rmd", Rmd),
            ("_Rmx", Rgr),
        ]:
            results["V" +
                    rname] = round(hBodyStatsCalculator.get_V(mass, rval), 2)
            results["T" +
                    rname] = round(hBodyStatsCalculator.get_T(mass, rval), 2)

        results["delV:Rcr-Rmd"] = hBodyStatsCalculator.get_delV(mass, Rcr, Rmd)
        results["delV:Rmd-Rmx"] = hBodyStatsCalculator.get_delV(mass, Rmd, Rgr)
        results["delV:Rcr-Rmx"] = hBodyStatsCalculator.get_delV(mass, Rcr, Rgr)
        return results

    def get_V(m, r):
        G = ConfigLoader().get("world.gravity_constant", float)
        V = math.sqrt((m*G)/r)
        return V

    def get_T(m, r):
        v = hBodyStatsCalculator.get_V(
            m, r)*WorldPhysConstants().get_real2sim_timescale()
        T = 2*3.1415*r/v
        return T

    def get_delV(m, r1, r2):
        r = r2/r1
        v = hBodyStatsCalculator.get_V(m, r1)
        delV1 = round(v*(math.sqrt(2*r/(r+1))-1), 2)
        delV2 = round((v/math.sqrt(r))*(1-math.sqrt(2/(r+1))), 2)
        return f"{delV1}, {delV2}, {round(delV1+delV2,2)}"
