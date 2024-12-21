

import configparser
import functools
import traceback
from queue import Queue


class Command:
    def __init__(self, command_json):
        self.json = command_json

    def contains_level(self, level_keyword):
        return level_keyword in self.json["level"]

    def get_target_id(self, level_keyword):

        levels = self.json["level"].split('.')
        targets = self.json["target_id"].split('.')
        for i, level_name in enumerate(levels):
            if level_name == level_keyword:
                return targets[i]
        return None

    def get_params(self):
        return self.json["params"]

    def get_action(self):
        return self.json["action"]


class CommandQueue:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CommandQueue, cls).__new__(cls)
            cls._instance.cmd_queue = Queue()

        return cls._instance

    def add_command(self, cmd: Command):
        self.cmd_queue.put(cmd)

    def is_empty(self):
        return self.cmd_queue.empty()

    def get_next(self):
        return self.cmd_queue.get()


def catch_exception(function):
    from functools import wraps

    @functools.wraps(function)
    def wrapper(*args, **kw):
        try:
            result = function(*args, **kw)
            return result
        except Exception as e:
            pass
    return wrapper


def get_dt_ms(t1, t2):
    return round((t2-t1).microseconds/1000000, 4)


class ConfigLoader:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance.config = configparser.ConfigParser()
            cls._instance.filename = "configs/config.ini"
            cls._instance.config.read("configs/config.ini")

        return cls._instance

    def update(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.filename)
        
    def get_main_ship_id(self):
        return "Sirocco"

    def get(self, param_string, type=str):
        tmp = self.config
        for key in param_string.split('.'):
            tmp = tmp[key]

        if type == list:
            return [float(a) for a in tmp.split()]
        return type(tmp)

    def proceed_command(self, command: Command):
        params = command.get_params()
        action = command.get_action()
        match action:
            case "save":
                self.save(params["filename"], params["config_data"])
            case "load":
                self.load(params["filename"])

    def load(self, filename):
        self.filename = f"configs/{filename}"
        self.update()

    def save(self, filename, config_data):
        config_object = configparser.ConfigParser()
        sections = config_data.keys()
        for section in sections:
            config_object.add_section(section)
        for section in sections:
            inner_dict = config_data[section]
            fields = inner_dict.keys()
            for field in fields:
                value = inner_dict[field]
                config_object.set(section, field, str(value))

        file = open("configs/"+filename+".ini", "w")
        config_object.write(file)
        file.close()
        # self.config = configparser.ConfigParser()
        # self.config.read(f"configs/{filename}")


class PerformanceCollector:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerformanceCollector, cls).__new__(cls)
            cls._instance.data = {}

        return cls._instance

    def add(self, key, timestep):
        if key not in self.data:
            self.data[key] = 0
        self.data[key] = self.data[key]+timestep

    def get(self):
        return self.data

    def clear(self):
        for k in self.data:
            self.data[k] = 0


class CommandLogger:
    _instance = None  # Приватное поле для хранения единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CommandLogger, cls).__new__(cls)

            cls._instance.commands = []
            cls._instance.commands_stats = {}

        return cls._instance

    def add(self, cmd: Command):
        action = cmd.get_action()
        if action not in self.commands_stats:
            self.commands_stats[action] = 0
        self.commands_stats[action] = self.commands_stats[action] + 1
        self.commands.append(cmd.json)

    def get_stats(self):
        return {
            "stats": self.commands_stats,
            "last_cmds": self.commands[-20:]
        }
