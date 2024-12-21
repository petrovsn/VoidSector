from math import ceil
from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.projectiles.projectile_selector import ProjectileSelector
from modules.ship.systems.sm_core import BasicShipSystem
from modules.ship.shipPool import ShipPool_Singleton
from modules.utils import Command, CommandQueue, ConfigLoader
from modules.ship.systems.sm_core import GlobalShipSystemController
from random import *
from datetime import datetime, timedelta
from modules.physEngine.plague2 import PlagueController_v2

class PlaguePhase:
    def __init__(self, name, next_phase, duration_sec, effect,) -> None:

        self.name: str = name
        self.next_phase: str = next_phase
        self.effect: dict = effect
        self.duration_sec: int = duration_sec
        self.ttl: int = int(WorldPhysConstants(
        ).get_ticks_per_second()*self.duration_sec)

    def run(self):
        self.ttl = WorldPhysConstants().get_ticks_per_second()*self.duration_sec

    def is_over(self):
        return self.ttl == 0

    def next_step(self):
        self.ttl = max(0, self.ttl-1)

    def time2next(self):
        return round(self.ttl/WorldPhysConstants().get_ticks_per_second())


class PlagueController:
    def __init__(self):
        self.current_phase = None

        self.plague_phase_sec = ConfigLoader().get("sm_med.plague_phase_min", float)*60
        plague_phase_degradation = ConfigLoader().get(
            "sm_med.plague_phase_degradation", float)
        plague_min_step = WorldPhysConstants().get_onetick_step(
            plague_phase_degradation, self.plague_phase_sec)  # *60

        self.phases = {
            # здоров

            None: PlaguePhase(name=None, next_phase=None, duration_sec=self.plague_phase_sec,                      effect={"HP": 0, "MP": 0}),
            '': PlaguePhase(name=None, next_phase=None, duration_sec=self.plague_phase_sec,                      effect={"HP": 0, "MP": 0}),
            # первая фаза инкубации
            "incubation": PlaguePhase(name="incubation", next_phase="predromal", duration_sec=self.plague_phase_sec,                effect={"HP": 0, "MP": 0}),


            # усиливает усталость
            "predromal": PlaguePhase(name="predromal", next_phase="active", duration_sec=self.plague_phase_sec, effect={"HP": 0, "MP": -plague_min_step}),

            # снимает хиты и усталость
            "active": PlaguePhase(name="active", next_phase="active_terminal", duration_sec=self.plague_phase_sec,              effect={"HP": -plague_min_step, "MP": -plague_min_step}),

            # снимакт хиты и усталость вдвое быстрее
            "active_terminal": PlaguePhase(name="active_terminal", next_phase="active_terminal", duration_sec=self.plague_phase_sec,                effect={"HP": -2*plague_min_step, "MP": -2*plague_min_step}),



            "active_regen": PlaguePhase(name="active_regen", next_phase="active_regen_terminal", duration_sec=self.plague_phase_sec,        effect={"HP": None, "MP": -plague_min_step}),

            "active_regen_terminal": PlaguePhase(name="active_regen_terminal", next_phase="active_regen_terminal", duration_sec=self.plague_phase_sec,             effect={"HP": None, "MP": -plague_min_step*2}),

            "active_mental": PlaguePhase(name="active_mental", next_phase="active_mental_terminal", duration_sec=self.plague_phase_sec, effect={"HP": -plague_min_step, "MP": None}),

            "active_mental_terminal": PlaguePhase(name="active_mental_terminal", next_phase="active_mental_terminal", duration_sec=self.plague_phase_sec,             effect={"HP": -plague_min_step*2, "MP": None}),
        }

    def get_description(self):
        result = {
            "phase": self.current_phase,
            "time2next": self.phases[self.current_phase].ttl
        }
        return result

    def put_description(self, descr):
        self.current_phase = descr['phase']
        self.phases[self.current_phase].ttl = descr["time2next"]

    def get_status(self):
        result = {
            "phase": None,
            "time2next": None
        }
        if self.current_phase:
            result['phase'] = self.current_phase
            result['time2next'] = self.phases[self.current_phase].time2next()
        return result

    def next_step(self):
        if self.current_phase:
            current_phase_obj = self.phases[self.current_phase]
            current_phase_obj.next_step()
            if current_phase_obj.is_over():
                self.current_phase = current_phase_obj.next_phase
                self.phases[self.current_phase].run()
        return self.phases[self.current_phase].effect

    def set_phase(self, phase):
        self.current_phase = phase
        self.phases[phase].run()

    def proceed_command(self, cmd: Command):
        action = cmd.get_action()
        params = cmd.get_params()
        match action:
            case "set_plague_phase":
                self.set_phase(params["phase"])


