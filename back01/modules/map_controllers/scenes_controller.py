from modules.physEngine.core import basic_Body, lBodyPool_Singleton, hBodyPool_Singleton
from modules.physEngine.entity_id_groups_controller import EntityIDGroupsController
from modules.ship.shipPool import ShipPool_Singleton


class ScenesController:
        _instance = None # Приватное поле для хранения единственного экземпляра

        def __new__(cls):
                if cls._instance is None:
                        cls._instance = super(ScenesController, cls).__new__(cls)

                return cls._instance



                    


        def next_step(self):
                pass





class Scene(basic_Body):
        def __init__(self, mark_id = None) -> None:
                super().__init__(mark_id)
                self.scene_name = None
                self.loaded = False
                self.stored_description = {}
                self.render_distance = 0



        def next_step(self):
                ships_in_distance = self.get_entities_ids_from_list_in_range(ShipPool_Singleton().ships, self.render_distance, False)
                if (not self.loaded) and ships_in_distance:
                        self.load()
                if (not ships_in_distance) and self.loaded:
                        self.unload()

        def get_description(self):
                return {
                        "loaded": self.loaded,
                        "mark_id": self.mark_id,
                }


        def load(self):
                self.loaded = True

        def unload(self):
                self.loaded = False



                    


