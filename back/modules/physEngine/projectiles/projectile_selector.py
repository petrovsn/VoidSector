from modules.physEngine.projectiles.explosives import pjtl_TimedExplosive, pjtl_TriggerExplosive, pjtl_TimedTorpedo, pjtl_HomingLRMissile
from modules.physEngine.projectiles.mine import pjtl_Mine
from modules.physEngine.projectiles.support import pjtl_TimedEMP
from modules.physEngine.projectiles.drones import io_Drone


class ProjectileSelector:
                def get_projectiles_list():
                                return ["pjtl_TimedExplosive", "pjtl_TriggerExplosive", "pjtl_Mine", "pjtl_TimedEMP", "io_Drone", "pjtl_TimedTorpedo", "pjtl_HomingLRMissile"]

                def get_projectile_by_classname(classname, master_id):
                                match classname:
                                                case "pjtl_TimedExplosive": return pjtl_TimedExplosive(master_id)
                                                case "pjtl_TriggerExplosive": return pjtl_TriggerExplosive(master_id)
                                                case "pjtl_Mine": return pjtl_Mine(master_id)
                                                case "pjtl_TimedEMP": return pjtl_TimedEMP(master_id)
                                                case "io_Drone": return io_Drone(master_id)
                                                case 'pjtl_TimedTorpedo': return pjtl_TimedTorpedo(master_id)
                                                case "pjtl_HomingLRMissile": return pjtl_HomingLRMissile(master_id)
                                return None
