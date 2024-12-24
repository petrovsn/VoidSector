from modules.physEngine.basic_objects import staticBody
import random
from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController
import numpy as np
from modules.physEngine.core import hBodyPool_Singleton, CalculationUtilites
from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.basic_objects import controllableBody, predictableBody
from modules.ship.shipPool import ShipPool_Singleton
from modules.physEngine.triggers.collector import TriggerQueue
from modules.physEngine.basic_objects import lBody
from modules.physEngine.world_constants import WorldPhysConstants

from dataclasses import dataclass
from datetime import datetime, timedelta

from modules.utils import ConfigLoader, PerformanceCollector, get_dt_ms


class destructableObject():
    def __init__(self, mark_id):
        self.mark_id = mark_id

    def self_destruct(self):
        TriggerQueue().add("selfdestruct", self.mark_id, {})
        self.status = "destroyed"


class ae_Ship(controllableBody):
    def __init__(self, x, y, mark_id=None, ship_subtype="ae_Ship"):
        super().__init__(x, y, mark_id)
        self.desctiption["type"] = ship_subtype
        if ship_subtype == "Kraken":
            self.desctiption["marker_type"] = ship_subtype
        self.set_predictor_state(True)
        self.close_scanrange = 150

        self.radar_levels = [
            (0.25, "activity"),
            (0.5, "active_ship"),
        ]

        if ship_subtype == "Kraken":
            self.radar_levels = [
                (2, "activity"),
            ]

        self.mapped_hbodies = set()
        self.last_radarscan_timestep = datetime.now()
        self.scan_marks = []
        self.distant_scanrange = 300
        self.distant_scanrange_arc = 10
        self.distant_scanrange_arc_p1 = 95
        self.distant_scanrange_arc_p2 = 85
        self.distant_scanrange_dir = 90


        if ship_subtype != "Kraken":
            EntityIDGroupsController().add(
                self.mark_id, ["radar_detectable", "id_labels_detectable", "is_ships"])
        else:
            EntityIDGroupsController().add(
                self.mark_id, ["is_ships"])

    def set_close_scanrange(self, value):
        self.close_scanrange = value

    def set_distant_scanrange(self, value):
        self.distant_scanrange = value

    def set_distant_scanparams(self, scan_distance, scan_arc, scan_dir):
        if scan_distance:
            self.distant_scanrange = scan_distance
        if scan_arc:
            self.distant_scanrange_arc = scan_arc
            self.distant_scanrange_arc_p1 = self.distant_scanrange_dir + \
                self.distant_scanrange_arc/2
            self.distant_scanrange_arc_p2 = self.distant_scanrange_dir - \
                self.distant_scanrange_arc/2

        if scan_dir:
            self.distant_scanrange_dir = scan_dir
            self.distant_scanrange_arc_p1 = self.distant_scanrange_dir + \
                self.distant_scanrange_arc/2
            self.distant_scanrange_arc_p2 = self.distant_scanrange_dir - \
                self.distant_scanrange_arc/2

    def get_interactble_objects_in_radius(self, interaction_radius):
        intact_objs = EntityIDGroupsController().get("interactable")
        bodies_ids = self.get_entities_ids_from_list_in_range(
            intact_objs, interaction_radius, False)
        return bodies_ids

    def get_hbodies_in_sight(self, close_radrange):
        bodies_idxs = self.hBodies.get_index_assosiated_idx_list(
            self.hbody_idx)
        result = {}
        all_body_descr = self.hBodies.get_bodies_description()
        for body_idx in bodies_idxs:
            result[body_idx] = all_body_descr[body_idx]
        return result

    def self_destruct(self):
        super().self_destruct()
        EntityIDGroupsController().remove(self.mark_id)

    # def update_position(self):
    # if self.predictor_is_active:
    #  self.upload_state_to_predictor()
    # #return super().update_position()

    def get_objects_in_sight(self, bodies_dict, close_radrange):
        # result = {}
        # bodies_ids = self.get_entities_ids_list_in_range(bodies_dict, close_radrange)
        # for body_id in bodies_ids:
        #  result[body_id]= bodies_dict[body_id].get_description(self.mark_id)
        result = self.lBodies.get_bodies_description()
        return result

    def get_viewfield(self):
        nav_data = {
            'mark_id': self.mark_id,
            "observer_pos": self.get_position(),
            'observer_radius': self.close_scanrange,
            "hBodies": self.get_objects_in_sight(self.hBodies.bodies),
            "lBodies": self.get_objects_in_sight(self.lBodies.bodies),
        }

        field_view = {
            "observer_id": self.mark_id,
            "nav_data": nav_data
        }
        return field_view

    def get_radar_mark_from_pos(self, tar_pos):
        tar_vector = tar_pos-self.get_position_np()
        tar_vector_norm = tar_vector/np.linalg.norm(tar_vector)
        tar_vector_norm = tar_vector_norm*self.close_scanrange
        marker_position = self.get_position_np()+tar_vector_norm
        return marker_position

    # returns only angle

    def get_hbodies_radar_marks(self, bodies_dict):
        marks = []

        bodies_ids = self.get_entities_in_sector(self.hBodies.bodies, self.hBodies.bodies,
                                                 self.distant_scanrange_arc_p1, self.distant_scanrange_arc_p2,
                                                 self.distant_scanrange, hard=True)
        for body_id in bodies_ids:
            mark = bodies_dict[body_id].get_radar_mark(
                self.get_position_np(), self.distant_scanrange, self.close_scanrange)
            if mark:
                tar_pos = bodies_dict[body_id].get_position_np()
                # marker_position = self.get_radar_mark_from_pos(tar_pos)
                marks.append((mark, tar_pos.tolist()))

        return marks

    def get_pole_mark(self):
        marks = []
        distance2pole = np.linalg.norm(self.get_position_np())
        if distance2pole > self.close_scanrange:
            marker_position = self.get_radar_mark_from_pos(np.zeros(2))
            marks.append(("pole", marker_position.tolist()))
        return marks

    def get_ships_activity_radar_marks(self):
        ships_ids_potential = EntityIDGroupsController().get("radar_detectable")
        # ships_ids = self.get_entities_ids_from_list_in_interval(ships_ids_potential, self.close_scanrange, distant_scanrange)
        ships_ids = self.get_entities_in_sector(ships_ids_potential, self.lBodies.bodies,
                                                self.distant_scanrange_arc_p1, self.distant_scanrange_arc_p2, self.distant_scanrange)

        marks = []
        for ship_mark in ships_ids:
            mark = self.lBodies[ship_mark].get_radar_mark(
                self.get_position_np(), self.distant_scanrange, self.close_scanrange)

            # если корабль обнаружен
            if mark:
                tar_pos = self.lBodies[ship_mark].get_position_np()
                if mark == "active_ship":
                    marker_position = tar_pos
                else:
                    tar_hbody = hBodyPool_Singleton().get_gravity_affected_body(tar_pos)
                    # если корабль в гравитационном колодце
                    if tar_hbody:
                        # если тело видимо
                        if self.check_entity_in_range(tar_hbody.mark_id, self.close_scanrange):
                            marker_position = tar_pos
                        else:
                            marker_position = tar_hbody.get_position_np()
                    else:
                        marker_position = tar_pos
                marks.append(("activity", marker_position.tolist()))
        return marks

    def get_radar_marks(self, radar_ping):

        if datetime.now()-self.last_radarscan_timestep > radar_ping:
            self.last_radarscan_timestep = datetime.now()
            scan_marks = self.get_hbodies_radar_marks(self.hBodies.bodies)
            scan_marks2 = self.get_ships_activity_radar_marks()
            self.scan_marks = scan_marks+scan_marks2
        return self.scan_marks+self.get_pole_mark()

    def get_visible_ships(self):
        visible_ships = self.get_entities_ids_from_list_in_range(
            EntityIDGroupsController().get("id_labels_detectable"), self.close_scanrange, False)

        return visible_ships

    def get_nav_data(self, radar_ping):

        hbodies_data = self.get_hbodies_in_sight(self.close_scanrange)
        lBodies_data = self.get_objects_in_sight(
            self.lBodies.bodies, self.close_scanrange)
        scan_marks = self.get_radar_marks(radar_ping)

        visible_ships = self.get_visible_ships()

        nav_data = {
            'mark_id': self.mark_id,
            "observer_pos": self.get_position(),
            'observer_radius': self.close_scanrange,
            "hBodies": hbodies_data,
            "lBodies": lBodies_data,
            "visible_ships": visible_ships,
        }

        nav_data["scan_marks"] = scan_marks
        return nav_data

    def get_description(self, requester_id=None):
        result = super().get_description(requester_id)
        result["close_scanrange"] = self.close_scanrange
        result["distant_scanrange"] = {
            "close_range": self.close_scanrange,
            "distant_range": self.distant_scanrange,
            "distant_dir": self.distant_scanrange_dir,
            "distant_arc": self.distant_scanrange_arc
        }

        """if (requester_id==None) or (requester_id==self.mark_id):
                                                result["close_scanrange"] = self.close_scanrange
                                                result["distant_scanrange"] = self.distant_scanrange
                                if requester_id:
                                                if requester_id!=self.mark_id:
                                                                result["alias"] = "enemy"""

        return result


