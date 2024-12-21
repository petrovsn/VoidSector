
from modules.ship.systems.sm_damage import CrewSystem
from modules.physEngine.solar_flare.solar_flar_defendzone import SolarFlareDefendZone
from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.projectiles.projectile_selector import ProjectileSelector
from modules.physEngine.projectiles.projectiles_core import pjtl_Basic, pjtl_Constructed
from modules.ship.shipPool import ShipPool_Singleton
from modules.ship.systems.sm_core import BasicShipSystem
from modules.ship.systems.sm_core import GlobalShipSystemController
from modules.utils import Command, CommandQueue, ConfigLoader
from modules.physEngine.aliances_controller import AlianceController

# launch drones, increase launch shafts amount


class LauncherSystem(BasicShipSystem):
    def __init__(self, mark_id):
        super().__init__(mark_id, "launcher_sm")
        self.lBodies = lBodyPool_Singleton()
        self.shafts = {
            str(k): LauncherSystem_shaft(str(k), self.mark_id) for k in range(self.upgrade_level)
        }
        self.select_shaft("0")
        self.status = "OK"
        self.auto_toggle = True
        self.auto_reload = False
        self.set_auto_reload(self.auto_reload)
        AlianceController().register(mark_id)

    def set_auto_reload(self, value):
        self.auto_reload = value
        for key in self.shafts:
            self.shafts[key].set_auto_reload(self.auto_reload)

    def upgrade(self):
        super().upgrade()
        if len(self.shafts) < 6:
            key = str(len(self.shafts))
            self.shafts[key] = LauncherSystem_shaft(key, self.mark_id)
            self.shafts[key].set_auto_reload(self.auto_reload)
        self.get_system("radar_sm").set_launcher_shafts_amount(
            self.get_actual_shafts_number())
        self.update_available_projectile()

    def get_actual_shafts_number(self):
        return len(self.shafts)

    def downgrade(self):
        super().downgrade()
        key = str(len(self.shafts)-1)
        if key in self.shafts:
            self.shafts[key].unload()
            del self.shafts[key]
            self.get_system("radar_sm").set_launcher_shafts_amount(
                self.get_actual_shafts_number())

    def unload(self):
        for key in self.shafts:
            self.shafts[key].unload()

    def get_status(self):
        shafts_status = {k: self.shafts[k].get_status() for k in self.shafts}

        status = super().get_status()
        status["shafts"] = shafts_status
        status["auto_toggle"] = self.auto_toggle
        status["auto_reload"] = self.auto_reload
        status["aliance"] = AlianceController().get_aliance(self.mark_id)
        return status

    def proceed_command(self, command: Command):
        super().proceed_command(command)
        if command.contains_level("shaft"):
            shaft_id = command.get_target_id("shaft")
            self.shafts[shaft_id].proceed_command(command)
            return

        params = command.get_params()
        match command.get_action():
            case 'select_shaft':
                self.select_shaft(params["shaft_id"])

            case 'auto_toggle':
                self.auto_toggle = params["active"]

            case 'auto_reload':
                self.set_auto_reload(params["active"])

            case "aim":
                for n in self.shafts:
                    self.shafts[n].aim(params)
            case "launch":
                succeed = self.shafts[self.selected_shaft].launch()
                if succeed:
                    self.iterate_shaft()

            case "add_to_aliance":
                AlianceController().add(self.mark_id, params["mark_id"])
            
            case "remove_from_aliance":
                AlianceController().remove(self.mark_id, params["mark_id"])

    def iterate_shaft(self):
        if self.auto_toggle:
            max_shaft = str(len(self.shafts))
            self.selected_shaft = str(int(self.selected_shaft)+1)
            if self.selected_shaft == max_shaft:
                self.selected_shaft = "0"
            self.select_shaft(self.selected_shaft)

    def select_shaft(self, n):
        self.selected_shaft = n
        for k in self.shafts:
            if self.shafts[k].shaft_num == n:
                self.shafts[k].select()
            else:
                self.shafts[k].unselect()

    def next_step(self):
        for k in self.shafts:
            self.shafts[k].next_step(self.power)

    def update_available_projectile(self):

        projectiles = self.get_system(
            "resources_sm").get_available_projectiles()
        for k in self.shafts:
            self.shafts[k].available_projectiles = projectiles

    def initiate(self):
        self.update_available_projectile()
        for k in self.shafts:
            self.shafts[k].initiate()


# класс одной шахты


