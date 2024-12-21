class SolarFlareDefendZone:
                _instance = None # Приватное поле для хранения единственного экземпляра

                def __new__(cls):
                                if cls._instance is None:
                                                cls._instance = super(SolarFlareDefendZone, cls).__new__(cls)
                                                cls._instance.entities = []
                                                cls._instance.__current = 0
                                return cls._instance

                def add(self, mark_id):
                                if mark_id not in self.entities:
                                                self.entities.append(mark_id)



                                
                def remove(self, mark_id):
                                if mark_id in self.entities:
                                                self.entities.remove(mark_id)

                def get_defended(self):
                                return self.entities

                def clear(self):
                                self.entities = []
