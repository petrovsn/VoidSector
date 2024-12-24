from modules.physEngine.projectiles.projectiles_core import pjtl_Constructed
from modules.utils import ConfigLoader


class ProjectileConstructorController:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(
                ProjectileConstructorController, cls).__new__(cls)
            cls._instance.blueprints = {}
            cls._instance.prices = {}

        return cls._instance

    def get_basic_blueprints(self):
        return {
            "protect": {
                "thruster": 0,
                "timer": 0,
                "inhibitor": 3,
                "explosive": 2,
                "emp": 7,
                "entities_detection": 3,
                "projectiles_detection": 3,
                "buster": 1,
                "detonator": 1,
                "decoy": 1
            },
            "boom": {
                "thruster": 1,
                "timer": 0,
                "inhibitor": 2,
                "explosive": 4,
                "emp": 0,
                "entities_detection": 2,
                "projectiles_detection": 0,
                "buster": 1,
                "detonator": 1,
                "decoy": 0
            },
            "t-1000": {
                "thruster": 0,
                "timer": 0,
                "inhibitor": 4,
                "explosive": 4,
                "emp": 5,
                "entities_detection": 5,
                "projectiles_detection": 5,
                "buster": 1,
                "detonator": 1,
                "decoy": 1
            },
            "piu-piu": {
                "thruster": 1,
                "timer": 0,
                "inhibitor": 2,
                "explosive": 2,
                "emp": 2,
                "entities_detection": 2,
                "projectiles_detection": 0,
                "buster": 1,
                "detonator": 1,
                "decoy": 0
            },
        }

    def get_basic_blueprints_NPC(self):
        return {
            "long": {
                "thruster": 3,
                "timer": 3,
                "inhibitor": 0,
                "explosive": 3,
                "emp": 3,
                "entities_detection": 0,
                "projectiles_detection": 0,
                "buster": 0,
                "detonator": 0,
                "decoy": 0
            },
            "short": {
                "thruster": 2,
                "timer": 2,
                "inhibitor": 0,
                "explosive": 2,
                "emp": 2,
                "entities_detection": 0,
                "projectiles_detection": 0,
                "buster": 0,
                "detonator": 0,
                "decoy": 0
            },
            "sn_ship": {
                "thruster": 1,
                "timer": 0,
                "inhibitor": 6,
                "explosive": 3,
                "emp": 3,
                "entities_detection": 6,
                "projectiles_detection": 0,
                "buster": 1,
                "detonator": 1,
                "decoy": 0
            },
        }

    def initiate_ship_blueprints(self, ship_mark_id, NPC):
        basic_bps = self.get_basic_blueprints()
        if NPC:
            basic_bps = self.get_basic_blueprints_NPC()

        self.blueprints[ship_mark_id] = basic_bps
        self.prices[ship_mark_id] = {}
        for bp_name in basic_bps:
            self.prices[ship_mark_id][bp_name] = self.get_blueprint_cost(
                basic_bps[bp_name])

    def append_blueprint(self, ship_mark_id, name, pjtl_description):
        self.blueprints[ship_mark_id][name] = pjtl_description
        self.prices[ship_mark_id][name] = self.get_blueprint_cost(
            pjtl_description)

    def get_blueprint(self, ship_mark_id, name):
        a = self.blueprints[ship_mark_id][name]
        return a

    def get_cost(self, ship_mark_id, name):
        a = self.prices[ship_mark_id][name]
        return a

    def get_volume(self, ship_mark_id, name):
        pjtl = pjtl_Constructed(
            None, None, self.blueprints[ship_mark_id][name], dumb=True)
        stats = pjtl.get_stats()
        return stats["details"]

    def get_blueprints_list(self, ship_mark_id):
        return (list(self.blueprints[ship_mark_id].keys()))

    def get_blueprint_cost(self, pjtl_description):
        sum = 0
        for comp_name in pjtl_description:
            sum = sum + \
                ConfigLoader().get(
                    f"projectile_builder_cost.{comp_name}", float)*pjtl_description[comp_name]
        return sum

    def get_production_time(self, pjtl_description):
        return 10

    def get_stats(self, pjtl_description):
        pjtl = pjtl_Constructed(None, None, pjtl_description, dumb=True)
        stats = pjtl.get_stats()
        stats["cost"] = self.get_blueprint_cost(pjtl_description)
        # stats["details"]*ConfigLoader().get(f"projectile_builder_cost.one_detail_time_production", float)
        stats["production_time"] = 5
        return stats

    def get_description(self, mark_id):
        return {
            "blueprints": self.blueprints[mark_id]
        }

    def put_description(self, mark_id, descr):
        self.blueprints[mark_id] = descr["blueprints"]
