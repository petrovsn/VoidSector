from modules.ship.systems.sm_medicine import MedicineSystem
from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.projectiles.projectile_selector import ProjectileSelector
from modules.utils import Command

from modules.ship.systems.sm_core import BasicShipSystem, GlobalShipSystemController

from modules.ship.shipPool import ShipPool_Singleton
from modules.utils import Command
from modules.utils import Command, CommandQueue, ConfigLoader
from modules.physEngine.triggers.collector import TriggerQueue


import random
import math


class RepairTeam:
    def __init__(self, mark_id, name):
        self.mark_id = mark_id
        self.name = name
        self.state = "idle"

        # экипаж в комане
        self.crew = 10
        self.max_crew = 10

        # количество материалов. Хватает на одну полную починку.
        self.loadout = 100
        self.max_loadout = 100

        full_module_recovery_time_sec = ConfigLoader().get("sm_damage.full_module_recovery_time_sec", float)

        self.repair_step = WorldPhysConstants().get_onetick_step(100, full_module_recovery_time_sec)
        self.recovery_step = WorldPhysConstants().get_onetick_step(100, 60)

        self._resources_sm = None

        # 1 юнит экипажа стоит где-то 50 единиц металла
        #self.damage_penalty = 1/50
        self.max_unit_hp = 30
        self.current_unit_hp = 30

    @property
    def resources_sm(self):
        if not self._resources_sm:
            self.resources_sm = GlobalShipSystemController().get(self.mark_id, "resources_sm")
        return self._resources_sm

    @resources_sm.setter
    def resources_sm(self, value):
        self._resources_sm = value

    """@property
    def crew(self):
        return self._crew

    @crew.setter
    def crew(self, value):
        self._crew = value
        self.crew_out = math.ceil(self._crew)"""

    def get_state(self):
        return {
            "name": self.name,
            "crew": self.crew,
            "loadout": self.loadout/self.max_loadout,
            "state": self.state
        }

    def set_state(self, state):
        self.state = state

    def get_repair_step(self):
        if self.loadout == 0:
            return 0
        repair_step = (self.crew/self.max_crew)*self.repair_step
        self.loadout = max(self.loadout-self.repair_step, 0)
        return repair_step

    def next_step(self):
        if self.state == "idle":
            if self.loadout < self.max_loadout:
                success = self.resources_sm.spend_resource(
                    "metal", self.recovery_step)
                if success:
                    self.loadout = min(
                        self.max_loadout, self.loadout+self.recovery_step)

    def add_crew_to_team(self):
        if self.crew < self.max_crew:
            self.crew = self.crew+1
            return True
        return False
    
    def set_crew_amount(self, value):
        if value<self.max_crew:
            self.crew = value

    def remove_crew_from_team(self):
        if self.crew > 0:
            self.crew = self.crew-1
            return True
        return False


    # логика такова: self.current_unit_hp - хиты крайнего юнита в очереди
    # как только они снижаются до 0, юнит считается раненым и удаляется из команды
    def takes_damage(self, damage):
        wounded_units = 0
        while damage>0:
            tmp_new_hp = self.current_unit_hp-damage
            damage = damage-self.current_unit_hp
            self.current_unit_hp = tmp_new_hp
            if self.current_unit_hp<=0:
                if self.crew:
                    wounded_units = wounded_units+1
                self.current_unit_hp = self.max_unit_hp
        self.crew = max(0, self.crew-wounded_units)
        return wounded_units
        

    def get_description(self):
        return {
            "name": self.name,
            "crew": self.crew,
            "loadout": self.loadout,
            "state": self.state
        }

    def put_description(self, descr):
        self.name = descr["name"]
        self.crew = descr["crew"]
        self.loadout = descr["loadout"]
        self.state = descr["state"]


