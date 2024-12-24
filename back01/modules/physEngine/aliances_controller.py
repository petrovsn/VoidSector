class AlianceController:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AlianceController, cls).__new__(cls)
            cls._instance.ships = {}
        return cls._instance

    def register(self, mark_id):
        self.ships[mark_id] = [mark_id]

    def add(self, mark_id, alias_id):
        self.ships[mark_id].append(alias_id)

    def remove(self, mark_id, alias_id):
        if mark_id in self.ships:
            if alias_id in self.ships[mark_id]:
                self.ships[mark_id].remove(alias_id)

    def get_aliance(self, mark_id):
        if mark_id not in self.ships:
            return []
        return self.ships[mark_id]