class HealthAxisController:
    def __init__(self):
        self.value = 8
        self.next_step_mod = 0
        self.normal_interval = [8, 8]
        self.light_damage = [5, 7]
        self.heavy_damage = [2, 4]
        self.frozen = False
        self.crit_state = False
        self.crit_timestamp = None
        #self.crit_duration = ConfigLoader().get("sm_med.critical_state_duration_min",
        #                                       float)*WorldPhysConstants().get_ticks_per_second()*60

        self.crit_stim_injection_duration = ConfigLoader().get("sm_med.crit_stim_injection_duration_min",
                                               float)*WorldPhysConstants().get_ticks_per_second()*60
        self.crit_stim_activity_left = 0

    def get_num_status(self):
        current_value = self.get_value()
        if self.normal_interval[0]<=current_value: return 4
        if self.light_damage[0]<=current_value<=self.light_damage[1]: return 3
        if self.heavy_damage[0]<=current_value<=self.heavy_damage[1]: return 2
        return 1

    def set_next_step_mod(self, value):
        self.frozen = False
        self.next_step_mod = value
        if value == None:
            self.frozen = True
            self.next_step_mod = 0

    def get_value(self):
        return ceil(self.value)

    def add_points(self, value):
        self.value = self.value+value
        if self.value > 9:
            self.value = 9
        if self.value < 1:
            self.value = 1

    def apply_light_cure(self):
        if self.light_damage[0] <= self.value <= self.light_damage[1]:
            self.value = randint(
                self.normal_interval[0], self.normal_interval[1])

    def apply_hard_cure(self):
        if self.heavy_damage[0] <= self.value <= self.heavy_damage[1]:
            self.value = randint(self.light_damage[0], self.light_damage[1])

    def apply_crit_cure(self):
        if self.value <= 1:
            self.value = self.normal_interval[0] #randint(self.normal_interval[0], self.normal_interval[1])
            self.crit_stim_activity_left = self.crit_stim_injection_duration
            #self.set_crit_state(False)

    def set_crit_state(self, value):
        if value == self.crit_state: return
        self.crit_state = value
        self.value = 1
        #if value == False:
        #    self.crit_stim_activity_left = self.crit_stim_injection_duration

    def next_step(self):
        #в норме - добавляет модификатор к состоянию на каждом шаге.
        #если крит и игрок не реактивирован стимулятором - игнорирует модификатор
        can_do_next_step = False
        if not self.crit_state:
            can_do_next_step = True
        else:
            if self.crit_stim_activity_left>0:
                can_do_next_step = True

        if can_do_next_step:
            self.value = max(1, self.next_step_mod+self.value)
            self.value = min(9, self.value)
        #if self.value == 1:
        #    self.set_crit_state(True)
        #if self.crit_state:
        #    if WorldPhysConstants().current_frame() > self.crit_timestamp+self.crit_duration:
        #        self.crit_state = False
        #        self.crit_timestamp = None
        #        self.apply_crit_cure()
        if self.crit_state:
            if self.crit_stim_activity_left>0:
                self.crit_stim_activity_left = self.crit_stim_activity_left-1
                if self.crit_stim_activity_left<=0:
                    self.value = 1
        else:
            if self.value == 1:
                self.set_crit_state(True)




