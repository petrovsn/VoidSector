
from modules.physEngine.core import hBody, CalculationUtilites
from modules.physEngine.active_objects import QuantumShadow, SpaceStation
from modules.physEngine.hb_entities import ResourceAsteroid, WormHole
from modules.physEngine.interactable_objects.container import intact_Container, ShipDebris, SpaceStationDebris
from modules.physEngine.projectiles.mine import pjtl_Mine
from modules.physEngine.projectiles.mine_master import Mine_type1, Mine_type2
from modules.ship.ship import Ship, NPC_Ship, NPC_Kraken
from modules.ship.shipPool import ShipPool_Singleton
from modules.utils import ConfigLoader, Command
from modules.physEngine.core import lBodyPool_Singleton, hBodyPool_Singleton
from modules.physEngine.predictor import TrajectoryPredictor_controller
from modules.physEngine.zones.meteors_zone import MeteorsCloud
from modules.physEngine.solar_flare.solar_flar_activator import SolarFlareActivator
import numpy as np
from random import randint
import json
import random
import copy


class MapEditor:
    def __init__(self):
        self.hBodies = hBodyPool_Singleton()
        self.cShips = ShipPool_Singleton()
        self.lBodies = lBodyPool_Singleton()
        self.grid_step = ConfigLoader().get("world.map_step", float)
        self.selected_body_id = None
        self.spawner = EntitySpawner()

        self.spawn_positions = {

        }

    # related commands: "create_hbody", "select_hbody",
    #     "create_lbody", "select_lbody",
    #     "unselect", cursor_move",
    #     "save",

    def proceed_command(self, command: Command):
        try:
            action = command.get_action()
            match action:
                case "brush_cache": self.brush_cache(command.get_params())
                case "brush_uncache": self.brush_uncache(command.get_params())
                case "brush_create": self.brush_create(command.get_params())
                case "brush_delete": self.brush_delete(command.get_params())
                case "brush_edit_weight": self.brush_edit_weight(command.get_params())
                case "brush_spawn_obstacles": self.brush_spawn_obstacles(command.get_params())
                case "brush_delete_obstacles": self.brush_delete_obstacles(command.get_params())
                case "brush_select_body": self.brush_select_body(command.get_params())
                case "select_body": self.select_body(command.get_params()["mark_id"])
                case "cursor_move": self.cursor_move(command.get_params()["position"], command.get_params()["clockwise"])
                case 'change_body': self.change_body(command.get_params()["descr"]["mark_id"], command.get_params()["descr"], command.get_params()["forced"])
                case 'spawn_body': self.spawn_body(command.get_params()["entity_type"], command.get_params())
                case 'copy_body': self.copy_body(command.get_params()["mark_id"])
                case 'delete_body': self.delete_body(command.get_params()["mark_id"])
                case 'save_map': self.save_map(command.get_params()["map_name"])
                case 'save_main_ship': self.save_main_ship(command.get_params()["screen_name"])
        except Exception as e:
            print(repr(e))

    def brush_select_body(self, brush_params):
        if self.selected_body_id:
            self.select_body(None)
            return
        brush_radius = brush_params["radius"]

        brush_position = brush_params["position"]
        brush_position_np = np.array([brush_position[0], brush_position[1]])

        selected_idx = None
        distance = 9000000000000000000000000000000
        for body_idx in self.brush_get_hbodies2proceed(brush_params):
            distance2body = self.hBodies.bodies[body_idx].get_distance2position(
                brush_position_np)
            if distance2body < distance:
                distance = distance2body
                selected_idx = body_idx
        if not selected_idx:
            return
        self.select_body(selected_idx)

    def brush_edit_weight(self,brush_params ):
        
        for body_idx in self.brush_get_hbodies2proceed(brush_params):
            new_mass = random.randint(brush_params["min_weight"], brush_params["max_weight"])
            self.hBodies.bodies[body_idx].set_mass(new_mass)
        TrajectoryPredictor_controller().update_hbodies_location()

    def brush_get_hbodies2proceed(self, brush_params):
        brush_radius = brush_params["radius"]

        brush_position = brush_params["position"]
        brush_position_np = np.array([brush_position[0], brush_position[1]])

        body_idx_to_proceed = []
        for body_idx in self.hBodies.bodies:
            if self.hBodies.bodies[body_idx].get_distance2position(brush_position_np) < brush_radius:
                body_idx_to_proceed.append(body_idx)
        return body_idx_to_proceed

    def brush_get_lbodies2proceed(self, brush_params):
        brush_radius = brush_params["radius"]

        brush_position = brush_params["position"]
        brush_position_np = np.array([brush_position[0], brush_position[1]])

        body_idx_to_proceed = []
        for body_idx in self.lBodies.bodies:
            if self.lBodies.bodies[body_idx].get_distance2position(brush_position_np) < brush_radius:
                body_idx_to_proceed.append(body_idx)
        return body_idx_to_proceed

    def brush_cache(self, brush_params):
        bodies = self.brush_get_hbodies2proceed(brush_params)
        for body_idx in bodies:
            self.hBodies.bodies[body_idx].cache_static_lbodies(True)

    def brush_uncache(self, brush_params):
        bodies = self.brush_get_hbodies2proceed(brush_params)
        for body_idx in bodies:
            self.hBodies.bodies[body_idx].uncache_static_lbodies(True)

    def brush_create(self, brush_params):
        brush_position = brush_params["position"]
        brush_position_np = np.array([brush_position[0], brush_position[1]])

        # получить точку, до границы которой ближе всего
        body_idx_to_start = None
        distance2brush_position = 99999999999
        for body_idx in self.hBodies.bodies:
            tmp_distance = self.hBodies.bodies[body_idx].get_distance2position_from_border(
                brush_position_np)
            if tmp_distance < distance2brush_position:
                body_idx_to_start = body_idx
                distance2brush_position = tmp_distance

        # запустить генерацию
        new_radius = random.randint(
            brush_params["min_size"], brush_params["max_size"])
        new_mass = random.randint(
            brush_params["min_weight"], brush_params["max_weight"])
        cnter = 0
        while (not (self.brush_check_condition(body_idx_to_start, brush_position_np))) and (cnter < 20):

            success, body_idx_to_start = self.brush_create_next(
                body_idx_to_start, brush_position_np, new_radius, new_mass)
            if success:
                if brush_params["closer"]:
                    new_radius = brush_params["max_size"]
                else:
                    new_radius = random.randint(
                        brush_params["min_size"], brush_params["max_size"])
                new_mass = random.randint(
                    brush_params["min_weight"], brush_params["max_weight"])
                cnter = cnter+1
            else:
                new_radius = new_radius*0.75
                if new_radius < brush_params["min_size"]:
                    return

    def brush_check_condition(self, last_created_body_idx, brush_position):
        return self.hBodies.bodies[last_created_body_idx].is_position_in_gravity_well(brush_position)

    def brush_create_next(self, ancor_body_idx, brush_position_np, new_radius, new_mass):
        # получаем всех соседей

        neighbours = self.hBodies.get_index_assosiated_idx_list(ancor_body_idx)
        neighbours.remove(ancor_body_idx)

        # считаем все возможные точки пересечения, для каждой находим расстояние до кисти
        possible_points = []
        pos1 = self.hBodies[ancor_body_idx].get_position_np()
        rad1 = self.hBodies[ancor_body_idx].gravity_well_radius+new_radius+2
        for neigh_body_idx in neighbours:
            pos2 = self.hBodies[neigh_body_idx].get_position_np()
            rad2 = self.hBodies[neigh_body_idx].gravity_well_radius+new_radius+2
            points = CalculationUtilites.get_intersection_for_2_circles(
                pos1, rad1, pos2, rad2)
            if points:
                for point in points:
                    distance2brush = np.linalg.norm(point - brush_position_np)
                    possible_points.append((point, distance2brush))

        # отсортировать по удалению от кисти
        possible_points = sorted(possible_points, key=lambda point: point[1])

        # для каждой потенциальной позиции чекаем проверку на пересечения с другими телами
        for point in possible_points:
            if self.brush_body_can_be_placed(point[0], new_radius):
                new_hbody = hBody(point[0][0], point[0]
                                  [1], new_radius, new_mass)
                self.hBodies.add(new_hbody)
                return True, new_hbody.mark_id
        return False, ancor_body_idx

    def brush_body_can_be_placed(self, position, new_radius):
        for body_idx in self.hBodies.bodies:
            tmp_distance = self.hBodies.bodies[body_idx].get_distance2position_from_border(
                position)
            if tmp_distance <= new_radius:
                return False
        return True

    def brush_delete(self, brush_params):
        body_idx_to_del = self.brush_get_hbodies2proceed(brush_params)
        for body_idx in body_idx_to_del:
            self.hBodies.delete(body_idx)

    def copy_body(self, mark_usi):
        body = self.hBodies[mark_usi]
        body_descr = body.get_description()
        body_descr["mark_id"] = None
        mark_id = self.spawner.spawn(body_descr["type"], body_descr)
        self.select_body(mark_id)
        self.hBodies[mark_id].put_description(body_descr)

    def brush_spawn_obstacles(self, brush_params):
        body_idx_to_proceed = self.brush_get_hbodies2proceed(brush_params)

        obstacles_min_count = brush_params["obstacles_min_count"]
        obstacles_max_count = brush_params["obstacles_max_count"]
        # (from 0 to 100)
        obstacles_probability = brush_params["obstacles_probability"]
        obstacles_type = brush_params["obstacles_type"]
        for body_idx in body_idx_to_proceed:
            random_chance = random.randint(0, 100)
            if random_chance < obstacles_probability:
                obstacles_count = random.randint(
                    obstacles_min_count, obstacles_max_count)
                self.brush_spawn_obstacles_to_hbody(
                    body_idx, obstacles_count, obstacles_type)

    def brush_spawn_obstacles_to_hbody(self, hbody_idx, obstacles_count, obstacles_type):
        for i in range(obstacles_count):
            radius = random.randint(
                50, int(self.hBodies[hbody_idx].gravity_well_radius*0.9))
            distance = np.array([radius, 0])
            angle = random.randint(0, 360)
            position = self.hBodies[hbody_idx].get_position_np(
            )+CalculationUtilites.rotate_vector(distance, angle)
            obstacle_body = None
            if obstacles_type == "Mine_type1/Mine_type2":
                obstacles_type = random.choice(obstacles_type.split('/'))

            if obstacles_type == "MeteorsCloud":
                obstacle_body = MeteorsCloud(position[0], position[1])

            if obstacles_type == "Mine_type1":
                obstacle_body = Mine_type1(position[0], position[1])
                obstacle_body.set_position_np_manual(
                    position, random.choice([True, False]))

            if obstacles_type == "Mine_type2":
                obstacle_body = Mine_type2(position[0], position[1])
                obstacle_body.set_position_np_manual(
                    position, random.choice([True, False]))
            self.lBodies.add(obstacle_body)

    def brush_delete_obstacles(self, brush_params):
        bodies = self.brush_get_lbodies2proceed(brush_params)
        for body_idx in bodies:
            lBodyPool_Singleton().delete(body_idx)

    # def brush_delete_obstacle(self, brush_params):
    #   pass

    def spawn_body(self, entity_type, entity_params):
        mark_id = self.spawner.spawn(entity_type, entity_params)
        self.select_body(mark_id)

    def delete_body(self, mark_id):
        self.cShips.delete(mark_id)
        self.lBodies.delete(mark_id)
        self.hBodies.delete(mark_id)

    def get_related_body_pool(self, mark_id):
        bodies = self.lBodies
        if mark_id in self.hBodies.bodies:
            bodies = self.hBodies
        return bodies

    def select_body(self, mark_id):
        if not mark_id:  # т.е. unselect
            selected_ship = self.cShips.get(self.selected_body_id)
            if selected_ship:
                selected_ship_state = selected_ship.get_viewfield()[
                    "state_data"]
                selected_ship_position = self.lBodies.get(
                    self.selected_body_id).get_description()["pos"]

                selected_ship_description = {
                    "type": str(selected_ship.__class__.__name__),
                    "state": selected_ship_state,
                    "pos": selected_ship_position
                }

                self.spawn_positions[self.selected_body_id] = selected_ship_description
            selected_body = self.hBodies.get(self.selected_body_id)
            if selected_body:
                TrajectoryPredictor_controller().update_hbodies_location()
                self.hBodies.generate_index_for_single_body(
                    self.selected_body_id)
        

        if self.selected_body_id: #if already selected smth
            if self.lBodies.if_body_exists(self.selected_body_id):
                self.lBodies[self.selected_body_id].set_edit_mode(False)
        
        if mark_id: #select
            if self.lBodies.if_body_exists(mark_id):
                self.lBodies[mark_id].set_edit_mode(True)

        self.selected_body_id = mark_id

    def change_body(self, mark_id, new_description, forced):
        bodies = self.get_related_body_pool(mark_id)

        bodies[mark_id].put_description(new_description, forced)

    def cursor_move(self, position, clockwise):
        if self.selected_body_id:
            bodies = self.get_related_body_pool(self.selected_body_id)
            bodies.bodies[self.selected_body_id].set_position_np_manual(
                np.array(position), clockwise)
        pass

    def save_map(self, map_name):
        self.hBodies.uncache_static_lbodies()
        hbodies_description = self.hBodies.get_bodies_description()
        # self.lBodies.update_description()
        self.lBodies.iter_loop()
        lbodies_description = self.lBodies.get_bodies_description()
        ships_description = self.cShips.get_ships_description()
        sector_map = {
            "hBodies": hbodies_description,
            "lBodies": lbodies_description,
            "cShips": ships_description,
            "SolarFlareActivator": SolarFlareActivator().get_description()
        }
        json.dump(sector_map, open(f"maps/{map_name}.json", 'w'))
        self.hBodies.cache_static_lbodies()

    def save_main_ship(self, screen_name):
        main_ship_id = ConfigLoader().get_main_ship_id()
        if main_ship_id in self.lBodies.bodies:
            main_ship_description = self.cShips.ships[main_ship_id].get_description()
            json.dump(main_ship_description, open(f"ship_screens/{screen_name}.json", 'w'))



