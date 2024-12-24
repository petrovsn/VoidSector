from math import sqrt, pow
from modules.physEngine.basic_objects import predictableBody
from modules.physEngine.active_objects import destructableObject
from modules.physEngine.core import CalculationUtilites
import numpy as np
from modules.physEngine.triggers.collector import TriggerQueue
from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController
from modules.physEngine.world_constants import WorldPhysConstants
import random
from modules.utils import ConfigLoader
from modules.physEngine.solar_flare.solar_flar_defendzone import SolarFlareDefendZone
from modules.physEngine.aliances_controller import AlianceController


class ProjectileListController:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProjectileListController, cls).__new__(cls)
            cls._instance.projectile_ids = {}

        return cls._instance

    def get(self, req_master_id, belongs_to_me=False):
        result = []
        for master_id in self.projectile_ids:
            if master_id != req_master_id:
                result = result+self.projectile_ids[master_id]
        return result

    def add(self, master_id, mark_id):
        if master_id not in self.projectile_ids:
            self.projectile_ids[master_id] = []

        if mark_id not in self.projectile_ids[master_id]:
            self.projectile_ids[master_id].append(mark_id)

    def remove(self, master_id, mark_id):
        if master_id in self.projectile_ids:
            if mark_id in self.projectile_ids[master_id]:
                self.projectile_ids[master_id].remove(mark_id)

    def clear(self):
        self.projectile_ids = []


class pjtl_Basic(predictableBody):  # ,destructableObject):
    def __init__(self, master_id):
        predictableBody.__init__(self, 9999999, 999999)
        # destructableObject.__init__(self, self.mark_id)
        self.master_id = master_id
        self.set_marker_type("projectile")
        self.positions[1] = np.array([9999999, 999999])
        self.status = "launched"
        if self.master_id in self.lBodies.bodies:
            self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
            self.status = "loaded"
        self.predictor_depth = 5
        self.explosion_radius = 0
        self.velocity_penalty = 1
        self.template = {}
        self.set_predictor_state(True)
        self.pjtl_name = self.__class__.__name__
        self.damage_zone_radius = self.explosion_radius
        self.is_decoy = False

        # self.delete_self_from_dwell()

    def set_aim(self, vel_angle, vel_scalar):
        vel = self.get_vel_from_angular(
            vel_angle, vel_scalar)*self.velocity_penalty
        self.launch_vector = vel
        self.set_actual_vel()
        self.upload_state_to_predictor()

    def get_vel_from_angular(self, angle, speed):
        vector = np.array([1, 0])
        vector = CalculationUtilites.rotate_vector(vector, angle)
        vel = CalculationUtilites.get_projections(speed, vector)
        return vel

    def set_params(self, params):
        pass

    def get_params_template(self):
        return self.template

    def get_description(self, requester_id=None):
        result = super().get_description(requester_id)
        result["master_id"] = self.master_id
        result['explosion_radius'] = self.damage_zone_radius
        return result

    def set_actual_vel(self):
        vel = self.launch_vector + \
            self.lBodies.bodies[self.master_id].get_velocity_np()
        self.velocities[2] = vel
        self.velocities[1] = vel
        self.velocities[0] = vel

    def update_position(self):
        if self.status == "loaded":
            self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
            self.set_actual_vel()
            self.upload_state_to_predictor()

        elif self.status == "launched":
            self.update_predictions()

    def launch(self):
        self.launch_timestamp = WorldPhysConstants().current_frame()
        self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
        self.positions[2] = self.lBodies.bodies[self.master_id].get_position_np()
        self.status = "launched"
        ProjectileListController().add(self.master_id, self.mark_id)

    def takes_damage(self, damage_value, damage_type="explosion", damage_source=None):
        pass  # print(self.__class__.__name__, damage_type)
        match damage_type:
            case "explosion":
                self.detonate()
            case "emp":
                self.self_destruct()
            case 'collision':
                self.self_destruct()
            case 'radiation':
                self.detonate()

    def detonate(self):
        TriggerQueue().add("detonate", self.mark_id, {
            "danger_radius": self.explosion_radius})
        self.set_predictor_state(False)
        self.status = "destroyed"
        SolarFlareDefendZone().remove(self.mark_id)

    def self_destruct(self):
        super().self_destruct()
        ProjectileListController().remove(self.master_id, self.mark_id)
        SolarFlareDefendZone().remove(self.mark_id)