class MPAxisController(HealthAxisController):
    def __init__(self):
        super().__init__()
        self.normal_interval = [6, 8]
        self.light_damage = [4, 5]
        self.heavy_damage = [2, 3]
        self.logged_in = False
        fatigue_phase_min = ConfigLoader().get("sm_med.fatigue_phase_min", float)*60
        fatigue_phase_degradation = ConfigLoader().get(
            "sm_med.fatigue_phase_degradation", float)
        self.fatigue_step = WorldPhysConstants().get_onetick_step(
            fatigue_phase_degradation, fatigue_phase_min)

    def log_in(self):
        self.logged_in = True

    def log_out(self):
        self.logged_in = False

    # основной метод, отсчитывающий такты состояний
    def next_step(self):
        super().next_step()
        if self.logged_in:
            self.value = max(self.value-self.fatigue_step, 1)


class HPAxisController(HealthAxisController):
    


    def apply_wound(self):
        if self.frozen:
            return
        if 8 < self.value <= 9:
            self.value = 8
            return
        if 7 < self.value <= 8:
            self.value = randint(self.light_damage[0], self.light_damage[1])
            return
        elif self.light_damage[0] <= self.value <= self.light_damage[1]:
            self.value = randint(self.heavy_damage[0], self.heavy_damage[1])
            return
        elif self.value <= self.heavy_damage[1]:
            self.value = 1
            return


