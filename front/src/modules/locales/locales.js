

const locales = {
    //shafts
    "ProjectileLauncher Control": "Торпедный аппарат",
    "load": "Загрузить",
    "unload": "Выгрузить",
    "SHAFT": "ПУСКОВАЯ",
    "auto_toggle": "авто-переключение",
    "auto_reload": "авто-перезарядка",


    //Projectile constructor
    "Projectile constructor": "Конструктор торпед",
    //Projectile Components
    "thruster": "Двигатель",
    "timer": "Таймер активации",
    "inhibitor": "Замедлитель",
    "explosive": "Взрывчатка",
    "emp": "ЭМП-излучатель",
    "entities_detection": "Детектор кораблей",
    "projectiles_detection": "Детектор снарядов",
    "buster": "Ускоритель",
    "detonator": "Детонатор",
    "decoy": "Приманка",
    //blueprints
    "SAVE": "Сохранить",
    "DELETE": "Удалить",


    //Projectile Stats
    "activation_time": "Макс.время до активации",
    "cost": "Стоимость",
    "emp_radius": "Радиус ЭМП-поражения",
    "explosion_radius/damage": "Радиус/Макс.урон взрыва",
    "projectiles_detection_radius": "Радиус обнаружения снарядов",
    "ship_detection_radius": "Радиус обнаружения кораблей",
    "speed_up": "Скорость",
    "ttl_time": "Активное время",
    "details": "К-во деталей",
    "velocity_penalty": "Управляемость",

    //Production sm
    "Production_sm": "Автофабрика",
    "metal": "Металл",
    "volume": "Склад изделий",
    "cancel_item": "Отменить производство",
    "clear_production": "Очистить очередь",


    //Radar control
    "Radar control": "Сканеры дальнего радиуса действия",
    "distant_arc": "Фокусировка",
    "distant_dir": "Направление",


    //Medic station
    "Hospital Crew Control": "Состояние здоровья экипажа мостика",
    "Hospital NPC Crew Control": "Состояние здоровья рядового экипажа",
    "humans in hospital": "Мест в лазарете(занято/всего)",
    "plague_phase": "Фаза чумы",
    "plague_time2next_level": "До следующей фазы",

    "health_state_HP9": "???",
    "health_state_HP8": "Норма",
    "health_state_HP7": "Легкое ранение",
    "health_state_HP6": "Легкое ранение",
    "health_state_HP5": "Легкое ранение",
    "health_state_HP4": "Тяжелое ранение",
    "health_state_HP3": "Тяжелое ранение",
    "health_state_HP2": "Тяжелое ранение",
    "health_state_HP1": "!Критическое!",


    "health_state_MP9": "",
    "health_state_MP8": "Норма",
    "health_state_MP7": "Норма",
    "health_state_MP6": "Норма",
    "health_state_MP5": "Легкая усталость",
    "health_state_MP4": "Легкая усталость",
    "health_state_MP3": "Сильная усталость",
    "health_state_MP2": "Сильная усталость",
    "health_state_MP1": "!Критическое!",

    "can_be_cured":"Можно ввести лекарство",

    //Названия систем
    "engine_sm": "Двигатели",
    "launcher_sm": "Торпедный аппарат",
    "radar_sm": "Сканеры",
    "resources_sm": "Внутренние системы",
    "energy_sm": "Реактор",

    //Energy control
    "Energy control": "Реактор",


    //Crew control
    "CrewControl": "Экипаж корабля",
    "total_crew": "Общая численность",
    "free_crew": "Свободно",
    "hospital": "В госпитале",
    "idle":"Отдых",

    //CrewTeams
    "smith":"Сжт.Смит",
    "johnson":"Сжт.Джонсон",
    "wake":"Сжт.Уэйк",
    "sharp":"Сжт.Шарп",

    //Alliance control
    "Aliance_controller":"Панель свой/чужой",
    "mark_as_allias":"Добавить",

    //Engineer 
    "assign_team": "Назначить рем.команду",
    "hp": "Целостность",
    "upgrade_level": "Уровень апгрейда",
    "Release_team":"Отправить на отдых",

    //Engine system
    "Acceleration Control": "Управление двигателем",
    "speed": "Скорость",
    "direction": "Курс",
    "deltaV": "дельта-V",

    "prediction_depth": "Прогноз",
    "engine_power": "Мощность",
    "overheat": "Перегрев",

    //InteractionControl
    "InteractionControl": "Управление захватом",

    //roles
    "username": "Офицер",
    "captain": "Капитан",
    "navigator": "Навигатор",
    "cannoneer": "Канонир",
    "engineer": "Инженер",
    "medic": "Медик",


    //radar
    "toogle_id_labels": "Просмотр идентифкаторов",
    "POS": "Координаты",
    "CURSOR_POS": "Координаты курсора",
    "SCALE": "Масштаб",
    "common_radar":"Общий радар",


    //CapPointsController
    "CapPointsController": "Навигационные метки",
    "MarkLetter": "Метка",
    "Position": "Координаты",
    "Status": "Статус",
    "select": "Поставить",
    "deaсtivate": "Сбросить",

    //solar_flares
    "time_to_flare": "До начала Вспышки[c]",
    "time_to_next_sf_phase": "До окончания вспышки[c]",
    "sf_probability": "Вероятность вспышки",
    "low":"Низкая",
    "high":"Высокая"
}


export function get_locales(s) {
    if (s in locales) {
        return locales[s]
    }
    return s
}
