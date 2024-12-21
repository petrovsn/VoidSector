from modules.physEngine.basic_objects import lBody, CalculationUtilites, staticBody
from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController
from modules.physEngine.triggers.collector import TriggerQueue
from modules.utils import ConfigLoader
from modules.physEngine.world_constants import WorldPhysConstants
import numpy as np



class MeteorsCloud(staticBody, lBody):
                def __init__(self, x,y, mark_id = None):
                                staticBody.__init__(self)
                                self.manual_init()
                                lBody.__init__(self, x,y, mark_id)
                                self.danger_radius = 40
                                self.marker_type = self.__class__.__name__
                                damage_per_sec = ConfigLoader().get("damage.meteors_coud_damage_per_sec",float)
                                self.damage_per_tick = WorldPhysConstants().get_onetick_step(damage_per_sec,1)
                                self.stabilize_orbit()



                                                
                def get_description(self, requester_id=None):
                                result = super().get_description(requester_id)
                                result["danger_radius"] = self.danger_radius
                                result["vel"] = self.get_velocity_np_static().tolist()
                                return result



                                

                def put_description(self, descr, foced):
                                self.danger_radius = descr["danger_radius"]
                                self.set_velocity(np.array(descr["vel"]))

                                



                def update_position(self):
                                super().update_position()

                                reachable_bodies = self.get_entities_ids_from_list_in_range(EntityIDGroupsController().get("is_ships"), self.danger_radius, False)
                                for body_id in reachable_bodies:
                                                TriggerQueue().add("damage2target", self.mark_id,{'target':body_id,
                                                                                                                                "damage_value":self.damage_per_tick,
                                                                                                                                "damage_type":"radiation"})