class CrewSystem(BasicShipSystem):
    def __init__(self, mark_id):
        super().__init__(mark_id, "crew_sm")
        self.free_crew = 0
        self.total_crew = 0

        self.teams = {}
        for name in ['smith', 'johnson', 'wake', 'sharp']:
            self.teams[name] = RepairTeam(self.mark_id, name)
            self.total_crew = self.total_crew+10

        self.system_names = ["engine_sm", "launcher_sm",
                             "energy_sm", "radar_sm", "resources_sm"]
        self.system_status = {}
        for sm_name in self.system_names:
            self.system_status[sm_name] = None

        self.crew_acceleration = ConfigLoader().get("sm_crew.crew_acceleration", float)

        self._med_sm: MedicineSystem = None

    @property
    def med_sm(self):
        if not self._med_sm:
            self._med_sm = GlobalShipSystemController().get(self.mark_id, "med_sm")
        return self._med_sm

    def get_description(self):
        result = super().get_description()
        result["free_crew"] = self.free_crew
        result["total_crew"] = self.total_crew
        result["system_status"] = self.system_status
        result["teams"] = {
            team_name: self.teams[team_name].get_description() for team_name in self.teams
        }
        return result

    def put_description(self, descr):
        super().put_description(descr)
        self.free_crew = descr["free_crew"]
        self.total_crew = descr["total_crew"]
        self.system_status = descr["system_status"]
        for team_name in descr["teams"]:
            team_descr = descr["teams"][team_name]
            self.teams[team_name].put_description(team_descr)

    @med_sm.setter
    def med_sm(self, value):
        self._med_sm = value

    def get_status(self):
        result = super().get_status()
        teams = {}
        for rteam_name, rteam_obj in self.teams.items():
            teams[rteam_name] = rteam_obj.get_state()
        result["teams"] = teams
        result["systems"] = self.system_status
        result["total_crew"] = self.total_crew
        result["free_crew"] = self.free_crew
        return result

    def next_step(self):
        super().next_step()
        for team_name in self.teams:
            self.teams[team_name].next_step()
        # ship defeat

    def proceed_command(self, cmd: Command):
        action = cmd.get_action()
        params = cmd.get_params()
        match action:
            case "create_new_team":
                self.create_new_team(params["team_name"])
            case "add_crew_to_team":
                self.add_crew_to_team(params["team_name"])

            case "add_unit_to_crew":
                self.free_crew = self.free_crew+params['value']
                self.total_crew = self.total_crew+params['value']

            case "remove_crew_from_team":
                self.remove_crew_from_team(cmd.get_params()["team_name"])

            case "assign_team":
                params = cmd.get_params()
                self.assign_team(params["team_name"], params["sm_name"])

    def get_density(self):
        pass

    def takes_damage2system(self, sm_name, damage):
        assigned_team = self.system_status[sm_name]
        if assigned_team:
            wounded_units:int = self.teams[assigned_team].takes_damage(damage)
            if wounded_units:
                not_placed_in_hospital = self.med_sm.add_unit_to_hospital(wounded_units)
                self.total_crew = self.total_crew-not_placed_in_hospital


    def get_total_crew_number(self):
        return sum([a[1].crew for a in self.teams.items()])

    def assign_team(self, team_name, sm_name):
        assigned_team = self.system_status[sm_name]
        if assigned_team:
            self.teams[assigned_team].set_state("idle")
            self.system_status[sm_name] = None

        if team_name:
            current_state = self.teams[team_name].state
            if current_state != "idle":
                self.system_status[current_state] = None
            self.teams[team_name].set_state(sm_name)
            self.system_status[sm_name] = team_name

    def get_crew_acceleration_in_system(self, sm_name):
        team_name = self.system_status[sm_name]
        if team_name:
            return self.crew_acceleration*self.teams[team_name].crew/self.teams[team_name].max_crew
        return 0
    
    def create_new_team(self, team_name):
        self.teams[team_name] = RepairTeam(self.mark_id, team_name)
        self.teams[team_name].set_crew_amount(0)

    def add_crew_to_team(self, team_name):
        if self.free_crew > 0:
            result = self.teams[team_name].add_crew_to_team()
            if result:
                self.free_crew = self.free_crew-1

    def add_unit_to_crew(self, value):
        #self.total_crew = self.total_crew+value
        self.free_crew = self.free_crew + value

    def remove_crew_from_team(self, team_name):
        result = self.teams[team_name].remove_crew_from_team()
        if result:
            self.free_crew = self.free_crew+1

    def get_repair_step(self, sm_name):
        if not self.system_status[sm_name]:
            return 0
        repair_hp = self.teams[self.system_status[sm_name]].get_repair_step()
        return repair_hp


