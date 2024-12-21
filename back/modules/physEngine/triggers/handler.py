from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.zones.damage_zone import ae_ExplosionZone, ae_EMPZone
from modules.physEngine.event_system import GlobalEventSystem
from modules.physEngine.interactable_objects.container import ShipDebris, SpaceStationDebris
from modules.physEngine.triggers.collector import TriggerQueue
from modules.ship.shipPool import ShipPool_Singleton
from modules.physEngine.quests.quest_controller import QuestPointsController
from modules.ship.ship import NPC_Ship
from modules.ship.shipPool import ShipPool_Singleton
from modules.physEngine.aliances_controller import AlianceController


def get_entity_from_Pools(mark_id, pool_list):
    for pool in pool_list:
        entity = pool.get(mark_id)
        if entity:
            return entity
    return None


class TriggerHandler:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TriggerHandler, cls).__new__(cls)
            cls._instance.bodies_to_delete = []
            cls._instance.triggers_list = []
            cls._instance.lBodies = lBodyPool_Singleton()
            cls._instance.cShips = ShipPool_Singleton()
            cls._instance.EventSystem = GlobalEventSystem()

        return cls._instance

    def proceed_triggerSelfDestruct(self, initiator, params):
        self.lBodies.delete(initiator)

    def proceed_triggerSelfExplode(self, initiator, params):
        pos = self.lBodies[initiator].get_position()
        # self.lBodies.delete(initiator)
        expZone = ae_ExplosionZone(pos[0], pos[1], params['danger_radius'])
        self.lBodies.add(expZone)

    def proceed_triggerSelfEmpExplode(self, initiator, params):
        pos = self.lBodies[initiator].get_position()
        # self.lBodies.delete(initiator)
        expZone = ae_EMPZone(pos[0], pos[1], params['danger_radius'])
        self.lBodies.add(expZone)

    def proceed_triggerDamage2Target(self, initiator, params):
        mark_id = params['target']
        damage_value = params["damage_value"]
        damage_type = params["damage_type"]
        target = get_entity_from_Pools(mark_id, [self.cShips, self.lBodies])
        if not target:
            return
        if hasattr(target, "takes_damage"):
            target.takes_damage(damage_value, damage_type, initiator)

    def proceed_triggerAddResource(self, initiator, params):
        self.EventSystem.add_resource(
            params['target'], params["resource_name"], params["resource_amount"])

    def hBodyCollision(self, initiator, params):
        self.EventSystem.hBodyCollision(params['target'])

    def proceed_triggerExplosion(self, initiator, params):
        pos = params["position"]
        danger_radius = params['danger_radius']
        expZone = ae_ExplosionZone(
            pos[0], pos[1], danger_radius, params["master_id"])
        self.lBodies.add(expZone)

    def proceed_triggerEmpExplosion(self, initiator, params):
        pos = params["position"]
        danger_radius = params['danger_radius']
        expZone = ae_EMPZone(
            pos[0], pos[1], danger_radius, params["master_id"])
        self.lBodies.add(expZone)

    def ShipDefeat(self, initiator, params):
        position = self.lBodies[initiator].get_position_np()
        velocity = self.lBodies[initiator].velocities[1]

        ShipPool_Singleton().delete(initiator)
        debris = ShipDebris(position[0], position[1], initiator+"[debris]")
        debris.set_position_and_velocity(position, velocity)
        self.lBodies.add(debris)

    def QuantumShadowDefeat(self, initiator, params):
        position = self.lBodies[initiator].get_position_np()
        velocity = self.lBodies[initiator].velocities[1]
        self.lBodies.delete(initiator)
        debris = ShipDebris(position[0], position[1], initiator+"[debris]")
        debris.set_position_and_velocity(position, velocity)
        self.lBodies.add(debris)

        ShipPool_Singleton().delete(initiator)
        debris = ShipDebris(position[0], position[1], initiator+"[debris]")
        debris.set_position_and_velocity(position, velocity)
        self.lBodies.add(debris)

    def StationDefeat(self, initiator, params):
        position = self.lBodies[initiator].get_position_np()
        clockwise = self.lBodies[initiator].clockwise
        self.lBodies.delete(initiator)
        debris = SpaceStationDebris(
            position[0], position[1], initiator+"[debris]")
        debris.set_position_np_manual(position, clockwise)
        self.lBodies.add(debris)

    def StationDefence(self, initiator, params):
        position = self.lBodies[initiator].get_position_np()
        velocity = self.lBodies[initiator].get_velocity_np()
        defender = params["defender"]
        defender_level = params["defender_level"]
        npc_defender = NPC_Ship(position[0], position[1], defender)
        ShipPool_Singleton().spawn(npc_defender)
        self.lBodies[npc_defender.mark_id].set_position_and_velocity_init(
            position, velocity)
        self.lBodies[npc_defender.mark_id].stabilize_orbit()
        # self.cShips.ships[npc_defender.mark_id].set_level(defender_level)
        AlianceController().add(defender, initiator)

    def proceed_interaction(self, initiator, params):
        pass

    def clear_trigger_list(self):
        while not TriggerQueue().empty():
            trigger = TriggerQueue().get()

    def proceed_triggers_list(self):
        while not TriggerQueue().empty():
            trigger = TriggerQueue().get()
            trigger_type = trigger["type"]
            QuestPointsController().check_trigger(trigger)
            match trigger_type:
                case "selfdestruct":
                    self.proceed_triggerSelfDestruct(
                        trigger["initiator"], trigger["params"])

                case "explosion":
                    self.proceed_triggerExplosion(
                        trigger["initiator"], trigger["params"])

                case 'emp_explosion':
                    self.proceed_triggerEmpExplosion(
                        trigger["initiator"], trigger["params"])

                case "damage2target":
                    self.proceed_triggerDamage2Target(
                        trigger["initiator"], trigger["params"])

                case 'addresource':
                    self.proceed_triggerAddResource(
                        trigger["initiator"], trigger["params"])

                case 'hBodyCollision':
                    self.hBodyCollision(
                        trigger["initiator"], trigger["params"])

                case 'ship_defeat':
                    self.ShipDefeat(trigger["initiator"], trigger["params"])


                case 'quantumshadow_defeat':
                    self.QuantumShadowDefeat(trigger["initiator"], trigger["params"])

                case 'station_defeat':
                    self.StationDefeat(trigger["initiator"], trigger["params"])

                case 'activate_station_defence':
                    self.StationDefence(
                        trigger["initiator"], trigger["params"])

                case 'interact':
                    self.proceed_interaction(
                        trigger["initiator"], trigger["params"])

        self.triggers_list = []
