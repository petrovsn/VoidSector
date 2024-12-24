class EntityIDGroupsController:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EntityIDGroupsController, cls).__new__(cls)
            cls._instance.categories = {
                "is_station": [],
                "radar_detectable": [],
                "id_labels_detectable": [],
                "is_ships": [],
                "interactable": [],
                "stationary_orbit": [],
            }
        return cls._instance

    def get(self, category):
        if category not in self.categories:
            if category == "is_station":
                self.categories[category] = []
        return self.categories[category]

    def add(self, mark_id, categories):
        for category in categories:
            if category in self.categories:
                if mark_id not in self.categories[category]:
                    self.categories[category].append(mark_id)
            else:
                self.categories[category] = [mark_id]

    def remove(self, mark_id):
        if mark_id == "Nuestra Bien[debris]":
            return
        for category in self.categories:
            if mark_id in self.categories[category]:
                self.categories[category].remove(mark_id)

    def clear(self):
        self.categories = {
            "radar_detectable": [],
            "id_labels_detectable": [],
            "is_ships": [],
            "interactable": [],
            "stationary_orbit": [],
        }