class SpaceStation(staticBody, lBody):
    def __init__(self, x, y, mark_id=None):
        staticBody.__init__(self)
        self.manual_init(False)
        lBody.__init__(self, x, y, mark_id)
        self.stabilize_orbit()
        self.radar_levels = [
            (0.1, "activity"),
            (0.3, "active_ship"),
        ]
        EntityIDGroupsController().add(self.mark_id, [
            "radar_detectable", "id_labels_detectable", "interactable", "stationary_orbit", "is_station"])
        self.hp = 1000
        self.max_hp = 1000

    def get_interact_description(self):
        return "interact"

    def get_description(self, requester_id=None):
        result = super().get_description(requester_id)
        result["vel"] = self.get_velocity_np_static().tolist()
        return result

    def put_description(self, descr, forced):
        super().put_description(descr, forced)
        if "pos" in descr and "vel" in descr:
            self.set_position_and_velocity_init(
                np.array(descr["pos"]), np.array(descr["vel"]))
            return
        if "vel" in descr:
            self.set_velocity(np.array(descr["vel"]))
        if "pos" in descr:
            self.set_position_np_manual(np.array(descr["pos"]))

    def get_velocity_np(self):
        return self.get_velocity_np_static()

    def get_short_description(self):
        return {
            "hp": f"{round(self.hp)}/{self.max_hp}",
            "pos": self.get_position()
        }

    def get_surrounding_hbodies_ids(self):
        return [self.hbody_idx]

    def self_destroy(self):
        EntityIDGroupsController().remove(self.mark_id)
        TriggerQueue().add("station_defeat", self.mark_id, {})
        TriggerQueue().add("ship_defeat", self.mark_id+"[DEF]", {})

    def activate_station_defence(self):
        defender_id = self.mark_id+"[DEF]"
        defender_level = 2
        if self.mark_id == "Selena":
            defender_id = "Galileo"
        if self.mark_id == "Medusa":
            if self.mark_id+"[DEF]" in self.lBodies.bodies:
                defender_id = "Otto"
                defender_level = 3
        TriggerQueue().add("activate_station_defence", self.mark_id, {
            "defender": defender_id, "defender_level": defender_level})

    def takes_damage(self, damage_value, damage_type="explosion", damage_source=None):
        self.hp = self.hp-damage_value
        if self.hp < 0:
            self.self_destroy()

    def interact(self, interactor_id):
        pass


