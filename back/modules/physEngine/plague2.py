from math import ceil
from modules.physEngine.core import lBodyPool_Singleton
from modules.physEngine.world_constants import WorldPhysConstants
from modules.physEngine.projectiles.projectile_selector import ProjectileSelector
from modules.ship.systems.sm_core import BasicShipSystem
from modules.ship.shipPool import ShipPool_Singleton
from modules.utils import Command, CommandQueue, ConfigLoader
from modules.ship.systems.sm_core import GlobalShipSystemController
from random import *
from datetime import datetime, timedelta
import numpy as np
import json
import copy
#класс для хранения всех собранных знаний о карте векторов заболевания
class PlagueMatrix:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlagueMatrix, cls).__new__(cls)
            cls._instance.N = 7
            cls._instance.load_matrix()

            cls._instance.init_view_matrix()
            cls._instance.full_open_matrix()
        return cls._instance
    

    def get_description(self):
        return self.view_matrix
    
    def put_description(self,view_matrix):
        self.view_matrix = view_matrix

    def init_view_matrix(self):
        self.view_matrix = [["___" for b in range(self.N)] for a in range(self.N)]
        self.view_matrix[3][3] = self.get_cell_str(3,3)

    def full_open_matrix(self):
        self.view_matrix = [[self.get_cell_str(a,b) for b in range(self.N)] for a in range(self.N)]

    def generate(self):
        self.matrix = [[[0,0] for b in range(self.N)] for a in range(self.N)]
        for i in range(self.N):
            for j in range(self.N):
                self.matrix[i][j] = [0,-1]


    def open_view_cell(self, i, j):
        if i<0: return
        if j<0: return
        if i>6: return
        if j>6: return
        self.view_matrix[i][j] = self.get_cell_str(i,j)

    def open_matrix_area(self, i, j):
        for i_view in range(i-1, i+2):
            for j_view in range(j-1, j+2):
                self.open_view_cell(i_view, j_view)

    def load_matrix(self):
        matrix_data = json.load(open("configs/plague2_matrix.json",'r'))
        self.matrix = matrix_data["plague_matrix"]


    def get_cell_str(self, i, j):
        mental = self.matrix[i][j][0]
        health = self.matrix[i][j][1]
        return f"{health}, {mental}"

    def update_view(self):
        self.view_matrix = [["Unk." for b in range(self.N)] for a in range(self.N)]
        for i in range(self.N):
            for j in range(self.N):
                self.view_matrix[i][j] = self.get_cell_str(i,j)

    def load(self):
        pass


    def apply_mutator_to_cell_np(self, i, j, mutator):
        vector = np.array(self.matrix[i][j])
        match mutator:
            #отражает относительно ОХ(здоровье, j)
            case "A":
                vector[1]=-vector[1]
                pass

            #отражает относительно ОY(менталка, i)
            case "B":
                vector[0]=-vector[0]

            #+1 к менталке, -1 к здоровью
            case "C":
                vector[0] = vector[0]+1
                vector[1] = vector[1]-1

            #-1 к менталке, +1 к здоровью
            case "D":
                vector[0] = vector[0]+1
                vector[1] = vector[1]-1
        
        return vector
        

    def get_next_phase(self, current_phase, mutator):
        next_step = self.apply_mutator_to_cell_np(current_phase[0],current_phase[1],mutator)
        current_phase = np.array(current_phase)
        next_phase = current_phase+next_step
        return next_phase.tolist()

    def get(self):
        return self.view_matrix


class PlagueController_v2:
    def __init__(self):
        self.current_phase = [3,3]
        self.mutator = ""
        self.plague_step_sec = ConfigLoader().get("sm_med.plague_phase_min", float)*60
        self.plague_step_ticks = WorldPhysConstants().get_ticks_in_seconds(self.plague_step_sec)
        self.plague_actual_tick = self.plague_step_ticks
        self.active = False
        self.effects_line = ConfigLoader().get("sm_med.plague_scale_lines", list) #[-1.25, -1, -0.5, 0, 0.5, 1, 1.25]
        plague_phase_degradation = ConfigLoader().get("sm_med.plague_phase_degradation", float)
        fatigue_phase_sec = ConfigLoader().get("sm_med.fatigue_phase_min", float)*60
        self.plague_phase_degradation_tick = WorldPhysConstants().get_onetick_step(plague_phase_degradation, fatigue_phase_sec)


    def is_critical(self):
        if self.current_phase[0]<0: return "MP"
        if self.current_phase[0]>6: return "MP"
        if self.current_phase[1]<0: return "HP"
        if self.current_phase[1]>6: return "HP"
        return False

    def get_description(self):
        result = {
            "active": self.active,
            "current_phase": self.current_phase,
            "plague_actual_tick": self.plague_actual_tick,
            "plague_view_matrix": PlagueMatrix().get_description()
        }
        return result

    def put_description(self, descr):
        self.active = descr['active']
        self.current_phase = descr['current_phase']
        self.plague_actual_tick = descr['plague_actual_tick']
        PlagueMatrix().put_description(descr['plague_view_matrix'])

    def get_status(self):
        result = {
            "active": self.active,
            "current_phase": self.current_phase,
            "mutator": self.mutator,
            "time2next_phase": round(self.plague_actual_tick/WorldPhysConstants().get_ticks_per_second(),2)
        }
        return result

    def get_effects(self):
        
        if not self.active: return {"HP": 0, "MP": 0}
        if self.is_critical(): return {"HP": 0, "MP": 0}
        effects = {"HP": 0, "MP": 0}
        effects["HP"] = self.plague_phase_degradation_tick*self.effects_line[self.current_phase[1]]
        effects["MP"] = self.plague_phase_degradation_tick*self.effects_line[self.current_phase[0]]
        return effects
    
    def move_to_next_phase(self):
        if not self.is_critical():
            self.current_phase = PlagueMatrix().get_next_phase(self.current_phase, self.mutator)
            self.mutator = ""
            if self.is_critical():
                self.active = False
            else:
                PlagueMatrix().open_matrix_area(self.current_phase[0], self.current_phase[1])

    def set_phase(self, i, j):
        new_phase = [int(i),int(j)]
        if 0<=new_phase[0]<=6:
            if 0<=new_phase[1]<=6:
                self.current_phase = new_phase
                self.plague_actual_tick = self.plague_step_ticks

    def set_mutator(self, mutator):
        if not self.mutator:
            self.mutator = mutator

    def next_step(self):
        try:
            if self.active:
                self.plague_actual_tick = self.plague_actual_tick-1
                if self.plague_actual_tick <= 0:
                    self.move_to_next_phase()
                    self.plague_actual_tick = self.plague_step_ticks
        except Exception as e:
            print(e)
            self.active = False

        return self.get_effects()

    def set_active_state(self, value):
        self.active = value

    def proceed_command(self, cmd: Command):
        action = cmd.get_action()
        params = cmd.get_params()
        match action:

            case 'set_plague_v2_activity':
                self.set_active_state(params["state"])


            case "set_plague_v2_phase":
                self.set_phase(params["i"], params['j'])

            case 'set_plague_v2_mutator':
                self.set_mutator(params["mutator"])

