from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.projectiles.projectile_selector import ProjectileSelector
from modules.utils import Command

from modules.ship.systems.sm_core import BasicShipSystem
from modules.ship.shipPool import ShipPool_Singleton
from modules.utils import Command
from modules.utils import Command, CommandQueue, ConfigLoader


ship_level_configs = {
    1: {
        "engine_sm": 2,
        "launcher_sm": 1,
        "damage_sm": 1,
        "resources_sm": 0,
    },
    2: {
        "engine_sm": 3,
        "launcher_sm": 3,
        "damage_sm": 2,
        "resources_sm": 1,

    },
    3: {
        "engine_sm": 3,
        "launcher_sm": 6,
        "damage_sm": 3,
        "resources_sm": 2,
    }
}


class ResearchAndDevSystem(BasicShipSystem):
    def __init__(self, mark_id, NPC=False):
        super().__init__(mark_id, "RnD_sm")
        self.systems_upgrades = {}
        system_names = ["engine_sm", "launcher_sm",
                        "energy_sm", "radar_sm", "resources_sm"]
        if NPC:
            system_names = ["engine_sm", "launcher_sm",
                            "energy_sm", "radar_sm", "resources_sm", "damage_sm"]
        for system_name in system_names:
            upgrade_scale = [int(a) for a in ConfigLoader().get(
                f"sm_RnD.{system_name}", str).split()]
            self.systems_upgrades[system_name] = {
                'current_level': upgrade_scale[0],
                'maximal_level': upgrade_scale[1],
                'cost': upgrade_scale[2:]
            }

    def get_short_description(self):
        result = {}
        for system_name in self.systems_upgrades:
            curr = self.systems_upgrades[system_name]['current_level']
            max = self.systems_upgrades[system_name]['maximal_level']
            result[system_name] = f"{curr}/{max}"
        return result

    def upgrade_to_config_state(self):
        # , "resources_sm"]:
        for system_name in ["engine_sm", "launcher_sm", "energy_sm", "radar_sm", "resources_sm"]:
            upgrade_scale = [int(a) for a in ConfigLoader().get(
                f"sm_RnD.{system_name}", str).split()]
            current_level = upgrade_scale[0]
            self.set_upgrade_level(system_name, current_level)

    def set_upgrade_level(self, system_name, upgrade_level):
        try:
            system = self.get_system(system_name)
            level_delta = upgrade_level - system.upgrade_level
            if not system:
                print("ALERT")
            foo = system.upgrade
            if level_delta < 0:
                foo = system.downgrade
            for i in range(abs(level_delta)):
                foo()
            self.systems_upgrades[system_name]["current_level"] = upgrade_level
        except Exception as e:
            print("set_upgrade_level", system_name, upgrade_level, repr(e))

    def set_initial_ship_level(self):
        pass

    def get_ship_level_config(self, ship_level):
        return ship_level_configs[int(ship_level)]

    def set_ship_level(self, ship_level):
        ship_upgrade_config = self.get_ship_level_config(ship_level)
        for system_name in ship_upgrade_config:
            if system_name in self.systems_upgrades:
                self.set_upgrade_level(
                    system_name, ship_upgrade_config[system_name])

    def get_upgrade_level(self, system_name):
        return self.systems_upgrades[system_name]['current_level']

    def update_upgrades_state(self):
        for sm_name in ["engine_sm", "launcher_sm", "energy_sm", "radar_sm"]:
            self.systems_upgrades[sm_name]['current_level'] = self.get_system(
                sm_name).upgrade_level

    def next_step(self):
        pass

    def get_status(self):
        status = super().get_status()
        status["systems_upgrades"] = self.systems_upgrades
        return status

    def upgrade_system(self, system_name, free=False):

        # cant upgrade damaged systems
        if not free:
            if not self.get_system("damage_sm").can_be_upgraded(system_name):
                return

        resources_sm = self.get_system("resources_sm")
        system_state = self.systems_upgrades[system_name]
        upgrade_cost = system_state["cost"][system_state["current_level"]]
        if not free:
            success = resources_sm.spend_resource("metal", upgrade_cost)
            if not success:
                return
            self.get_system("damage_sm").inform_system_upgrade(system_name)
        system_obj = self.get_system(system_name)
        system_obj.upgrade()
        self.systems_upgrades[system_name]["current_level"] = system_obj.upgrade_level

    def downgrade_system(self, system_name):
        system_obj = self.get_system(system_name)
        system_obj.downgrade()

        self.systems_upgrades[system_name]["current_level"] = system_obj.upgrade_level
        self.get_system("resources_sm").trigger_launcher_update()

    def proceed_command(self, command: Command):
        super().proceed_command(command)
        params = command.get_params()
        match command.get_action():
            case 'upgrade_system':
                system_name = params["system"]
                self.upgrade_system(system_name)

            case "set_ship_level":
                level = params["value"]
                self.set_ship_level(int(level))

            case 'upgrade_system_admin':
                system_name = params["system"]
                self.upgrade_system(system_name, free=True)

            case "downgrade_system":
                system_name = params["system"]
                self.downgrade_system(system_name)