class LauncherSystem_shaft:
    def __init__(self, shaft_num, master_mark_id) -> None:
        self.lBodies = lBodyPool_Singleton()
        self.master_mark_id = master_mark_id
        self.shaft_num = shaft_num

        self.selected = False
        self.projectile = None

        self.available_projectiles = ProjectileSelector.get_projectiles_list()

        self.loading_progress = 0
        self.loading_time = ConfigLoader().get(
            "sm_launcher.reloading_period_sec", float)
        self.auto_reload = True
        self.last_load_params = None

        self.launch_params = {
            "vel_angle": 0,
            "vel_scalar": 0
        }

        self.projectile_templates = {

        }

        self.launch_speed = ConfigLoader().get("sm_launcher.launch_speed", float)
        self._crew_sm = None

    def set_auto_reload(self, value):
        self.auto_reload = value

    @property
    def crew_sm(self):
        if not self._crew_sm:
            self.crew_sm = GlobalShipSystemController().get(self.master_mark_id, "crew_sm")
        return self._crew_sm

    @crew_sm.setter
    def crew_sm(self, value):
        self._crew_sm = value

    # one step - ~0.03 sec
    def next_step(self, power):
        if self.projectile:
            if self.projectile.status == "destroyed":
                self.projectile = None
                self.loading_progress = 0
                return

            if self.loading_progress != 100:
                crew_acc = self.crew_sm.get_crew_acceleration_in_system(
                    "launcher_sm") if self.crew_sm else 0
                loading_step = WorldPhysConstants().get_onetick_step(
                    100, self.loading_time)*(1+crew_acc)*power
                self.loading_progress = round(
                    min(100, self.loading_progress+loading_step), 2)

    def proceed_command(self, command: Command):
        match command.get_action():
            case 'load_projectile':
                self.load(command.get_params())
            case 'set_projectile_params':
                self.set_projectile_params(command.get_params())

    def get_status(self):
        return {
            "progress": self.loading_progress,
            "selected": self.selected,
            "available_projectiles": self.available_projectiles,
            "loaded_type": self.projectile.pjtl_name if self.projectile else None,
            "launch_params": self.projectile_templates[self.projectile.type] if self.projectile else {}
        }

    def aim(self, params):
        if self.projectile:
            self.projectile.set_aim(
                params["vel_angle"], self.launch_speed*params["vel_scalar"])

    def set_projectile_params(self, params):
        if self.projectile:
            self.projectile.set_params(params)
            try:
                if self.projectile.type in self.projectile_templates:
                    for k in params:
                        self.projectile_templates[self.projectile.type][k][-1] = params[k]
            except Exception as e:
                pass

    def send_command(self, level, command, params):
        cmd_content = {
            "level": "ship."+level,
            "target_id": self.master_mark_id,
            "action": command,
            "params": params
        }
        cmd_obj = Command(cmd_content)
        CommandQueue().add_command(cmd_obj)

    def launch(self):
        if self.selected:
            if self.projectile:
                if int(self.loading_progress) == 100:
                    self.projectile.launch()
                    self.projectile = None
                    self.loading_progress = 0
                    self.launch_params = {}
                    if self.auto_reload:
                        self.load(self.last_load_params)
                    return True

    def return_projectile_to_storage(self):
        resources_sm = GlobalShipSystemController().get(
            self.master_mark_id, "resources_sm")
        if self.projectile:
            resources_sm.add_resource(self.projectile.pjtl_name, 1)
            self.unload()

    def get_projectile_from_storage(self, projectile_type):
        resources_sm = GlobalShipSystemController().get(
            self.master_mark_id, "resources_sm")
        if not resources_sm.stockpile_items.contains_item(projectile_type):
            return False
        success = resources_sm.spend_resource(projectile_type, 1)
        return success

    # projectile_type - projectile, mine, drone

    def load(self, params):
        self.last_load_params = params
        self.return_projectile_to_storage()
        if not params["type"]:
            self.unload()
            return
        projectile_type = params["type"].split('[')[0].strip()
        if not self.get_projectile_from_storage(projectile_type):
            return

        blueprint = GlobalShipSystemController().get(
            self.master_mark_id, "resources_sm").get_blueprint(projectile_type)
        self.projectile: pjtl_Constructed = pjtl_Constructed(
            self.master_mark_id, projectile_type, blueprint)
        if not self.projectile:
            return

        if self.projectile:
            self.update_template()

            paramset = {}
            for k in self.projectile_templates[self.projectile.type]:
                paramset[k] = self.projectile_templates[self.projectile.type][k][-1]
            self.projectile.set_params(paramset)
            self.projectile.set_aim(0, 0)
            if self.selected:
                self.show_projectile()
        GlobalShipSystemController().get(
            self.master_mark_id, "launcher_sm").update_available_projectile()

    def update_template(self):
        projectile_params = self.projectile.get_params_template()
        if self.projectile.type not in self.projectile_templates:
            self.projectile_templates[self.projectile.type] = projectile_params
        else:
            current_template = self.projectile_templates[self.projectile.type]
            for k in projectile_params:
                if k not in current_template:
                    self.projectile_templates[self.projectile.type] = projectile_params
                    return
                if projectile_params[k][:-1] != current_template[k][:-1]:
                    self.projectile_templates[self.projectile.type] = projectile_params
                    return
            for k in current_template:
                if k not in projectile_params:
                    self.projectile_templates[self.projectile.type] = projectile_params
                    return

    def unload(self):
        self.hide_projectile()
        self.projectile = None
        self.loading_progress = 0
        self.launch_params = {}

    # only visual via LBody Singleton
    def select(self):
        if self.selected:
            return
        self.selected = True
        self.show_projectile()

    def unselect(self):
        if not self.selected:
            return
        self.selected = False
        self.hide_projectile()

    def show_projectile(self):
        if self.projectile:
            self.lBodies.add(self.projectile)

    def hide_projectile(self):

        if self.projectile:

            flare_defended = self.projectile.mark_id in SolarFlareDefendZone().entities
            self.lBodies.delete(self.projectile.mark_id)
            if flare_defended:
                SolarFlareDefendZone().add(self.projectile.mark_id)


class XenoBeast_Launcher:

    def get_status(self):
        shafts_status = {k: self.shafts[k].get_status() for k in self.shafts}
        status = super().get_status()
        status["shafts"] = shafts_status
        status["auto_toggle"] = self.auto_toggle
        status['xeno_beast'] = True
        return status

    def proceed_command(self, command: Command):
        super().proceed_command(command)
        if command.contains_level("shaft"):
            shaft_id = command.get_target_id("shaft")
            self.shafts[shaft_id].proceed_command(command)
            return


