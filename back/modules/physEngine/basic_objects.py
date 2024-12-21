
import numpy as np
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.core import TrajectoryCalculator
from modules.physEngine.predictor import TrajectoryPredictor_controller
from modules.physEngine.core import CalculationUtilites, basic_Body, hBody, hBodyPool_Singleton
from modules.physEngine.triggers.collector import TriggerQueue
from modules.utils import PerformanceCollector
# класс-реальный объект.
# длительность тактов предсказания ~3
# связан со своей "копией", которая в отдельном потоке
# генерирует предсказания
from modules.physEngine.core import hBodyStatsCalculator


class lBody(TrajectoryCalculator):
    def __init__(self, x, y, mark_id=None):
        self.marker_type = self.__class__.__name__
        self.mark_id = mark_id if mark_id else str(id(self))
        pos = np.array([x, y])
        super().__init__(pos, np.array([0, 0]), mark_id)
        self.is_detectable = False
        self.in_edit_mode = False

    def get_description(self, requester_id=None):
        res = {
            "mark_id": self.mark_id,
            "type": self.marker_type,
            # [self.positions[1][0].item(), self.positions[1][1].item()],
            "pos": self.positions[1].tolist(),
            "vel": self.velocities[1].tolist(),
            'marker_type': self.marker_type,
            'in_edit_mode': self.in_edit_mode,
        }
        return res

    def set_edit_mode(self, state):
        self.in_edit_mode = state

class staticBody():
    def manual_init(self, is_cachable=True):
        self.stabilized = False
        self.stable_dphi = 0.0
        self.stable_phi = 0.0
        self.stable_distance_vector = np.array([100, 0])
        self.clockwise = False
        self.is_cachable = is_cachable

    def do_cache(self):
        self.stabilized = False
        self.hbody_idx = None
        self.last_hbody_idx = None

    def do_uncache(self):
        pass

    def get_velocity_np_static(self):
        radius = np.linalg.norm(self.stable_distance_vector)
        scalar_V = abs(self.stable_dphi*radius)
        add_phi = 90
        if self.clockwise:
            add_phi = -90
        req_phi = self.stable_phi+add_phi
        vector_V = CalculationUtilites.rotate_vector(
            np.array([scalar_V, 0]), req_phi)
        return vector_V

    def set_position_np_manual(self, position, clockwise=False):
        self.stabilized = False
        self.clockwise = clockwise
        return super().set_position_np_manual(position, clockwise)

    def try_stabilization_static(self):
        if self.hbody_idx:
            distance = self.get_distance2entity(self.hbody_idx)
            self.stable_distance_vector = np.array([distance, 0])
            current_vector = self.get_position_np(
            ) - self.hBodies.bodies[self.hbody_idx].get_position_np()

            # self.stable_distance_vector = CalculationUtilites.rotate_vecto_rad(self.stable_distance_vector, current_phi_rad)
            T = hBodyStatsCalculator.get_T(
                self.hBodies[self.hbody_idx].mass, distance)
            T_ticks = T*WorldPhysConstants().get_ticks_per_second()

            current_phi_rad = CalculationUtilites.get_radangle_between(
                current_vector, self.stable_distance_vector)
            self.stable_phi = current_phi_rad*180/3.14
            self.stable_dphi = 360/T_ticks
            self.clockwise = self.get_clockwise()
            if self.clockwise:
                self.stable_dphi = - self.stable_dphi
            self.stabilized = True

    def get_clockwise(self):
        vector2hbody = hBodyPool_Singleton().get(
            self.hbody_idx).get_position_np() - self.get_position_np()
        angle = CalculationUtilites.get_radangle_between(
            self.velocities[1], vector2hbody)
        angle2 = CalculationUtilites.get_radangle_between(
            self.velocities[1]*-1, vector2hbody)
        if 0 <= angle <= 3.14:
            return True
        return False

    def update_position(self):
        if not self.stabilized:
            super().update_position()
            self.try_stabilization_static()

        else:
            self.stable_phi = self.stable_phi+self.stable_dphi
            self.positions[0] = self.positions[1]
            self.positions[1] = self.hBodies.bodies[self.hbody_idx].get_position_np(
            ) + CalculationUtilites.rotate_vector(self.stable_distance_vector, self.stable_phi)
            self.positions[2] = self.positions[1]