class pjtl_Constructed(pjtl_Basic):
    def __init__(self, master_id, pjtl_name, pjtl_description, dumb=False):
        self.template = {}
        if not dumb:
            pjtl_Basic.__init__(self, master_id)
        self.parse_pjtl_description(pjtl_description)
        self.pjtl_name = pjtl_name
        self.target_id = None
        self.type = pjtl_name
        self.radar_levels = [
            (0.5, "activity"),
            (0.75, "active_ship"),
        ]

        # if not dumb: SolarFlareDefendZone().add(self.mark_id)

    def set_params(self, params):
        if 'activation_delay' in params:
            activation_delay = float(params["activation_delay"])
            self.predictor_depth = (
                float(activation_delay)+float(self.ttl_delay))*(self.thrusters+1)
            self.activation_delay = WorldPhysConstants().get_ticks_in_seconds(activation_delay)
            self.upload_state_to_predictor()

    def get_description(self, requester_id=None):
        result = super().get_description(requester_id)
        if self.detection_radius:
            result["detection_radius"] = self.detection_radius
        if self.detonation_radius:
            result["detonation_radius"] = self.detonation_radius

        return result

    def parse_pjtl_description(self, pjtl_description):

        time_step = ConfigLoader().get("projectile_builder.time_step", float)
        radius_step = ConfigLoader().get("projectile_builder.radius_step", float)
        exp_radius_step = ConfigLoader().get("projectile_builder.exp_radius_step", float)

        self.thrusters = pjtl_description["thruster"]

        prediction_depth = 0
        activation_delay = pjtl_description["timer"]*time_step
        self.max_activation_delay = 0
        if activation_delay:
            self.template["activation_delay"] = [
                0, activation_delay, 1, activation_delay]
            self.max_activation_delay = activation_delay

            prediction_depth = prediction_depth+activation_delay

        self.activation_delay = WorldPhysConstants(
        ).get_ticks_in_seconds(self.max_activation_delay)

        ttl = pjtl_description["inhibitor"]*time_step
        self.ttl_delay = 0
        if ttl:

            self.ttl_delay = ttl
            prediction_depth = prediction_depth+ttl
        self.ttl = WorldPhysConstants().get_ticks_in_seconds(seconds=self.ttl_delay)

        self.predictor_depth = float(prediction_depth)*(self.thrusters+1)
        # self.upload_state_to_predictor()

        self.explosion_radius = round(
            pow(pjtl_description["explosive"], 0.3)*exp_radius_step)
        self.explosive_damage = self.explosion_radius*ConfigLoader().get("damage.explosion_damage_per_sec",
                                                                         float)*ConfigLoader().get("damage.explosive_duration", float)
        self.emp_radius = round(
            pow(pjtl_description["emp"], 0.3)*exp_radius_step)
        self.damage_zone_radius = max(self.explosion_radius, self.emp_radius)
        self.thrusters = pjtl_description["thruster"]
        self.ship_detection_radius = pjtl_description["entities_detection"]*radius_step
        self.projectiles_detection_radius = pjtl_description["projectiles_detection"]*radius_step
        self.detection_radius = max(
            self.ship_detection_radius, self.projectiles_detection_radius)

        self.busters = pjtl_description["buster"]
        self.buster_acceleration = ConfigLoader().get(
            "projectile_builder.buster_acceleration", float)*self.busters

        self.detonation_radius = pjtl_description["detonator"]*radius_step
        self.is_decoy = False
        if pjtl_description["decoy"]:
            self.is_decoy = True

        self.details_count = sum(pjtl_description.values())
        self.velocity_penalty = self.get_vel_penalty(pjtl_description)

    def get_vel_penalty(self, pjtl_description):
        sum_vel_penalty = ConfigLoader().get(
            "projectile_builder_velpenalty.detail_penalty", float)*self.details_count
        thrusters_penalty = ConfigLoader().get(
            "projectile_builder_velpenalty.thrusters", float)*self.thrusters
        busters_penalty = ConfigLoader().get(
            "projectile_builder_velpenalty.busters", float)*self.busters
        sensors_count = pjtl_description["entities_detection"] + \
            pjtl_description["projectiles_detection"] + \
            pjtl_description["detonator"]
        sensors_penalty = ConfigLoader().get(
            "projectile_builder_velpenalty.sensors", float)*sensors_count
        explosives_penalty = ConfigLoader().get(
            "projectile_builder_velpenalty.explosives", float)*pjtl_description["explosive"]
        sum_vel_penalty = sum_vel_penalty+thrusters_penalty + \
            busters_penalty+sensors_penalty+explosives_penalty
        return round(max(0, 1-sum_vel_penalty), 2)

    def get_stats(self):
        return {
            "activation_time": self.max_activation_delay,
            "ttl_time": self.ttl_delay,
            "explosion_radius/damage": f"{self.explosion_radius}/{self.explosive_damage}",
            "emp_radius": self.emp_radius,
            "speed_up": self.thrusters+1,
            "ship_detection_radius": self.ship_detection_radius,
            "projectiles_detection_radius": self.projectiles_detection_radius,
            "details": self.details_count,
            "velocity_penalty": self.velocity_penalty,
        }

    def update_position(self):
        if self.status == "loaded":
            self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
            # self.hbody_idx = self.lBodies.bodies[self.master_id].hbody_idx
            self.set_current_dwell(
                self.lBodies.bodies[self.master_id].last_hbody_idx)
            self.set_actual_vel()
            self.upload_state_to_predictor()

        elif self.status == "launched":
            if WorldPhysConstants().current_frame() - self.launch_timestamp > self.activation_delay:
                self.status = "activated"
                if self.is_decoy:
                    EntityIDGroupsController().add(
                        self.mark_id, ["radar_detectable"])
                self.activation_timestamp = WorldPhysConstants().current_frame()

            self.update_predictions()
            for i in range(self.thrusters):
                self.update_predictions()

        elif self.status == "activated":
            if WorldPhysConstants().current_frame() - self.activation_timestamp > self.ttl:
                self.detonate(activated=True)

            if self.ship_detection_radius:
                potential_targets = [a for a in EntityIDGroupsController().get("radar_detectable")]
                prevented_targets = AlianceController().get_aliance(self.master_id)
                potential_targets = list(set(potential_targets)-set(prevented_targets))
                potential_targets = self.get_entities_ids_from_list_in_range(potential_targets, self.ship_detection_radius, False)

                if potential_targets:
                    if self.busters:
                        self.status = "locked"
                        self.target_id = random.choice(potential_targets)
                    else:
                        prevented_targets_in_damage_zone = self.get_entities_ids_from_list_in_range(prevented_targets, self.damage_zone_radius, False)
                        if not prevented_targets_in_damage_zone:
                            self.detonate(activated=True)

            if self.projectiles_detection_radius:
                potential_targets = ProjectileListController().get(self.master_id)
                prevented_targets = AlianceController().get_aliance(self.master_id)
                potential_targets = list(set(potential_targets)-set(prevented_targets))
                potential_targets = self.get_entities_ids_from_list_in_range(potential_targets, self.projectiles_detection_radius, False)

                if potential_targets:
                    if self.busters:
                        self.status = "locked"
                        self.target_id = random.choice(potential_targets)
                        self.velocities[2] = self.velocities[2]*self.thrusters
                        self.velocities[1] = self.velocities[1]*self.thrusters
                    else:
                        prevented_targets_in_damage_zone = self.get_entities_ids_from_list_in_range(prevented_targets, self.damage_zone_radius, False)
                        if not prevented_targets_in_damage_zone:
                            self.detonate(activated=True)

            self.update_predictions()
            for i in range(self.thrusters):
                self.update_predictions()

        elif self.status == "locked":
            if WorldPhysConstants().current_frame() - self.activation_timestamp > self.ttl:
                self.detonate(activated=True)

            acceleration = np.array([0, 0])
            if self.target_id in self.lBodies.bodies:
                target_pos = self.lBodies[self.target_id].get_position_np()
                vector = target_pos-self.get_position_np()
                acceleration = self.get_acceleration_gravity(
                    self.positions[1])+CalculationUtilites.get_projections(self.buster_acceleration, vector)
            self.velocities[2] = self.velocities[1] + \
                WorldPhysConstants().get_timestep()*acceleration
            self.update_predictions()

            reachable_bodies = [a for a in self.get_entities_ids_list_in_range(self.lBodies.bodies, self.detonation_radius, False)]
            prevented_targets = AlianceController().get_aliance(self.master_id)
            reachable_bodies = list(set(reachable_bodies)-set(prevented_targets))
            if reachable_bodies:
                prevented_targets_in_damage_zone = self.get_entities_ids_from_list_in_range(prevented_targets, self.damage_zone_radius, False)
                prevented_targets_in_detonation_radius = self.get_entities_ids_from_list_in_range(prevented_targets, self.detonation_radius, False)
                if not prevented_targets_in_damage_zone:
                    if not prevented_targets_in_detonation_radius:
                        self.detonate(activated=True)

    def detonate(self, activated=False):
        if activated:
            if self.explosion_radius:
                TriggerQueue().add("explosion", self.mark_id, {"danger_radius": self.explosion_radius,
                                                               "position": self.get_position_np(),
                                                               "master_id": self.master_id})
            if self.emp_radius:
                TriggerQueue().add("emp_explosion", self.mark_id, {"danger_radius": self.emp_radius,
                                                                   "position": self.get_position_np(),
                                                                   "master_id": self.master_id})
        else:
            TriggerQueue().add("explosion", self.mark_id, {"danger_radius": max(
                0.1, self.explosion_radius/4), "position": self.get_position_np(), "master_id": self.master_id})
        self.set_predictor_state(False)
        self.self_destruct()
        if self.is_decoy:
            EntityIDGroupsController().remove(self.mark_id)
        self.status = "destroyed"