class EntitySpawner:
    def __init__(self):
        self.hBodies = hBodyPool_Singleton()
        self.cShips = ShipPool_Singleton()
        self.lBodies = lBodyPool_Singleton()
        pass

    def spawn(self, entity_type, entity_params):
        spawn_position = 999999
        mark_id = entity_params["mark_id"] if entity_params["mark_id"] else str(
            randint(0, 10000000))
        match entity_type:
            case "ae_Ship":
                mark_id = "aeShip_"+str(randint(0, 10000000))
                if ConfigLoader().get_main_ship_id() not in self.lBodies.bodies:
                    mark_id = ConfigLoader().get_main_ship_id()
                ship1 = Ship(spawn_position, spawn_position, mark_id=mark_id)
                mark_id = ship1.mark_id
                self.cShips.spawn(ship1)
            case 'NPC_Ship':
                if not mark_id:
                    mark_id = "aeShip_"+str(randint(0, 10000000))
                ship1 = NPC_Ship(
                    spawn_position, spawn_position, mark_id=mark_id)
                mark_id = ship1.mark_id
                self.cShips.spawn(ship1)

            case 'NPC_Kraken':
                mark_id = 'Kraken'
                ship1 = NPC_Kraken(
                    spawn_position, spawn_position, mark_id=mark_id)
                mark_id = ship1.mark_id
                self.cShips.spawn(ship1)

            case 'hBody':
                body = hBody(spawn_position, spawn_position,
                             ConfigLoader().get("world.map_step", float))
                body.mark_id = mark_id
                self.hBodies.add(body)
            case 'ResourceAsteroid':
                body = ResourceAsteroid(
                    spawn_position, spawn_position, ConfigLoader().get("world.map_step", float))
                body.mark_id = mark_id
                self.hBodies.add(body)
            case "pjtl_Mine":
                body = pjtl_Mine("admin")
                mark_id = body.mark_id
                self.lBodies.add(body)
            case 'intact_Container':
                body = intact_Container(-9000, 9000)
                mark_id = body.mark_id
                self.lBodies.add(body)
            case 'WormHole':
                body = WormHole(spawn_position, spawn_position,
                                ConfigLoader().get("world.map_step", float))
                mark_id = body.mark_id
                self.hBodies.add(body)
            case "ShipDebris":
                body = ShipDebris(spawn_position, spawn_position, mark_id)
                mark_id = body.mark_id
                self.lBodies.add(body)

            case 'MeteorsCloud':
                body = MeteorsCloud(spawn_position, spawn_position)
                mark_id = body.mark_id
                self.lBodies.add(body)

            case 'QuantumShadow':
                body = QuantumShadow(spawn_position, spawn_position)
                mark_id = body.mark_id
                self.lBodies.add(body)

            case 'SpaceStation':
                body = SpaceStation(spawn_position, spawn_position, mark_id)
                mark_id = body.mark_id
                self.lBodies.add(body)

            case 'SpaceStationDebris':
                body = SpaceStationDebris(
                    spawn_position, spawn_position, mark_id)
                mark_id = body.mark_id
                self.lBodies.add(body)

            case 'Mine_type1':
                body = Mine_type1(spawn_position, spawn_position)
                mark_id = body.mark_id
                self.lBodies.add(body)

            case 'Mine_type2':
                body = Mine_type2(spawn_position, spawn_position)
                mark_id = body.mark_id
                self.lBodies.add(body)

        return mark_id