class HealthStateController:
    def __init__(self):
        self.HP = HPAxisController()
        self.MP = MPAxisController()
        self.plague_controller = PlagueController_v2()

        self.logged_in = False

        # блок про то, сколько висит плашка "вы ранены"
        self.wounded = False
        self.wound_timestamp = None
        self.wound_disability_period = timedelta(
            seconds=ConfigLoader().get("sm_med.wound_disability_period", float))

        # раз во сколько времени в игрока может прилететь ранение
        self.last_wound_timestamp = None
        self.is_vulnerable = True
        self.unvulnerability_period_min = timedelta(
            minutes=ConfigLoader().get("sm_med.unvulnerability_period_min", float))

        # через сколько после лечения можно повторно вводить лекарства
        self.can_be_cured = True
        self.cure_timestamp = None
        self.set_cure_reablity_default()
            #minutes=ConfigLoader().get("sm_med.cure_reabilitation_period_min", float))

    def set_cure_reablity_crit(self):
        self.cure_reabilitation_period_min = timedelta(minutes=ConfigLoader().get("sm_med.cure_reabilitation_period_min_crit", float))

    def set_cure_reablity_default(self):
        self.cure_reabilitation_period_min = timedelta(minutes=ConfigLoader().get("sm_med.cure_reabilitation_period_min", float))

    def is_vulnerable_f(self):
        if not self.logged_in:
            return False
        return self.is_vulnerable

    def get_description(self):
        return {
            "HP": self.HP.value,
            "MP": self.MP.value,
            "plague": self.plague_controller.get_description(),
        }

    def put_description(self, descr):
        self.HP.value = descr["HP"]
        self.MP.value = descr["MP"]
        self.plague_controller.put_description(descr["plague"])

    def get_state(self):
        return {
            "HP": self.HP.get_value(),
            "MP": self.MP.get_value(),
            "plague": self.plague_controller.get_status(),
            "disabled": self.wounded,
            "can_be_cured": self.can_be_cured
        }

    def set_wounded(self, state):
        if state:
            self.last_wound_timestamp = datetime.now()
            self.wound_timestamp = datetime.now()
        else:
            self.wound_timestamp = None
        self.wounded = state

    def update_wounded(self):
        if self.wound_timestamp:
            if self.wound_timestamp+self.wound_disability_period < datetime.now():
                self.set_wounded(False)

    def update_unvulnerability(self):
        if self.last_wound_timestamp:
            if self.last_wound_timestamp+self.unvulnerability_period_min>datetime.now():
                self.set_vulnerable(False)
            else:
                self.set_vulnerable(True)
        else:
            self.set_vulnerable(True)

    def set_can_be_cured(self, state):
        if state:
            self.cure_timestamp = None
        else:
            self.cure_timestamp = datetime.now()
        self.can_be_cured = state

    def update_can_be_cured_state(self):
        if self.cure_timestamp:
            if self.cure_timestamp+self.cure_reabilitation_period_min < datetime.now():
                self.set_can_be_cured(True)

    def set_vulnerable(self, state):
        self.is_vulnerable = state

    def get_controller(self, scale):
        if scale == "MP":
            return self.MP
        return self.HP

    def log_in(self):
        self.logged_in = True
        self.MP.log_in()

    def log_out(self):
        self.logged_in = False
        self.MP.log_out()

    def add_points(self, scale, points):
        controller: HealthAxisController = self.get_controller(scale)
        controller.add_points(points)

    def apply_light_cure(self, scale):
        controller: HealthAxisController = self.get_controller(scale)
        controller.apply_light_cure()
        self.set_cure_reablity_default()
        self.set_can_be_cured(False)
        

    def apply_hard_cure(self, scale):
        controller: HealthAxisController = self.get_controller(scale)
        controller.apply_hard_cure()
        self.set_cure_reablity_default()
        self.set_can_be_cured(False)

    def apply_crit_cure(self, scale):
        controller: HealthAxisController = self.get_controller(scale)
        controller.apply_crit_cure()
        self.set_cure_reablity_crit()
        self.set_can_be_cured(False)

    def apply_wound(self):
        self.HP.apply_wound()
        if self.HP.value<8:
            self.set_wounded(True)

    def detect_wound(self):
        self.set_wounded(True)

    def next_step(self):
        effects = self.plague_controller.next_step()
        #if effects["HP"] == None:
        #   self.set_vulnerable(False)
        #else:
        self.update_unvulnerability()
        self.MP.set_next_step_mod(effects["MP"])
        self.HP.set_next_step_mod(effects["HP"])
        self.MP.next_step()
        last_HP_status = self.HP.get_num_status()
        self.HP.next_step()
        current_HP_status = self.HP.get_num_status()
        if current_HP_status<last_HP_status:
            self.detect_wound()
        self.update_wounded()
        self.update_can_be_cured_state()

        plague_critical_axis = self.plague_controller.is_critical()
        if plague_critical_axis=="MP":
            self.MP.set_crit_state(True)
        if plague_critical_axis == "HP":
            self.HP.set_crit_state(True)


