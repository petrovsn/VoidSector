from modules.utils import Command

class QuestEvent:
                def __init__(self):
                                self.description = ""
                                self.trigger = None

                def match(trigger):
                                pass

class QuessEventsController:
                __instance = None
                def __new__(cls):
                                if cls._instance is None:
                                                cls._instance = super(QuessEventsController, cls).__new__(cls)
                                                cls._instance.quest_events = []
                                return cls._instance



                                
                def get_state(self):
                                pass



                                
                def proceed_command(self, cmd: Command):
                                action = cmd.get_action()
                                params = cmd.get_params()
                                match action:
                                                case "add_quest_event": self.add()

                def add(self, quest_event_descr):
                                pass

                def get_state(self):
                                pass

                def check_quest_event(trigger):

                                pass
