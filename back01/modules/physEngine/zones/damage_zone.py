from datetime import datetime, timedelta
from modules.physEngine.active_objects import destructableObject
from modules.physEngine.basic_objects import lBody
from modules.physEngine.world_constants import WorldPhysConstants
from modules.utils import ConfigLoader
from modules.physEngine.triggers.collector import TriggerQueue

class ae_BasicZone(lBody,destructableObject):
                def __init__(self, x, y):
                                lBody.__init__(self, x, y)
                                destructableObject.__init__(self, self.mark_id)
                                self.marker_type = "ae_BasicZone"
                                self.blast_type = self.__class__.__name__
                                self.is_detectable = False

                def get_description(self, requester_id = None):
                                result = super().get_description(requester_id)
                                result["type"] = "ae_BasicZone"
                                result["danger_radius"] = self.danger_radius
                                result["blast_type"] = self.blast_type
                                return result



                                
import time



class ae_ExplosionZone(ae_BasicZone):
                def __init__(self, x, y, danger_radius, master_id):
                                super().__init__(x, y)
                                self.danger_radius = danger_radius
                                self.master_id = master_id
                                duration = ConfigLoader().get("damage.explosive_duration", float)
                                self.ttl = WorldPhysConstants().get_ticks_in_seconds(duration) #timedelta(seconds=duration)
                                self.launch_timestamp = WorldPhysConstants().current_frame() #time.perf_counter()# datetime.now()
                                damage_per_second = ConfigLoader().get("damage.explosion_damage_per_sec", float)*danger_radius

                                self.damage_per_step = WorldPhysConstants().get_onetick_step(damage_per_second*duration,duration)


                def update_position(self):
                                reachable_bodies = self.get_entities_ids_list_in_range(self.lBodies.bodies, self.danger_radius, False)
                                for body_id in reachable_bodies:
                                                distance = self.get_distance2entity(body_id)
                                                damage2target = self.damage_per_step*(1-distance/self.danger_radius)
                                                TriggerQueue().add("damage2target", self.mark_id,{'target':body_id,
                                                                                                                                                                                                                                                                "master_id": self.master_id,
                                                                                                                                "damage_value":damage2target,
                                                                                                                                "damage_type":"explosion"})
                                time_now = WorldPhysConstants().current_frame()#time.perf_counter()
                                time_delta = time_now - self.launch_timestamp
                                if time_delta>self.ttl:
                                                self.self_destruct()


class ae_EMPZone(ae_BasicZone):
                def __init__(self, x, y, danger_radius, master_id):
                                super().__init__(x, y)
                                self.master_id = master_id
                                self.danger_radius = danger_radius
                                self.ttl = timedelta(seconds=2)
                                self.launch_timestamp = datetime.now()


                def update_position(self):
                                reachable_bodies = self.get_entities_ids_list_in_range(self.lBodies.bodies, self.danger_radius, False)
                                for body_id in reachable_bodies:
                                                TriggerQueue().add("damage2target", self.mark_id,{'target':body_id, "master_id": self.master_id,
                                                                                                                                "damage_value":4/60,
                                                                                                                                "damage_type":"emp"})

                                if (datetime.now() - self.launch_timestamp)>self.ttl:
                                                self.self_destruct()






