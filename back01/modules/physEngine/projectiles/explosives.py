from datetime import timedelta, datetime
import numpy as np
from modules.physEngine.projectiles.projectiles_core import pjtl_Basic
from modules.physEngine.core import CalculationUtilites
from modules.utils import ConfigLoader
from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController
from modules.physEngine.world_constants import WorldPhysConstants
import random

class pjtl_TimedExplosive(pjtl_Basic):
                def __init__(self, master_id):
                                super().__init__(master_id)
                                self.predictor_depth = 5
                                self.ttl = timedelta(seconds=self.predictor_depth)
                                self.launch_timestamp = 5
                                self.explosion_radius = ConfigLoader().get("projectile_params.pjtl_timedexplosive_exprad", float)
                                self.velocity_penalty = ConfigLoader().get("projectile_params.pjtl_timedexplosive_velpenalty", float)

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



class pjtl_TriggerExplosive(pjtl_Basic):
                def __init__(self, master_id):
                                super().__init__(master_id)
                                self.predictor_depth = ConfigLoader().get("projectile_params.pjtl_triggerexplosive_ttl", float)
                                self.launch_timestamp = None
                                self.ttl = timedelta(seconds=self.predictor_depth)



                                                
                                self.explosion_radius = ConfigLoader().get("projectile_params.pjtl_triggerexplosive_exprad", float)
                                self.activation_radius = ConfigLoader().get("projectile_params.pjtl_triggerexplosive_exprad", float)

                def update_position(self):
                                if self.status=="loaded":
                                                self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
                                                self.set_actual_vel()
                                                self.upload_state_to_predictor()



                                                                
                                elif self.status == "launched":
                                                self.update_predictions()
                                                if (datetime.now() - self.launch_timestamp)>self.ttl:
                                                                self.detonate()

                                                reachable_bodies = self.get_entities_ids_list_in_range(self.lBodies.bodies, self.activation_radius, False)
                                                if len(reachable_bodies)!=0:
                                                                if self.master_id in reachable_bodies:
                                                                                return
                                                                for mark in reachable_bodies:
                                                                                if hasattr(self.lBodies[mark], "master_id"):
                                                                                                if self.lBodies[mark].master_id != self.master_id:
                                                                                                                self.detonate()
                                                                                else:
                                                                                                self.detonate()



class pjtl_TimedTorpedo(pjtl_Basic):
                def __init__(self, master_id):
                                super().__init__(master_id)
                                self.predictor_depth = 5
                                self.ttl = timedelta(seconds=self.predictor_depth)
                                self.launch_timestamp = 5
                                self.explosion_radius = ConfigLoader().get("projectile_params.pjtl_timedtorpedo_exprad", float)
                                self.velocity_penalty = ConfigLoader().get("projectile_params.pjtl_timedtorpedo_velpenalty", float)

                def set_params(self, params):
                                if 'detonation_time' in params:
                                                self.predictor_depth = float(params["detonation_time"])
                                                self.ttl = timedelta(seconds=self.predictor_depth)
                                                self.upload_state_to_predictor()

                def get_params_template(self):
                                return {
                                                'detonation_time':[0,60,1,5]
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



class pjtl_HomingLRMissile(pjtl_Basic):
                def __init__(self, master_id):
                                super().__init__(master_id)
                                self.predictor_depth = 10

                                self.fly_time = timedelta(seconds=self.predictor_depth)
                                self.launch_timestamp = None
                                self.ttl = timedelta(seconds=ConfigLoader().get("projectile_params.pjtl_HomingLRMissile_ttl", float))



                                                
                                self.activation_delay = timedelta(seconds=15)

                                self.velocity_penalty = ConfigLoader().get("projectile_params.pjtl_HomingLRMissile_velpenalty", float)
                                self.detection_radius = ConfigLoader().get("projectile_params.pjtl_HomingLRMissile_targetdetectionrange", float)




                                                
                                self.explosion_radius = ConfigLoader().get("projectile_params.pjtl_HomingLRMissile_exprad", float)
                                self.activation_radius = ConfigLoader().get("projectile_params.pjtl_HomingLRMissile_expactrad", float)

                                self.locked_target = None

                                self.initial_speed = ConfigLoader().get("projectile_params.pjtl_HomingLRMissile_guidance_speed", float)
                                self.acceleration = ConfigLoader().get("projectile_params.pjtl_HomingLRMissile_guidance_acceleration", float)




                                                

                def set_params(self, params):
                                if 'activation_time' in params:
                                                self.predictor_depth = float(params["activation_time"])
                                                self.fly_time = timedelta(seconds=self.predictor_depth)
                                                self.upload_state_to_predictor()

                def get_params_template(self):
                                return {
                                                'activation_time':[10,90,1,5]
                                }



                                
                def get_description(self, requester_id=None):
                                res = super().get_description(requester_id)
                                res['explosion_radius'] = self.detection_radius
                                return res

                def update_position(self):
                                if self.status=="loaded":
                                                self.positions[1] = self.lBodies.bodies[self.master_id].get_position_np()
                                                self.set_actual_vel()
                                                self.upload_state_to_predictor()

                                elif self.status == "launched":
                                                self.update_predictions()
                                                if (datetime.now() - self.launch_timestamp)>self.activation_delay:
                                                                self.status = "activated"
                                                                self.launch_timestamp = datetime.now()



                                                                                                

                                elif self.status == "activated":
                                                if not self.locked_target:
                                                                targetable_ids = self.get_entities_ids_from_list_in_range(RadarDetectionEntitiesController().get(), self.detection_radius, False)



                                                                                
                                                                if self.master_id in targetable_ids:
                                                                                targetable_ids.remove(self.master_id)



                                                                                                
                                                                if targetable_ids:
                                                                                self.locked_target = random.choice(targetable_ids)
                                                else:
                                                                target_pos = self.lBodies[self.locked_target].get_position_np()
                                                                vector = target_pos-self.get_position_np()
                                                                acceleration = self.get_acceleration_gravity(self.positions[1])+CalculationUtilites.get_projections(self.acceleration, vector)
                                                                self.velocities[2]=CalculationUtilites.get_projections(self.initial_speed, vector)+WorldPhysConstants().get_timestep()*acceleration
                                                self.update_predictions()



                                                                

                                                reachable_bodies = self.get_entities_ids_list_in_range(self.lBodies.bodies, self.activation_radius, False)
                                                if len(reachable_bodies)!=0:
                                                                self.detonate()

                                                if (datetime.now() - self.launch_timestamp)>self.fly_time:
                                                                self.detonate()
