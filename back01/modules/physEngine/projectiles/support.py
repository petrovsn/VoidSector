from datetime import timedelta, datetime
import numpy as np
from modules.physEngine.projectiles.projectiles_core import pjtl_Basic
from modules.physEngine.core import CalculationUtilites
from modules.physEngine.triggers.collector import TriggerQueue
from modules.utils import ConfigLoader

#not implemented
#вырубает четыре пункта электричества на вражеском корабле на 5 секунд
class pjtl_TimedEMP(pjtl_Basic):
                def __init__(self, master_id):
                                super().__init__(master_id)
                                self.predictor_depth = 5
                                self.ttl = timedelta(seconds=self.predictor_depth)
                                self.launch_timestamp = 5
                                self.explosion_radius = ConfigLoader().get("projectile_params.pjtl_timedemp_exprad", float)

                def set_params(self, params):
                                if 'detonation_time' in params:
                                                self.predictor_depth = float(params["detonation_time"])
                                                self.ttl = timedelta(seconds=self.predictor_depth)
                                                self.upload_state_to_predictor()

                def get_params_template(self):
                                return {
                                                'detonation_time':[0,10,1,5]
                                }

                def update_position(self):
                                if self.status=="loaded":
                                                self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
                                                self.set_actual_vel()
                                                self.upload_state_to_predictor()



                                                                
                                elif self.status == "launched":
                                                self.update_predictions()
                                                if (datetime.now() - self.launch_timestamp)>self.ttl:
                                                                self.detonate()

                def takes_damage(self, damage_value, damage_type = "explosion", damage_source = None):
                                self.self_destruct()


                def detonate(self):
                                TriggerQueue().add("emp_detonate",self.mark_id, {"danger_radius":self.explosion_radius})
                                self.set_predictor_state(False)
                                self.status = "destroyed"




                                
#not implemented
#пока находишься внутри, видимость - 0.25%
class pjtl_TimedStealthCloak(pjtl_Basic):
                def __init__(self, master_id):
                                super().__init__(master_id)
                                self.predictor_depth = 5
                                self.ttl = timedelta(seconds=self.predictor_depth)
                                self.launch_timestamp = 5
                                self.explosion_radius = 50

                def set_params(self, params):
                                if 'detonation_time' in params:
                                                self.predictor_depth = float(params["detonation_time"])
                                                self.ttl = timedelta(seconds=self.predictor_depth)
                                                self.upload_state_to_predictor()

                def get_params_template(self):
                                return {
                                                'detonation_time':[0,10,1,5]
                                }

                def update_position(self):
                                if self.status=="loaded":
                                                self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
                                                self.set_actual_vel()
                                                self.upload_state_to_predictor()



                                                                
                                elif self.status == "launched":
                                                self.update_predictions()
                                                if (datetime.now() - self.launch_timestamp)>self.ttl:
                                                                self.detonate()