class dynamicBody(TrajectoryCalculator):
    def __init__(self, x, y, mark_id=None):

        self.marker_type = self.__class__.__name__  # 'unknown'
        self.mark_id = mark_id if mark_id else str(
            self.__class__.__name__)+'_'+str(id(self))
        pos = np.array([x, y])
        stable_velocity_vector = CalculationUtilites.get_stable_velocity(pos)
        super().__init__(pos, stable_velocity_vector, mark_id)
        self.is_detectable = True
        self.desctiption = {
            "mark_id": self.mark_id,
            "type": self.type,
            'marker_type': self.marker_type,
            "alias": "neutral"
        }
        self.in_edit_mode = False

    def set_edit_mode(self, state):
        self.in_edit_mode = state

    def set_marker_type(self, marker_type):
        self.marker_type = marker_type
        self.desctiption['marker_type'] = marker_type

    def get_description(self, requester_id=None):
        self.desctiption["pos"] = self.positions[1].tolist()
        self.desctiption["vel"] = self.velocities[1].tolist()
        self.desctiption['in_edit_mode'] = self.in_edit_mode
        return self.desctiption

    def put_description(self, descr, forced=False):
        super().put_description(descr, forced)
        if "pos" in descr and "vel" in descr:
            self.set_position_and_velocity_init(
                np.array(descr["pos"]), np.array(descr["vel"]))
            return
        if "vel" in descr:
            self.set_velocity(np.array(descr["vel"]))
        if "pos" in descr:
            self.set_position_np_manual(np.array(descr["pos"]))

    def self_destruct(self):
        TriggerQueue().add("selfdestruct", self.mark_id, {})
        self.status = "destroyed"


class predictableBody(dynamicBody):
    def __init__(self, x, y, mark_id=None):
        super().__init__(x, y, mark_id)
        self.predictor_is_active = False
        self.task_uploaded = True
        self.predictor_depth = 10
        self.run_predictor()

    def run_predictor(self):
        try:
            self.predictor_controller = TrajectoryPredictor_controller()
            m = self.mark_id
            self.predictor_controller.login(m)
        except Exception as e:
            pass  # print(repr(e))

    def upload_state_to_predictor(self):
        params = {"pos": self.positions[1].tolist(),
                  "vel": self.velocities[1].tolist(),
                  "mass": self.mass,
                  "hbody_idx": self.hbody_idx,
                  "last_hbody_idx": self.last_hbody_idx,
                  "depth": self.predictor_depth}

        self.task_uploaded = self.predictor_controller.upload_task(
            self.mark_id, params)

    def set_predictor_state(self, state: bool):
        self.predictor_is_active = state
        if state:
            self.predictor_controller.login(self.mark_id)
        else:
            self.predictor_controller.logout(self.mark_id)

    def set_prediction_depth(self, duration: float):
        self.predictor_depth = float(duration)

    def get_prediction(self):
        if self.predictor_is_active:
            return self.predictor_controller.get_prediction(self.mark_id)
        return []

    def update_position(self):
        if self.predictor_is_active:
            self.upload_state_to_predictor()
        super().update_position()

    def get_description(self, requester_id=None):
        res = super().get_description(requester_id)
        res["predictions"] = self.get_prediction()
        return res


class controllableBody(predictableBody):
    def __init__(self, x, y, mark_id=None):
        super().__init__(x, y, mark_id)
        self.acceleration = 0.0
        self.rotation = 0.0
        self.direction = 0.0
        self.is_detectable = True


# region АКТИВАЦИЯ ДВИГАТЕЛЕЙ
    # prograde - по направлению движения


    def set_acceleration(self, value):
        self.acceleration = value

    # normal - от поверхности планеты
    def set_rotation(self, value):
        self.rotation = value

    def is_underAcceleration(self):
        return (self.acceleration != 0)

    # ускорение от активации двигателей вдоль касательной(prograd)

    def get_dA_artificial(self):
        self.next_step(2)
        next_position = self.positions[2]
        # вектор касательной

        tangent = np.array([0, 1])
        tangent = CalculationUtilites.rotate_vector(tangent, self.direction)
        # раскладываем на компоненты
        acceleration = CalculationUtilites.get_projections(
            self.acceleration, tangent)
        return acceleration
# endregion

    def update_position(self):
        if self.rotation != 0:
            self.direction = self.direction+WorldPhysConstants().get_timestep() * \
                self.rotation

        if self.is_underAcceleration():
            acceleration = self.get_acceleration_gravity(
                self.positions[1])+self.get_dA_artificial()
            self.velocities[2] = self.velocities[1] + \
                WorldPhysConstants().get_timestep()*acceleration
        super().update_position()

    def get_description(self, requester_id=None):
        res = super().get_description(requester_id)
        #if requester_id == self.mark_id:
        res["direction"] = self.direction
        return res
