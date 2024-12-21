from modules.physEngine.solar_flare.solar_flar_defendzone import SolarFlareDefendZone
from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.triggers.collector import TriggerQueue
from modules.physEngine.world_constants import WorldPhysConstants
from modules.utils import Command, ConfigLoader


class SolarFlareActivator:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SolarFlareActivator, cls).__new__(cls)
            cls._instance.lBodies = lBodyPool_Singleton()
            cls._instance.active = False
            damage_per_sec = ConfigLoader().get("damage.solarflare_damage_per_sec", float)
            cls._instance.damage_per_tick = WorldPhysConstants(
            ).get_onetick_step(damage_per_sec, 1)
            cls._instance.ticks_per_sec = WorldPhysConstants().get_ticks_in_seconds(1)
            cls._instance.activity_period_ticks = ConfigLoader().get(
                "solar_flares.activity_period_min", float)*cls._instance.ticks_per_sec*60
            cls._instance.sleep_period_ticks = ConfigLoader().get(
                "solar_flares.sleep_period_min", float)*cls._instance.ticks_per_sec*60
            cls._instance.current_tick = 0
            cls._instance.timer_active = False
            cls._instance.probability = "low"  # high
        return cls._instance

    def add(self, mark_id):
        pass

    def set_state(self, state):
        self.timer_active = False
        self.current_tick = 0
        self.active = state

    def set_probability(self, state):
        self.probability = state

    def get_description(self):
        return {
            "timer_active": self.timer_active,
            "current_tick": self.current_tick,
            "active": self.active,
            "probability": self.probability
        }

    def put_description(self, descr):
        self.timer_active = descr["timer_active"]
        self.current_tick = descr["current_tick"]
        self.active = descr["active"]

    def get_status(self):
        return {
            "state": self.active,
            "timer_state": self.timer_active,
            "time2nextphase": self.get_time2nextphase(),
            "probability": self.probability
        }

    def get_time2nextphase(self):
        return round((self.get_current_timer()-self.current_tick)/self.ticks_per_sec, 0)

    def set_timer(self, state):
        self.timer_active = state

    def set_timer_value(self, value):
        new_value = float(value)*self.ticks_per_sec
        self.current_tick = 0
        if self.active:
            self.activity_period_ticks = new_value
            return
        self.sleep_period_ticks = new_value

    def get_current_timer(self):
        if self.active:
            return self.activity_period_ticks
        else:
            return self.sleep_period_ticks

    def proceed_command(self, command: Command):
        action = command.get_action()
        params = command.get_params()
        match action:
            case "set_solar_flare":
                self.set_state(params["state"])
            case "set_timer_state":
                self.set_timer(params["state"])
            case "set_timer_value":
                self.set_timer_value(params["value"])
            case 'set_probability_value':
                self.set_probability(params["value"])

    def timer_step(self):
        if self.timer_active:
            self.current_tick = self.current_tick+1
            if self.current_tick >= self.get_current_timer():
                self.active = not self.active
                self.current_tick = 0
                if not self.active:
                    self.set_probability("low")
                    self.set_timer(False)
                

    def step(self):
        self.timer_step()
        if self.active:
            defended = SolarFlareDefendZone().get_defended()
            for body_id in self.lBodies.bodies:
                if body_id not in defended:
                    TriggerQueue().add("damage2target", "SolarFlare", {'target': body_id,
                                                                       "damage_value": self.damage_per_tick,
                                                                       "damage_type": "radiation"})
