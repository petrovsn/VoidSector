from modules.physEngine.basic_objects import dynamicBody, lBody
from datetime import datetime, timedelta
from modules.physEngine.core import CalculationUtilites
import numpy as np
from modules.physEngine.triggers.collector import TriggerQueue

from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController
from modules.physEngine.basic_objects import staticBody

class intact_Basic(staticBody, dynamicBody):
                def __init__(self, x,y, mark_id = None):
                                staticBody.__init__(self)
                                self.manual_init()
                                dynamicBody.__init__(self, x,y, mark_id)


                                                


                                                
                                self.set_marker_type("interactable_object")
                                EntityIDGroupsController().add(self.mark_id, ["interactable"])
                def interact(self):
                                pass


                def get_interact_description(self):
                                return ""

                def self_destruct(self):
                                super().self_destruct()
                                EntityIDGroupsController().remove(self.mark_id)

class intact_Container(intact_Basic):
                def __init__(self, x,y, mark_id = None):
                                super().__init__(x,y, mark_id)
                                self.storage = {

                                }
                                for name in ["metal"]:
                                                self.storage[name]=1

                def get_description(self, requester_id=None):
                                descr = super().get_description(requester_id)
                                for item in self.storage:
                                                descr[item] = self.storage[item]
                                return descr


                                

                def get_interact_description(self):
                                result = f"get "+str(self.storage["metal"])+" metal"
                                return result



                                
                def put_description(self, descr, foced):
                                for item in self.storage:
                                                if item in descr:
                                                                self.storage[item] = descr[item]


                def interact(self, interactor_id):
                                for item in self.storage:
                                                TriggerQueue().add("addresource", self.mark_id, {
                                                                                                "target":interactor_id,
                                                                                                "resource_name":item,
                                                                                                "resource_amount":self.storage[item],
                                                                                                })



                                                                
                                self.self_destruct()



class ShipDebris(intact_Container):
                def __init__(self, x,y, mark_id = None):
                                super().__init__(x,y, mark_id)
                                self.set_marker_type("ShipDebris")
                                self.storage["metal"]=500
                                if mark_id == "Nuestra Bien[debris]":
                                                self.storage["metal"]=5000
                                EntityIDGroupsController().add(self.mark_id, ["id_labels_detectable"])



                def self_destruct(self):
                                super().self_destruct()
                                EntityIDGroupsController().remove(self.mark_id)

                def interact(self, interactor_id):
                                for item in self.storage:
                                                TriggerQueue().add("addresource", self.mark_id, {
                                                                                                "target":interactor_id,
                                                                                                "resource_name":item,
                                                                                                "resource_amount":self.storage[item],
                                                                                                })


                                if self.mark_id != "Nuestra Bien[debris]":
                                                self.self_destruct()


class SpaceStationDebris(intact_Container):
                def __init__(self, x,y, mark_id = None):
                                super().__init__(x,y, mark_id)
                                self.set_marker_type("SpaceStationDebris")
                                for name in ["metal"]:
                                                self.storage[name]=1000
                                EntityIDGroupsController().add(self.mark_id, ["id_labels_detectable"])

                def get_surrounding_hbodies_ids(self):
                                return [self.hbody_idx]

                def self_destruct(self):
                                super().self_destruct()
                                EntityIDGroupsController().remove(self.mark_id)
