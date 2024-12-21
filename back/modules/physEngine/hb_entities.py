from modules.physEngine.core import hBody, hBodyPool_Singleton
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.triggers.collector import TriggerQueue
from modules.utils import ConfigLoader
from modules.physEngine.solar_flare.solar_flar_defendzone import SolarFlareDefendZone

class ResourceAsteroid(hBody):
                def __init__(self, x, y, r=100, m=10):
                                super().__init__(x,y,r,m)
                                self.mining_radius = self.gravity_well_radius #ConfigLoader().get("world.mining_r_percentage", float)*
                                self.marker_type = self.__class__.__name__ # "resource_asteroid"
                                self.radar_levels = [
                                                (0, "resource"),
                                ]



                                                
                def get_description(self,requester_id=None):
                                result = super().get_description(requester_id)
                                result['mining_radius'] = self.mining_radius
                                return result



                                
                def put_description(self, json_descr, forced=False):
                                super().put_description(json_descr, forced)
                                self.mining_radius = ConfigLoader().get("world.mining_r_percentage", float)*self.gravity_well_radius
                                if forced:
                                                self.mining_radius = json_descr['mining_radius']

                def add_in_gwell(self, mark_id):
                                super().add_in_gwell(mark_id)
                                SolarFlareDefendZone().add(mark_id)



                                
                def del_from_gwell(self, mark_id):
                                super().del_from_gwell(mark_id)
                                SolarFlareDefendZone().remove(mark_id)



                                                



                                
                def step(self):
                                super().step()

                #def step(self):
                # bodies_ids = self.get_entities_ids_list_in_range(self.lBodies.bodies, self.mining_radius, False)
                # for body_id in bodies_ids:
                #  TriggerQueue().add("collisionIntohBody", self.mark_id, {"target":body_id})



                                                


class WormHole(hBody):
                def __init__(self, x, y, r=100, m=10):
                                super().__init__(x,y,r,m)
                                self.marker_type = self.__class__.__name__ # "resource_asteroid"
                                self.radar_levels = [
                                                (2, "hbody"), #invisible on radar
                                ]
                                self.type = "WormHole"
                                self.mark_id = "WormHole"
                                self.critical_r = 1

                def step(self):
                                pass

                def get_description(self, requester_id=None):
                                res = super().get_description(requester_id)
                                res.pop("critical_r")
                                return res
