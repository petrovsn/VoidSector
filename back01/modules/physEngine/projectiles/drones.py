from datetime import timedelta, datetime
import numpy as np
from modules.physEngine.projectiles.projectiles_core import pjtl_Basic
from modules.physEngine.core import CalculationUtilites
from modules.physEngine.triggers.collector import TriggerQueue


class io_Drone(pjtl_Basic):
                def __init__(self, master_id):
                                super().__init__(master_id)
                                self.set_marker_type(self.__class__.__name__)# "io_Drone"
                                self.resource_storage = {}
                                self.set_predictor_state(True)


                def get_params_template(self):
                                return {
                                                'prediction_depth':[5, 60, 1, 20]
                                }



                                
                def set_params(self, params):
                                if 'prediction_depth' in params:
                                                self.predictor_depth = float(params["prediction_depth"])
                                                self.upload_state_to_predictor()

                def get_description(self, requester_id=None):
                                status = super().get_description(requester_id)
                                status["type"] = "io_Drone"
                                return status

                def gain_resource(self,resource_name,resource_amount):
                                if self.status == "launched":
                                                self.status = "at_work"
                                                self.stabilize_orbit(offset=-5)
                                                self.predictor_controller.logout(self.mark_id)

                                if resource_name not in self.resource_storage:
                                                self.resource_storage[resource_name]=0
                                self.resource_storage[resource_name] = self.resource_storage[resource_name]+resource_amount


                def update_position(self):
                                if self.status=="loaded":
                                                self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
                                                self.set_actual_vel()
                                                self.upload_state_to_predictor()



                                                                
                                elif self.status == "launched":
                                                self.update_predictions()

                                elif self.status == "at_work":
                                                self.update_predictions()


                def interact(self, interactor_id):
                                if self.status == "at_work":
                                                if interactor_id != self.master_id: self.detonate()
                                                for resource_name in self.resource_storage:
                                                                TriggerQueue().add("addresource", self.mark_id,{
                                                                                                                "target":interactor_id,
                                                                                                                "resource_name":resource_name,
                                                                                                                "resource_amount":self.resource_storage[resource_name],
                                                                                                                })



                                                                                
                                                TriggerQueue().add("addresource", self.mark_id,{
                                                                                                                "target":interactor_id,
                                                                                                                "resource_name":"io_Drone",
                                                                                                                "resource_amount":1,
                                                                                                                })


                                                self.self_destruct()




                                