class DamageSystem(BasicShipSystem):
    def __init__(self, mark_id):
        super().__init__(mark_id, "damage_sm")
        # basic
        self.systems_hp = {}
        self.hp_level_step = 100
        self.system_names = ["engine_sm", "launcher_sm",
                             "energy_sm", "radar_sm", "resources_sm"]
        for sm_name in self.system_names:
            self.systems_hp[sm_name] = {
                'current_hp': self.hp_level_step,
                "max_hp": self.hp_level_step,
            }

        # energy overload
        energyoverlock_damage_per_sec = ConfigLoader().get(
            "damage.energyoverlock_damage_per_sec", float)
        self.energyoverlock_damage_per_tick = WorldPhysConstants(
        ).get_onetick_step(energyoverlock_damage_per_sec, 1)
        self.overloaded = {}

        # taking damage marker
        self.is_taking_damage = False
        self.taking_damage_showoff_time = WorldPhysConstants().get_ticks_in_seconds(1)
        self.last_taking_damage_timestamp = WorldPhysConstants().current_frame()

        # crew link
        self._crew_sm = None

        # TODO delete later
        self.tmp_damage_log = {}

    @property
    def crew_sm(self):
        if not self._crew_sm:
            self.crew_sm = GlobalShipSystemController().get(self.mark_id, "crew_sm")
        return self._crew_sm

    @crew_sm.setter
    def crew_sm(self, value):
        self._crew_sm = value

    def inform_system_upgrade(self, system_name):
        self.systems_hp[system_name]["current_hp"] = 5

    def get_description(self):
        result = super().get_description()
        result["systems_hp"] = self.systems_hp
        result["crew"] = self.crew_sm.get_description()
        return result

    def put_description(self, descr):
        super().put_description(descr)
        self.systems_hp = descr["systems_hp"]
        self.crew_sm.put_description(descr["crew"])

    def inform_system_overload(self, system_name, power_overcome):
        self.overloaded[system_name] = power_overcome

    def inform_system_normalload(self, system_name):
        if system_name in self.overloaded:
            del self.overloaded[system_name]

    def next_step(self):
        super().next_step()
        # energy overload
        for system_name in self.overloaded:
            damage = self.energyoverlock_damage_per_tick * \
                self.overloaded[system_name]
            self.cause_damage2system(system_name, damage)

        # taking damage marker
        self.is_taking_damage = (WorldPhysConstants().current_frame(
        )-self.last_taking_damage_timestamp) < self.taking_damage_showoff_time

        # repair by crew
        self.repair_step()

    def repair_step(self):
        for sm_name in self.systems_hp:
            if self.systems_hp[sm_name]["current_hp"] < self.systems_hp[sm_name]["max_hp"]:
                repair_hp = self.crew_sm.get_repair_step(sm_name)
                if repair_hp:
                    self.systems_hp[sm_name]["current_hp"] = min(
                        self.systems_hp[sm_name]["max_hp"], self.systems_hp[sm_name]["current_hp"]+repair_hp)

    def can_be_upgraded(self, system_name):
        return (self.systems_hp[system_name]["current_hp"]/self.systems_hp[system_name]["max_hp"]) > 0.9

    def cause_damage2system(self, system_name, damage):
        if system_name not in self.systems_hp:
            return

        self.systems_hp[system_name]['current_hp'] = self.systems_hp[system_name]['current_hp']-damage

        if self.systems_hp[system_name]['current_hp'] <= 0:
            self.systems_hp[system_name]['current_hp'] = 0

            if self.get_system("RnD_sm").get_upgrade_level(system_name) > 0:
                self.get_system("RnD_sm").downgrade_system(system_name)
                self.systems_hp[system_name]['current_hp'] = self.systems_hp[system_name]['max_hp']

    def get_status(self):
        status = super().get_status()
        status["systems_hp"] = self.systems_hp
        status["is_taking_damage"] = self.is_taking_damage
        return status

    def get_short_description(self):
        return "100/100"

    def proceed_command(self, command: Command):
        super().proceed_command(command)
        if command.contains_level("crew_sm"):
            self.crew_sm.proceed_command(command)
        match command.get_action():
            case "takes_damage":
                self.takes_damage(command.get_params()[
                                  "damage_value"], command.get_params()["damage_type"])
            case 'repair_system_admin':
                system_name = command.get_params()["system_name"]
                self.systems_hp[system_name]['current_hp'] = self.systems_hp[system_name]['max_hp']

    def takes_damage(self, damage_value, damage_type='explosion', damage_source=None):
        self.last_taking_damage_timestamp = WorldPhysConstants().current_frame()

        targeted_system_name = "energy_sm"
        if damage_source:
            targeted_system_idx = abs(hash(damage_source)) % 5
            targeted_system_name = self.system_names[targeted_system_idx]
        else:
            targeted_system_name = random.choice(self.system_names)

        # temprary for balance calculation
        if damage_source not in self.tmp_damage_log:
            self.tmp_damage_log[damage_source] = 0

        # TODO delete later
        self.tmp_damage_log[damage_source] = self.tmp_damage_log[damage_source]+damage_value

        match damage_type:
            case "explosion":
                # system_name = random.choice(list(self.systems_hp.keys()))
                self.cause_damage2system(targeted_system_name, damage_value)
                self.crew_sm.takes_damage2system(
                    targeted_system_name, damage_value)
            case "emp":
                self.get_system("energy_sm").takes_emp_damage(
                    damage_value, ConfigLoader().get("damage.emp_duration", float))

            case 'collision':
                system_name = random.choice(list(self.systems_hp.keys()))
                modulo = damage_value % 1
                for i in range(int(damage_value)):
                    self.cause_damage2system(system_name, 1)
                self.cause_damage2system(system_name, modulo)
                self.crew_sm.takes_damage2system(system_name, damage_value)

            case "radiation":
                system_name = random.choice(list(self.systems_hp.keys()))
                self.cause_damage2system(system_name, damage_value)
                # self.crew_sm.takes_damage2system(system_name, damage_value)


