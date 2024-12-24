from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.projectiles.projectile_selector import ProjectileSelector
from modules.utils import Command
from modules.physEngine.triggers.collector import TriggerQueue
from modules.ship.systems.sm_core import BasicShipSystem
from modules.ship.shipPool import ShipPool_Singleton
from modules.utils import Command
from modules.utils import Command, CommandQueue, ConfigLoader


class InteractionSystem(BasicShipSystem):
    def __init__(self, mark_id):
        super().__init__(mark_id, "interact_sm")
        self.lBodies = lBodyPool_Singleton()
        self.hp = 300
        self.interaction_radius = 30

    def proceed_command(self, command: Command):
        super().proceed_command(command)
        match command.get_action():
            case 'interact':
                self.interact(command.get_params()["target_id"])

    def get_status(self):
        status = super().get_status()
        status["interactable_objects"] = self.get_available_interactable_objects()
        return status

    def get_available_interactable_objects(self):
        if self.mark_id in self.lBodies.bodies:
            result = []
            available_bodies = self.lBodies[self.mark_id].get_interactble_objects_in_radius(
                self.interaction_radius)
            for body_idx in available_bodies:
                interact_descr = self.lBodies[body_idx].get_interact_description(
                )
                result.append((body_idx, interact_descr))
            return result
        return []

    def interact(self, target_id):
        TriggerQueue().add("interact", self.mark_id, {
            "target": target_id,
        })
        if hasattr(self.lBodies[target_id], "interact"):
            self.lBodies[target_id].interact(self.mark_id)
