from modules.physEngine.core import lBodyPool_Singleton, hBodyPool_Singleton
from modules.physEngine.predictor import TrajectoryPredictor, TrajectoryPredictor_controller
from modules.ship.ship import NPC_Ship, NPC_Kraken
from modules.ship.shipPool import ShipPool_Singleton


import numpy as np 
def VanEicSet2Phase2(state):
    if lBodyPool_Singleton().if_body_exists("VanEick"):
        lBodyPool_Singleton().bodies["VanEick"].set_phase('phase2' if state else 'phase1')

def DestroyWormHole(state):
    if hBodyPool_Singleton().if_body_exists("WormHole"):
        hBodyPool_Singleton().bodies["WormHole"].set_position_np_manual(np.array([-90000,9000]))
        hBodyPool_Singleton().update_description()
        TrajectoryPredictor_controller().update_hbodies_location()
        


def ResurrectVanEick(state):
    if lBodyPool_Singleton().if_body_exists("VanEick"):
        position = lBodyPool_Singleton().bodies["VanEick"].get_position_np()
        lBodyPool_Singleton().delete("VanEick")
        npc_VanEick = NPC_Ship(90000, 900000, "VanEick")
        ShipPool_Singleton().spawn(npc_VanEick)
        #lBodyPool_Singleton().add(npc_VanEick)
        lBodyPool_Singleton().bodies["VanEick"].set_position_np_manual(position)


def PingFangDestruction(state):
    if lBodyPool_Singleton().if_body_exists("PingFang"):
        position = lBodyPool_Singleton().bodies["PingFang"].get_position_np()
        npc_Kraken = NPC_Kraken(position[0], position[1],"Kraken")
        ShipPool_Singleton().spawn(npc_Kraken)
