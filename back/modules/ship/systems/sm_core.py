from modules.utils import Command, CommandQueue, PerformanceCollector, get_dt_ms
from datetime import datetime


class GlobalShipSystemController:
                _instance = None # Приватное поле для хранения единственного экземпляра

                def __new__(cls):
                                if cls._instance is None:
                                                cls._instance = super(GlobalShipSystemController, cls).__new__(cls)
                                                cls._instance.systems = {}



                                                                
                                return cls._instance



                                                
                def add(self, mark_id, system_name, system_class_obj):
                                if mark_id not in self.systems:
                                                self.systems[mark_id] = {}
                                self.systems[mark_id][system_name] = system_class_obj

                def get(self, mark_id, system_name):
                                try:
                                                return self.systems[mark_id][system_name]
                                except Exception as e:
                                                return None

                                
                def get_systems_list(self, mark_id):
                                result  = [sm_name for sm_name in self.systems[mark_id]]
                                return result

                def next_step(self, mark_id):
                                for sm_name in self.systems[mark_id]:
                                                tmp_t1 = datetime.now()
                                                self.systems[mark_id][sm_name].next_step()
                                                tmp_t2 = datetime.now()
                                                PerformanceCollector().add(f"Ship.system.{sm_name}", get_dt_ms(tmp_t1, tmp_t2))

                def get_status(self, mark_id):
                                res = {}
                                for sm_name in self.systems[mark_id]:
                                                tmp_t1 = datetime.now()
                                                res[sm_name] = self.systems[mark_id][sm_name].get_status()
                                                tmp_t2 = datetime.now()
                                                PerformanceCollector().add(f"Ship.status.{sm_name}", get_dt_ms(tmp_t1, tmp_t2))
                                return res



                                
                def delete(self, mark_id):
                                for sm_name in self.systems[mark_id]:
                                                self.systems[mark_id][sm_name].delete()
                                del self.systems[mark_id]

                def proceed_command(self, mark_id, command:Command):
                                for sm_name in self.systems[mark_id]:
                                                if command.contains_level(sm_name):
                                                                self.systems[mark_id][sm_name].proceed_command(command)
                                                                return True
                                return False

class BasicShipSystem:
                def __init__(self, master_id, sm_name):
                                self.sm_name = sm_name
                                self.mark_id = master_id
                                self.status = "OK"
                                self.power = 0.25
                                self.upgrade_level = 1



                def get_system(self, system_name):
                                return GlobalShipSystemController().get(self.mark_id, system_name)


                
                def get_description(self):
                                result = {
                                                "sm_name":self.sm_name,
                                                "mark_id":self.mark_id,
                                                "power":self.power,
                                                "upgrade_level": self.upgrade_level
                                }
                                return result

                def put_description(self, descr):
                                self.power = descr["power"]
                                self.set_level(descr["upgrade_level"])


                                
                def set_level(self, value):
                                func = self.upgrade
                                if value<self.upgrade_level:
                                                func = self.downgrade

                                for i in range(abs(value-self.upgrade_level)):
                                                func()


                                                
                def get_status(self):
                                return {
                                                "mark_id":self.mark_id,
                                                "status":self.status,

                                                #float - percentage of optimum
                                                #"power": self.power,

                                                #integer
                                                "upgrade_level": self.upgrade_level
                                }



                                



                                                
                def send_command(self, level, command, params):
                                cmd_content = {
                                                "level":"ship."+level,
                                                "target_id":self.mark_id,
                                                "action":command,
                                                "params":params
                                }
                                cmd_obj = Command(cmd_content)
                                CommandQueue().add_command(cmd_obj)


                def proceed_command(self, cmd:Command):
                                action = cmd.get_action()
                                match action:
                                                case "upgrade": self.upgrade()
                                                case "downgrade": self.downgrade()
                                                case "set_power":
                                                                self.power = cmd.get_params()["power"]

                def set_power(self, value):
                                self.power = value
                                if self.power>1:
                                                self.get_system("damage_sm").inform_system_overload(self.sm_name,self.power-1)
                                else:
                                                self.get_system("damage_sm").inform_system_normalload(self.sm_name)



                                

                def actualize(self):
                                pass

                def upgrade(self):
                                self.upgrade_level = self.upgrade_level+1
                                self.actualize()

                def downgrade(self):
                                self.upgrade_level = max(self.upgrade_level-1,0)
                                self.actualize()

                def next_step(self):
                                pass

                def delete(self):
                                pass
