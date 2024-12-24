
import json
from modules.utils import Command
from modules.physEngine.quests.quest_controller_special import VanEicSet2Phase2,DestroyWormHole, ResurrectVanEick, PingFangDestruction

class QuestPointsController:

    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QuestPointsController, cls).__new__(cls)
            cls._instance.quest_points = {}
            quest_points_desr = json.load(
                open("quest_points/quest_points.json"))
            for quest_point_name in quest_points_desr:
                cls._instance.quest_points[quest_point_name] = QuestPointTrigger(
                    quest_points_desr[quest_point_name])

        return cls._instance

    def __init__(self) -> None:
        pass

    def load_triggers(self):
        pass

    def check_trigger(self, trigger):
        for qp_name in self.quest_points:
            result = self.quest_points[qp_name].check(trigger)
            if result:
                self.quest_points[qp_name].set_state(result)
                self.proceed_special_cases(qp_name, self.quest_points[qp_name].completed)

    def get_quest_point_state(self, qp_name):
        if qp_name in self.quest_points:
            return self.quest_points[qp_name].completed
        return True

    def toogle_quest_point_state(self, qp_name):
        self.quest_points[qp_name].completed = not self.quest_points[qp_name].completed

    def get_state(self):
        result = {}
        for qp_name in self.quest_points:
            result[qp_name] = self.quest_points[qp_name].completed
        return result

    def proceed_command(self, command: Command):
        action = command.get_action()
        params = command.get_params()
        match action:
            case "toogle_qp_state":
                self.toogle_quest_point_state(params["qp_name"])
                self.proceed_special_cases(params["qp_name"], self.quest_points[params["qp_name"]].completed)


    def proceed_special_cases(self, qp_name, state):
        if qp_name == '3_VanEicSet2Phase2':
            VanEicSet2Phase2(state)

        if qp_name == "4_DestroyWormHole":
            DestroyWormHole(state)
        
        if qp_name == "5_ResurrectVanEick":
            ResurrectVanEick(state)

        if qp_name == "6_PingFangDestruction":
            PingFangDestruction(state)
        

    def save(self):
        pass


class QuestPointTrigger:
    def __init__(self, quest_points_descr):
        self.initiator = quest_points_descr["initiator"]
        self.event_type = quest_points_descr["type"]
        self.event_params = quest_points_descr["params"]
        self.depends_on = None
        if "depends_on" in quest_points_descr:
            self.depends_on = quest_points_descr["depends_on"]
        self.completed = False
        pass

    def set_state(self, value: bool):
        self.completed = value

    def check(self, trigger):
        if self.depends_on:
            if not QuestPointsController().get_quest_point_state(self.depends_on):
                return False
        if self.completed:
            return False
        if self.event_type != trigger["type"]:
            return False

        match self.event_type:

            case 'quantumshadow_defeat':
                return True
            
            case "station_defeat":
                if self.initiator == trigger["initiator"]:
                    return True
                    
            case "interact":
                if self.initiator == trigger["initiator"]:
                    if self.event_params["target"] == trigger["params"]["target"]:
                        return True
            case 'damage2target':
                if self.initiator == trigger["params"]["master_id"]:
                    if self.event_params["damage_type"] == trigger["params"]["damage_type"]:
                        if self.event_params["target"] == trigger["params"]["target"]:
                            return True

        return False
