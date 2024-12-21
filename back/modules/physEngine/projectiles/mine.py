from datetime import timedelta, datetime
from modules.physEngine.projectiles.projectiles_core import pjtl_Basic
from modules.physEngine.core import CalculationUtilites
from modules.utils import ConfigLoader
import numpy as np

class pjtl_Mine(pjtl_Basic):
                def __init__(self, master_id):
                                super().__init__(master_id)
                                self.activation_radius = ConfigLoader().get("projectile_params.pjtl_mine_exprad", float)
                                self.explosion_radius = ConfigLoader().get("projectile_params.pjtl_mine_exprad", float)
                                self.velocity_penalty = ConfigLoader().get("projectile_params.pjtl_mine_velpenalty", float)



                                                

                def get_params_template(self):
                                return {
                                                'prediction_depth':[5, 60, 1, 20]
                                }



                                
                def set_params(self, params):
                                if 'prediction_depth' in params:
                                                self.predictor_depth = float(params["prediction_depth"])
                                                self.upload_state_to_predictor()



                                                

                def update_position(self):
                                if self.status=="loaded":
                                                self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
                                                self.set_actual_vel()
                                                self.upload_state_to_predictor()



                                                                
                                elif self.status == "launched":
                                                self.update_predictions()
                                                reachable_bodies = self.get_entities_ids_list_in_range(self.lBodies.bodies, self.activation_radius, False)
                                                if len(reachable_bodies)!=0:
                                                                if self.master_id in reachable_bodies: return



                                                                                
                                                                for mark in reachable_bodies:
                                                                                if not self.lBodies[mark].is_detectable: continue
                                                                                if hasattr(self.lBodies[mark], "master_id"):
                                                                                                if self.lBodies[mark].master_id != self.master_id:
                                                                                                                self.detonate()
                                                                                else:
                                                                                                self.detonate()





                                