class QuantumShadow(lBody):
    def __init__(self, x, y, mark_id=None):
        super().__init__(x, y, "VanEick")
        self.marker_type = "QuantumShadow"
        self.stabilize_orbit()
        self.destability_radius = 200
        self.radar_levels = [
            (0.25, "activity"),
            (0.5, "active_ship"),
        ]
        EntityIDGroupsController().add(
            self.mark_id, ["radar_detectable", "id_labels_detectable"])

        self.wormhole_position = self.hBodies["WormHole"].get_position_np()
        self.potential_start_points = self.get_potential_start_points()
        self.mode = 'phase1'
        self.hp = 100


    def get_description(self, requester_id=None):
        res = super().get_description(requester_id)
        res["mode"] = self.mode
        return res
    
    def put_description(self, descr, forced):
        super().put_description(descr, forced)
        if "mode" in descr:
            self.mode = descr["mode"]

    def get_potential_start_points(self):
        result = []
        for body_idx in self.hBodies.bodies:
            distance = np.linalg.norm(
                self.wormhole_position - self.hBodies[body_idx].get_position_np())
            if 1200 < distance < 1400:
                result.append(body_idx)
        return result

    def quantum_jump(self):
        if self.hbody_idx != "WormHole":
            potential_new_hbodies = self.hBodies.get_index_assosiated_idx_list(
                self.hbody_idx)
            current_distance = np.linalg.norm(
                self.wormhole_position - self.get_position_np())
            new_hbody_idx = self.hbody_idx
            for body_idx in potential_new_hbodies:
                tmp_distance = np.linalg.norm(
                    self.wormhole_position - self.hBodies[body_idx].get_position_np())
                if tmp_distance < current_distance:
                    current_distance = tmp_distance
                    new_hbody_idx = body_idx

        else:
            new_hbody_idx = random.choice(self.potential_start_points)

        position = self.hBodies[new_hbody_idx].get_random_stable_point()
        self.set_position_np_manual(position, random.choice([True, False]))

    def update_position(self):
        super().update_position()
        if self.mode == 'phase1':
            reachable_bodies = self.get_entities_ids_from_list_in_range(
                EntityIDGroupsController().get("is_ships"), self.destability_radius, False)
            if reachable_bodies:
                self.quantum_jump()

    def set_phase(self, phase):
        self.mode = phase
        if self.mode == 'phase2':
            position = self.hBodies["WormHole"].get_random_stable_point()
            self.set_position_np_manual(position, random.choice([True, False]))

    def takes_damage(self, damage_value, damage_type="explosion", damage_source=None):
        if self.mode == 'phase2':
            self.hp = self.hp-damage_value
            if self.hp < 0:
                self.self_destroy()


    def self_destroy(self):
        TriggerQueue().add("quantumshadow_defeat", self.mark_id, {})
        EntityIDGroupsController().remove(self.mark_id)