class MedicineSystem(BasicShipSystem):
    def __init__(self, mark_id):
        super().__init__(mark_id, "med_sm")
        self.capacity = 5
        self.capacity_levels = ConfigLoader().get("sm_med.capacity_levels", list)
        self.crew_units = 0

        self.crew_unit_healing_progress = 0
        self.crew_unit_healing_progress_max = 100
        self.crew_unit_healing_duration = ConfigLoader().get(
            "sm_med.crew_unit_healing_duration", float)
        self.crew_unit_healing_step = WorldPhysConstants(
        ).get_onetick_step(100, self.crew_unit_healing_duration)
        self.active = True

        self.roles = {
            "captain": HealthStateController(),
            "navigator": HealthStateController(),
            "cannoneer": HealthStateController(),
            "engineer": HealthStateController(),
            "medic": HealthStateController(),
        }
        self._crew_sm = None

    def get_description(self):
        result = super().get_description()
        result["crew_units"] = self.crew_units
        result["roles"] = {
            role: self.roles[role].get_description() for role in self.roles
        }
        return result

    def put_description(self, descr):
        super().put_description(descr)
        self.crew_units = descr["crew_units"]
        for role in descr["roles"]:
            self.roles[role].put_description(descr["roles"][role])

    def upgrade(self):
        super().upgrade()
        self.capacity = self.capacity_levels[self.upgrade_level]

    def downgrade(self):
        super().downgrade()
        self.capacity = self.capacity_levels[self.upgrade_level]
        if self.crew_units > self.capacity:
            self.crew_units = self.capacity

    @property
    def crew_sm(self):
        if not self._crew_sm:
            self.crew_sm = GlobalShipSystemController().get(self.mark_id, "crew_sm")
        return self._crew_sm

    @crew_sm.setter
    def crew_sm(self, value):
        self._crew_sm = value

    def get_status(self):
        res = super().get_status()
        res = {"roles": {}, "hospital": {}}
        for a in self.roles:
            res["roles"][a] = self.roles[a].get_state()
        res["hospital"]["capacity"] = int(self.capacity)
        res["hospital"]["units"] = self.crew_units
        res["hospital"]["progress"] = self.crew_unit_healing_progress
        return res

    def get_random_vulnerable_role(self):
        available = []
        for role in ["captain", "navigator", "cannoneer", "engineer"]:
            if self.roles[role].is_vulnerable_f():
                available.append(role)
        if available:
            return choice(available)
        else:
            return None

    def add_unit_to_hospital(self, value):

        not_placed_in_hospital = 0
        if self.crew_units+value > self.capacity:
            not_placed_in_hospital = self.capacity-self.crew_units+value

        self.crew_units = min(self.crew_units+value, self.capacity)
        role_to_wound = self.get_random_vulnerable_role()
        if role_to_wound:
            self.roles[role_to_wound].apply_wound()

        return not_placed_in_hospital

    def remove_unit_from_hospital(self, value):
        if self.crew_units >= value:
            self.crew_units = self.crew_units-value
            self.crew_sm.add_unit_to_crew(value)

    def npc_crew_cure_step(self):
        if self.active:
            if self.crew_units > 0:
                if self.crew_unit_healing_progress < self.crew_unit_healing_progress_max:
                    healing_step = self.get_healing_step()
                    self.crew_unit_healing_progress = min(self.crew_unit_healing_progress+healing_step,
                                                          self.crew_unit_healing_progress_max)
                else:
                    self.crew_unit_healing_progress = 0
                    self.remove_unit_from_hospital(1)

    def get_healing_step(self):
        crew_acc = self.crew_sm.get_crew_acceleration_in_system(
            "resources_sm") if self.crew_sm else 0
        power = self.get_system("resources_sm").power
        return self.crew_unit_healing_step*(1+crew_acc)*power

    def proceed_command(self, cmd: Command):
        action = cmd.get_action()
        params = cmd.get_params()

        if cmd.contains_level("plague"):
            role = params['role']
            self.roles[role].plague_controller.proceed_command(cmd)
            return

        match action:
            case 'set_activity':
                self.active = params["value"]
            case 'toogle_activity':
                self.active = not self.active
            case "remove_unit_from_hospital": self.remove_unit_from_hospital(params['value'])
            case "disable_user":
                self.roles[params['role']].set_disable(params['role'], True)

            case "restore_user":
                self.roles[params['role']].set_disable(params['role'], False)

            case 'apply_light_cure':
                self.roles[params['role']].apply_light_cure(params['axis'])
            case 'apply_hard_cure':
                self.roles[params['role']].apply_hard_cure(params['axis'])
            case 'apply_crit_cure':
                self.roles[params['role']].apply_crit_cure(params['axis'])

            case 'add_points':
                self.roles[params['role']].add_points(
                    params['axis'], params["value"])

            case 'apply_wound':
                self.roles[params['role']].apply_wound()

            case "log_in":
                self.roles[params['role']].log_in()

            case "log_out":
                self.roles[params['role']].log_out()

            case "add_patient":
                self.roles[params['name']] = HealthStateController()

    def next_step(self):
        super().next_step()
        for role in self.roles:
            self.roles[role].next_step()
        self.npc_crew_cure_step()
