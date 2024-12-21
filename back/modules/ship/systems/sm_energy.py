from modules.ship.systems.sm_core import BasicShipSystem
from modules.utils import Command
from datetime import datetime, timedelta


class EnergySystem(BasicShipSystem):
    def __init__(self, mark_id, NPC=False):
        super().__init__(mark_id, "energy_sm")
        self.NPC = NPC
        self.max_power_supply = 4
        self.systems_energy = {
            "engine_sm": 1,
            "launcher_sm": 1,
            "radar_sm": 1,
            "resources_sm": 1,
        }
        self.energy_level_upgrade = 3
        self.NPC_energy_proxy = 7
        self.energy_limit = self.get_energy_limit()
        self.debuffs = []
        

    def set_NpcEnergy(self):
        self.shift_energy_level("launcher_sm", self.NPC_energy_proxy)
        self.shift_energy_level("resources_sm", self.NPC_energy_proxy)
        self.shift_energy_level("engine_sm", self.NPC_energy_proxy)
        self.shift_energy_level("radar_sm", self.NPC_energy_proxy)

    def get_energy_limit(self):
        if self.NPC:
            return 1+(self.NPC_energy_proxy+1)*4
        return 1+self.upgrade_level*self.energy_level_upgrade

    def get_energy_usage(self):
        return sum(self.systems_energy.values())

    def get_energy_free(self):
        return self.energy_limit - self.get_energy_usage()

    def set_max_power(self):
        for system_name in self.systems_energy.keys():
            self.systems_energy[system_name] = 4
            self.get_system(system_name).set_power(1)
        self.get_system("radar_sm").change_energy_magnitude(16)

    def get_status(self):
        status = super().get_status()
        status["systems_energy"] = self.systems_energy
        status["max_power_supply"] = self.max_power_supply
        status["energy_free"] = self.get_energy_free()
        return status

    def shift_energy_level(self, system_name, step):
        result = self.systems_energy[system_name]+step
        if result < 0:
            return
        # self.get_system("radar_sm").change_energy_magnitude(step)
        self.systems_energy[system_name] = result
        power_supply = self.systems_energy[system_name]/self.max_power_supply
        self.get_system(system_name).set_power(power_supply)

    def next_step(self):
        debuff_value = 0
        if len(self.debuffs) > 0:
            time_now = datetime.now()
            shift_outdated = None
            for i, (emp_damage, exp_ttime) in enumerate(self.debuffs):
                if time_now < exp_ttime:
                    debuff_value = debuff_value+emp_damage
                else:
                    shift_outdated = i
            if shift_outdated:
                self.debuffs = self.debuffs[shift_outdated+1:]

        debuff_value = int(debuff_value)

        self.energy_limit = max(0, self.get_energy_limit() - debuff_value)

        energy_shrinkage = self.get_energy_usage()-self.energy_limit
        if (energy_shrinkage > 0):
            for i in range(energy_shrinkage):
                idx = i % len(self.systems_energy)
                system_name = list(self.systems_energy.keys())[idx]
                self.shift_energy_level(system_name, -1)

    def proceed_command(self, command: Command):
        super().proceed_command(command)
        match command.get_action():
            case 'increase_energy_level':
                if self.get_energy_free() < 1:
                    return
                system_name = command.get_params()["system"]
                self.shift_energy_level(system_name, 1)

            case 'decrease_energy_level':
                system_name = command.get_params()["system"]
                if self.systems_energy[system_name] < 1:
                    return
                self.shift_energy_level(system_name, -1)

            case 'emp_damage':
                damage_value = command.get_params()["damage_value"]
                duration = command.get_params()["duration"]
                self.takes_emp_damage(damage_value, duration)

    def takes_emp_damage(self, damage_value, duration):
        self.debuffs.append(
            (damage_value, datetime.now()+timedelta(seconds=duration)))

    def upgrade(self):
        super().upgrade()
        self.energy_limit = self.upgrade_level*self.energy_level_upgrade

    def downgrade(self):
        super().downgrade()
        self.energy_limit = self.upgrade_level*self.energy_level_upgrade
