class MarksCollector:
                _instance = None # Приватное поле для хранения единственного экземпляра

                def __new__(cls):
                                if cls._instance is None:
                                                cls._instance = super(MarksCollector, cls).__new__(cls)
                                                cls._instance.data = {}

                                return cls._instance



                                
                def add(self, category, mark_id):
                                if category not in self.data: self.data[category]=[]
                                self.data[category].append(mark_id)



                                
                def get(self,category):
                                return self.data[category]



                                
                def clear(self):
                                self.data = {}

                def remove(self, mark_id):
                                for category in self.data:
                                                self.data[category].remove(mark_id)