class NPC_DamageSystem(BasicShipSystem):

    def __init__(self, mark_id):
        super().__init__(mark_id, "damage_sm")
        self.total_max_hp = 125
        self.hp_state = {
            "total_hp": {
                'current_hp': self.total_max_hp,
                "max_hp": self.total_max_hp,
            }
        }
        # taking damage marker
        self.is_taking_damage = False
        self.taking_damage_showoff_time = WorldPhysConstants().get_ticks_in_seconds(1)
        self.last_taking_damage_timestamp = WorldPhysConstants().current_frame()

        self.hp_list = [125, 150, 200, 250]

    def next_step(self):
        super().next_step()
        # energy overload

        # taking damage marker
        self.is_taking_damage = (WorldPhysConstants().current_frame(
        )-self.last_taking_damage_timestamp) < self.taking_damage_showoff_time

    def set_hp(self, value):
        self.hp_state = {
            "total_hp": {
                'current_hp': value,
                "max_hp": value,
            }
        }

    def upgrade(self):
        super().upgrade()
        self.set_hp(self.hp_list[self.upgrade_level])

    def downgrade(self):
        super().downgrade()
        self.set_hp(self.hp_list[self.upgrade_level])

    def inform_system_overload(self, system_name, power_overcome):
        pass

    def inform_system_normalload(self, system_name):
        pass

    def get_short_description(self):
        max_hp = round(self.hp_state["total_hp"]["max_hp"], 2)
        curr_hp = self.hp_state["total_hp"]["current_hp"]
        return f"{curr_hp}/{max_hp}"

    def get_status(self):
        status = super().get_status()
        status["systems_hp"] = self.hp_state
        status["is_taking_damage"] = self.is_taking_damage
        return status

    def proceed_command(self, command: Command):
        super().proceed_command(command)
        params = command.get_params()
        match command.get_action():
            case "takes_damage":
                self.takes_damage(command.get_params()[
                                  "damage_value"], command.get_params()["damage_type"])

            case 'set_NPC_hp':
                self.hp_state["total_hp"]["current_hp"] = params["value"]
                self.hp_state["total_hp"]["max_hp"] = params["value"]

    def takes_damage(self, damage_value, damage_type='explosion', damage_source=None):
        self.last_taking_damage_timestamp = WorldPhysConstants().current_frame()
        match damage_type:
            case "explosion":
                self.hp_state["total_hp"]["current_hp"] = self.hp_state["total_hp"]["current_hp"]-damage_value
            case "emp":
                self.get_system("energy_sm").takes_emp_damage(
                    damage_value, ConfigLoader().get("damage.emp_duration", float))
            case 'collision':
                self.hp_state["total_hp"]["current_hp"] = self.hp_state["total_hp"]["current_hp"]-damage_value
            case "radiation":
                self.hp_state["total_hp"]["current_hp"] = self.hp_state["total_hp"]["current_hp"]-damage_value

        if self.hp_state["total_hp"]["current_hp"] <= 0:
            TriggerQueue().add("ship_defeat", self.mark_id, {})
