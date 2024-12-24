
from modules.ship.systems.sm_core import BasicShipSystem
from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.active_objects import ae_Ship
from modules.physEngine.world_constants import WorldPhysConstants
from modules.utils import Command, ConfigLoader, PerformanceCollector, get_dt_ms
from datetime import datetime
import numpy as np

from modules.ship.systems.sm_damage import CrewSystem
from modules.ship.systems.sm_core import GlobalShipSystemController

class EngineSystem(BasicShipSystem):
                def __init__(self,pos_x, pos_y, mark_id, ship_subtype = "ae_Ship"):
                                super().__init__(mark_id, "engine_sm")
                                self.mark_id = mark_id
                                self.lBodies = lBodyPool_Singleton()
                                self.lBodies.add(ae_Ship(pos_x, pos_y, self.mark_id, ship_subtype))


                                #мощность двигателя на разном уровне прокачки
                                self.thrust_levels = ConfigLoader().get("sm_engine.thrust_levels", list)

                                #кривая генерации перегрева
                                self.burning_period = ConfigLoader().get("sm_engine.burning_period", float)
                                ticks_per_sec = WorldPhysConstants().get_ticks_per_second()





                                                
                                self.heatcap_levels = [t*self.burning_period*ticks_per_sec for t in self.thrust_levels]



                                                
                                self.heat_level_limit = self.heatcap_levels[self.upgrade_level]
                                self.heat_level = 0
                                self.max_thrust = self.thrust_levels[self.upgrade_level]

                                time_limit = ConfigLoader().get("sm_engine.cooling_period", float)
                                self.cooling_normal_speed = WorldPhysConstants().get_onetick_step(self.heat_level_limit,time_limit)

                                rotation360time_levels = ConfigLoader().get("sm_engine.rotation360time_levels", list)
                                self.rotation_levels = [360/rot360_time for rot360_time in rotation360time_levels]

                                self.reverse_penalty = ConfigLoader().get("sm_engine.reverse_penalty", float)



                                                


                                self.acceleration = 0
                                self.rotation = 0
                                self._crew_sm = None



                                                
                @property
                def crew_sm(self):
                                if not self._crew_sm:
                                                self.crew_sm = GlobalShipSystemController().get(self.mark_id, "crew_sm")
                                return self._crew_sm

                def get_position(self):
                                result = [0,0]
                                try:
                                                result = self.lBodies[self.mark_id].get_position()
                                except Exception: pass
                                return result


                                
                @crew_sm.setter
                def crew_sm(self, value):
                                self._crew_sm = value


                
                def get_description(self):
                                result = super().get_description()
                                result["lbody"] = self.lBodies[self.mark_id].get_description()
                                return result

                
                def put_description(self, descr):
                                super().put_description(descr)
                                self.lBodies[self.mark_id].put_description(descr["lbody"])

                def get_actual_heat_generated(self):
                                actual_thrust = abs(self.acceleration)
                                heat_generated = actual_thrust
                                return heat_generated

                def next_step(self):
                                if self.heat_level>=self.heat_level_limit:
                                                self.lBodies[self.mark_id].set_acceleration(0)

                                heat_generated = self.get_actual_heat_generated()

                                if heat_generated==0:
                                                if self.heat_level <= self.heat_level_limit:
                                                                cooling_speed = self.get_cooling_speed()
                                                                self.heat_level = max(self.heat_level-cooling_speed, 0)
                                else:
                                                self.heat_level = min(self.heat_level_limit,self.heat_level + heat_generated)


                def get_status(self):
                                status = super().get_status()
                                status['heat_level'] = round((self.heat_level/self.heat_level_limit)*100,2)
                                status["velocity"] = round(self.lBodies[self.mark_id].get_abs_velocity(),2)
                                status["direction"] = round(self.lBodies[self.mark_id].direction%360,2)
                                status["deltaV"] = round(self.burning_period*self.thrust_levels[self.upgrade_level]*(1-self.heat_level/self.heat_level_limit), 2)


                                return status



                                

                def get_cooling_speed(self):
                                crew_acc= self.crew_sm.get_crew_acceleration_in_system("engine_sm") if self.crew_sm else 0
                                return self.cooling_normal_speed*(1+crew_acc)*self.power



                                

                def get_actual_thrust(self, thrust_percentage):
                                actual_thrust = self.max_thrust*thrust_percentage
                                if actual_thrust<0: actual_thrust = actual_thrust*self.reverse_penalty
                                return actual_thrust



                                

                def proceed_command(self, command:Command):
                                super().proceed_command(command)
                                match command.get_action():
                                                case 'set_prediction_depth':
                                                                self.set_prediction_depth(command.get_params())
                                                case 'set_acceleration':
                                                                self.set_acceleration(command.get_params())
                                                case "exhaust_heat":
                                                                pass


                def set_prediction_depth(self, params):
                                self.lBodies[self.mark_id].set_prediction_depth(params['value'])

                def set_acceleration(self, params):
                                if "acceleration" in params:
                                                self.acceleration = self.get_actual_thrust(float(params["acceleration"]))
                                                self.lBodies[self.mark_id].set_acceleration(self.acceleration)



                                                                
                                if "rotation" in params:
                                                self.rotation = self.rotation_levels[self.upgrade_level]*float(params["rotation"])*self.power
                                                self.lBodies[self.mark_id].set_rotation(self.rotation)


                def delete(self):
                                super().delete()
                                self.lBodies[self.mark_id].self_destruct()
                                #self.lBodies.de



class NPC_Kraken_EngineSystem(EngineSystem):
                def get_cooling_speed(self):
                                return self.cooling_normal_speed*(1)*self.power
