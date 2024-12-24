from modules.utils import ConfigLoader
class WorldPhysConstants:
                _instance = None # Приватное поле для хранения единственного экземпляра

                def __new__(cls):
                                if cls._instance is None:
                                                cls._instance = super(WorldPhysConstants, cls).__new__(cls)
                                                cls._instance.Gconst = ConfigLoader().get("world.gravity_constant", float)
                                                #cls._instance.timestep = 0.5
                                                cls._instance.timestep = 0.03
                                                cls._instance.real_timestep = 0.03
                                                cls._instance.frame_counter = 0
                                return cls._instance



                                

                def set_Gconst(self, value):
                                self.Gconst = value

                def get_Gconst(self):
                                return self.Gconst

                def set_timestep(self, value):
                                self.timestep = value

                def get_timestep(self):
                                return self.timestep



                                
                def get_real_timestep(self):
                                return self.real_timestep



                                
                def get_ticks_per_second(self):
                                return 1.0/self.real_timestep



                                
                def get_ticks_in_seconds(self, seconds):
                                return seconds/self.real_timestep




                                
                def get_real2sim_timescale(self):
                                return self.timestep/self.real_timestep



                                
                def get_onetick_step(self, summary_value, summary_realtime):
                                step_per_sec = summary_value/summary_realtime
                                step_per_tick = step_per_sec/(1/self.real_timestep)
                                return step_per_tick



                                
                def next_step(self):
                                self.frame_counter = self.frame_counter+1

                def current_frame(self):
                                return self.frame_counter




                                
