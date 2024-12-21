
from modules.ship.ship import ShipPool_Singleton
from modules.physEngine.core import lBodyPool_Singleton
from modules.utils import Command, CommandQueue, ConfigLoader


def get_entity_from_Pools(mark_id, pool_list):
                for pool in pool_list:
                                entity = pool.get(mark_id)
                                if entity: return entity
                return None


class GlobalEventSystem:
                _instance = None # Приватное поле для хранения единственного экземпляра

                def __new__(cls):
                                if cls._instance is None:
                                                cls._instance = super(GlobalEventSystem, cls).__new__(cls)
                                                cls._instance.cShips = ShipPool_Singleton()
                                                cls._instance.lBodies = lBodyPool_Singleton()

                                return cls._instance



                                
                def takes_damage(self, mark_id, damage_value, damage_type):
                                target = get_entity_from_Pools(mark_id, [self.cShips, self.lBodies])
                                if not target: return
                                if hasattr(target, "takes_damage"):
                                                target.takes_damage(damage_value, damage_type)




                                                                
                def add_resource(self, target_id,resource_name, resource_amount):
                                target = get_entity_from_Pools(target_id, [self.cShips, self.lBodies])
                                if not target: return
                                if hasattr(target, "gain_resource"):
                                                target.gain_resource(resource_name,resource_amount)


                def hBodyCollision(self, target_id):
                                phys_target = get_entity_from_Pools(target_id, [self.lBodies])
                                if not phys_target: return

                                phys_target.stabilize_orbit(offset=5)

                                target = get_entity_from_Pools(target_id, [self.cShips, self.lBodies])
                                damage_value = ConfigLoader().get("damage.hbody_collision_damage", float)
                                if hasattr(target, "takes_damage"):
                                                target.takes_damage(damage_value, "collision")



                                                                
