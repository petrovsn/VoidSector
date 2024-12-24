from modules.ship.systems.sm_core import BasicShipSystem
from modules.physEngine.core import lBodyPool_Singleton, CalculationUtilites
from modules.utils import Command, ConfigLoader, PerformanceCollector, get_dt_ms
from datetime import timedelta
from datetime import datetime
import math


class RadarSystem(BasicShipSystem):
    def __init__(self, mark_id):
        super().__init__(mark_id, "radar_sm")
        self.lBodies = lBodyPool_Singleton()
        self.basic_close = ConfigLoader().get("sm_radar.basic_close_range", float)
        self.add_close = ConfigLoader().get(
            "sm_radar.add_close_range_per_upgrade_level", float)
        self.basic2distant_coef = ConfigLoader().get(
            "sm_radar.basic2distant_coef", float)

        self.radar_ping = timedelta(
            seconds=ConfigLoader().get("sm_radar.ping_time", float))
        self.energy_magnitude = 0
        self.launcher_shafts_amount = 0

    def get_status(self):
        res = super().get_status()
        res["close_range"] = self.lBodies.bodies[self.mark_id].close_scanrange
        res["distant_range"] = self.lBodies.bodies[self.mark_id].distant_scanrange
        res["distant_dir"] = self.lBodies.bodies[self.mark_id].distant_scanrange_dir
        res["distant_arc"] = self.lBodies.bodies[self.mark_id].distant_scanrange_arc
        return res

    def proceed_command(self, cmd: Command):
        super().proceed_command(cmd)
        action = cmd.get_action()
        params = cmd.get_params()
        match action:
            case "set_radar_arc":
                self.set_radar_params(params["radar_arc"], None)
            case "set_radar_dir":
                self.set_radar_params(None, params["radar_dir"])

    def upgrade(self):
        super().upgrade()
        self.update_scanrange()

    def downgrade(self):
        super().downgrade()
        self.update_scanrange()

    def get_actual_close_scanrange(self):
        return self.basic_close+self.add_close*self.upgrade_level

    def get_maximal_distant_scanrange(self):
        close_range = self.get_actual_close_scanrange()
        return close_range+close_range*self.basic2distant_coef*self.power

    def get_actual_distant_scanrange(self, arc=None):
        distance = self.get_maximal_distant_scanrange()
        sectorArea = 3.1415*distance*distance
        radar_arc_rad = CalculationUtilites.degress2rads(
            self.lBodies.bodies[self.mark_id].distant_scanrange_arc)
        if arc:
            radar_arc_rad = CalculationUtilites.degress2rads(arc)
        new_distance = math.sqrt(sectorArea/radar_arc_rad)
        return new_distance

    def update_scanrange(self):
        self.lBodies.bodies[self.mark_id].set_close_scanrange(
            self.get_actual_close_scanrange())
        self.lBodies.bodies[self.mark_id].set_distant_scanrange(
            self.get_actual_distant_scanrange())
        self.update_visibility()

    def set_power(self, value):
        super().set_power(value)
        self.update_scanrange()

    # вызывается из базового класса корабля

    def get_nav_data(self):
        nav_data = self.lBodies.bodies[self.mark_id].get_nav_data(
            self.radar_ping)
        return nav_data

    # radar_arc in angles

    def set_radar_params(self, radar_arc, radar_dir):
        new_distance = self.get_actual_distant_scanrange(radar_arc)
        self.lBodies.bodies[self.mark_id].set_distant_scanparams(
            new_distance, radar_arc, radar_dir)

    # вызывается из реактора на каждое изменение уровня энергии в любой системе
    def change_energy_magnitude(self, step):
        self.energy_magnitude = self.energy_magnitude+step
        self.update_visibility()

    # вызывается из лаунчера на каждое добавление/удаление пусковой шахты
    def set_launcher_shafts_amount(self, amount):
        self.launcher_shafts_amount = amount
        self.update_visibility()

    def update_visibility(self):
        pass
        # visibility = (self.launcher_shafts_amount + self.energy_magnitude)*2/19
        # self.lBodies.bodies[self.mark_id].set_visibility(visibility)


class NPC_RadarSystem(BasicShipSystem):
    pass
