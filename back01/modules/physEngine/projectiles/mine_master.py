from datetime import timedelta, datetime
from modules.physEngine.projectiles.projectiles_core import pjtl_Basic, pjtl_Constructed, ProjectileListController
from modules.physEngine.core import CalculationUtilites
from modules.physEngine.basic_objects import lBody, CalculationUtilites, staticBody, dynamicBody
from modules.utils import ConfigLoader
import numpy as np
from modules.physEngine.basic_objects import lBody, CalculationUtilites, staticBody
from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController
from modules.physEngine.triggers.collector import TriggerQueue
from modules.physEngine.world_constants import WorldPhysConstants
import random


class Mine_type1(staticBody, dynamicBody):
    def __init__(self, x, y):
        staticBody.__init__(self)
        dynamicBody.__init__(self, x, y, "mine_type1_"+str(id(self)))
        self.set_marker_type("projectile")
        self.manual_init()
        self.master_id = "master_of_game"
        self.ship_detection_radius = ConfigLoader().get(
            "mines.mine_type1_detection_radius", float)
        self.explosion_radius = ConfigLoader().get(
            "mines.mine_type1_explosion_radius", float)
        self.boosters = False
        ProjectileListController().add(self.master_id, self.mark_id)

    def do_cache(self):
        super().do_cache()
        ProjectileListController().remove(self.master_id, self.mark_id)

    def do_uncache(self):
        super().do_uncache()
        ProjectileListController().add(self.master_id, self.mark_id)

    def __del__(self):
        ProjectileListController().remove(self.master_id, self.mark_id)

    def update_position(self):
        super().update_position()
        if not self.boosters:
            potential_targets = [
                a for a in EntityIDGroupsController().get("radar_detectable")]
            potential_targets = self.get_entities_ids_from_list_in_range(
                potential_targets, self.ship_detection_radius, False)
            if potential_targets:
                self.detonate(True)

    def get_description(self, requester_id=None):
        result = super().get_description(requester_id)
        result["master_id"] = self.master_id
        result['detection_radius'] = self.ship_detection_radius
        result["vel"] = self.get_velocity_np_static().tolist()
        return result

    def put_description(self, descr, forced=False):
        super().put_description(descr, forced)

    def detonate(self, activated=False):
        activation_radius = self.explosion_radius
        if not activated:
            activation_radius = max(0.1, self.explosion_radius/4)
        TriggerQueue().add("explosion", self.mark_id, {
            "danger_radius": activation_radius, "position": self.get_position_np(), "master_id": self.master_id})
        self.status = "destroyed"
        self.self_destruct()

    def self_destruct(self):
        TriggerQueue().add("selfdestruct", self.mark_id, {})
        self.status = "destroyed"
        ProjectileListController().remove(self.master_id, self.mark_id)

    def takes_damage(self, damage_value, damage_type="explosion", damage_source=None):
        match damage_type:
            case "explosion":
                self.detonate()
            case "emp":
                self.self_destruct()
            case 'collision':
                self.self_destruct()


class Mine_type2(Mine_type1):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.ship_detection_radius = ConfigLoader().get(
            "mines.mine_type2_detection_radius", float)
        self.explosion_radius = ConfigLoader().get(
            "mines.mine_type2_explosion_radius", float)
        self.detonation_radius = ConfigLoader().get(
            "mines.mine_type2_detonation_radius", float)
        self.status = "launched"
        self.target_id = None
        self.ttl = ConfigLoader().get("mines.mine_type2_ttl", float) * \
            WorldPhysConstants().get_ticks_per_second()
        self.buster_acceleration = ConfigLoader().get(
            "projectile_builder.buster_acceleration", float)*2
        self.boosters = True

    def update_position(self):
        if self.status != "locked":
            super().update_position()
            potential_targets = [
                a for a in EntityIDGroupsController().get("radar_detectable")]
            potential_targets = self.get_entities_ids_from_list_in_range(
                potential_targets, self.ship_detection_radius)
            if potential_targets:
                self.status = "locked"
                self.activation_timestamp = WorldPhysConstants().current_frame()
                self.target_id = random.choice(potential_targets)

        elif self.status == "locked":
            if WorldPhysConstants().current_frame() - self.activation_timestamp > self.ttl:
                self.detonate(activated=True)
            target_pos = self.lBodies[self.target_id].get_position_np()
            vector = target_pos-self.get_position_np()
            acceleration = self.get_acceleration_gravity(
                self.positions[1])+CalculationUtilites.get_projections(self.buster_acceleration, vector)
            self.velocities[2] = self.velocities[1] + \
                WorldPhysConstants().get_timestep()*acceleration
            self.update_predictions()

            reachable_bodies = self.get_entities_ids_list_in_range(
                self.lBodies.bodies, self.detonation_radius, False)
            if reachable_bodies:
                self.detonate(activated=True)
