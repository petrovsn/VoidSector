from datetime import datetime, timedelta

passwords = {
    "captain": "pjkjn",
    "navigator": "vtxnf",
    "cannoneer": "vcnbn",
    "engineer": "fdfyn",
    "medic": "ljrnj",
    "admin": "cfvjt",
    "pilot": "rfvbr",
    "master_medic": "jkbnd"
}


class UniversalPasswlrdController:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(
                UniversalPasswlrdController, cls).__new__(cls)
            cls._instance.universal_passwords = {
                "newbvd": True
            }

            cls._instance.universal_password_ttl = timedelta(seconds=30)
            cls._instance._temporary_access_tokens = {}

        return cls._instance
    

    def is_universal(self, password):
        return password in self.universal_passwords
    
    def auth_ws(self, token, password):
        if password in self.universal_passwords:
            if token not in self._temporary_access_tokens:
                self._temporary_access_tokens[token] = datetime.now()+self.universal_password_ttl

    def auth(self, password):
        if password in self.universal_passwords:
            if self.universal_passwords[password]:
                self.universal_passwords[password] = False
                return True    
        return False
    
    def restore(self):
        self.universal_passwords = {
                "newbvd": True}
        self.universal_password_ttl = timedelta(seconds=60)
        self._temporary_access_tokens = {}

    def get_upass_status(self):
        return self.universal_passwords
        
    def is_token_expired(self, token):
        if token not in self._temporary_access_tokens:
            return False

        if self._temporary_access_tokens[token] == None:
            return True

        if datetime.now() > self._temporary_access_tokens[token]:
            self._temporary_access_tokens[token] = None
            return True

        return False


class UserData:
    def __init__(self, username):
        self.username = username
        self.password = ""
        if username in passwords:
            self.password = passwords[username]
        self.roles = {"map_editor": False, "admin": False, "game_master": False, "pilot": False, "captain": False,
                      "navigator": False, "cannoneer": False, "engineer": False, "NPC_pilot": False, "medic": False, "common_radar": False}

    def get_roles(self):
        return self.roles

    def set_role(self, role, state):
        if type(state) != bool:
            state = state.lower() == "true"
        self.roles[role] = state

    def auth(self, password):
        if password == self.password: return True
        if not self.username in ["admin", "pilot", "master_medic"]:
            return UniversalPasswlrdController().auth(password)
        return False
    
    
        


class UsersControler:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UsersControler, cls).__new__(cls)
            cls._instance.users = {}
            cls._temporary_access_tokens = {}
            for username in ["captain", "navigator", "cannoneer", "engineer", "medic"]:
                cls._instance.users[username] = UserData(username)
                for role in ["map_editor", "admin", "game_master", "pilot", "captain", "navigator", "cannoneer", "engineer", "medic", "NPC_pilot"]:
                    cls._instance.users[username].set_role(
                        role, role == username)
                    cls._instance.users[username].set_role(
                        "common_radar", True)

            for username in ["admin", "master_medic", "NPC_pilot"]:
                cls._instance.users[username] = UserData(username)
                for role in ["map_editor", "admin", "game_master", "pilot", "captain", "navigator", "cannoneer", "engineer", "medic", "NPC_pilot", "common_radar"]:
                    cls._instance.users[username].set_role(role, True)

            for username in ['common_radar']:
                cls._instance.users[username] = UserData(username)
                for role in ["common_radar"]:
                    cls._instance.users[username].set_role(role, True)
            for username in ["pilot"]:
                cls._instance.users[username] = UserData(username)
                for role in ["game_master", "captain", "navigator", "cannoneer", "engineer",  "NPC_pilot", "common_radar"]:
                    cls._instance.users[username].set_role(role, True)

        return cls._instance

    def auth(self, username, password):
        if username not in self.users:
            return False
        return self.users[username].auth(password)

    def auth_ws(self, token, password):
        UniversalPasswlrdController().auth_ws(token, password)


    def is_token_expired(self, token):
        return UniversalPasswlrdController().is_token_expired(token)

    def get_state(self):
        result = {}
        for username in self.users:
            result[username] = self.users[username].get_roles()
        return result

    def get_roles_list(self, username):
        result = []
        roles_dict = self.users[username].get_roles()
        for role in roles_dict:
            if roles_dict[role]:
                result.append(role)

        return result

    def set_role(self, username, role, state):
        self.users[username].set_role(role, state)
