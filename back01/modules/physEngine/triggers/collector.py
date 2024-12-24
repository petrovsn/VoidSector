from queue import Queue

class TriggerQueue():
                _instance = None # Приватное поле для хранения единственного экземпляра

                def __new__(cls):
                                if cls._instance is None:
                                                cls._instance = super(TriggerQueue, cls).__new__(cls)
                                                cls._instance.queue = Queue()
                                return cls._instance



                                

                def add(self, trigger_type, initiator, params):
                                self.queue.put({
                                                                "type":trigger_type,
                                                                "initiator":initiator,
                                                                "params":params
                                })

                def get(self):
                                return self.queue.get()



                                
                def empty(self):
                                return self.queue.empty()
