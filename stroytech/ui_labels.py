"""Russian labels and stable values shared by the interface."""
CHOICES = {
    'work': {'Земляные работы': 'excavation', 'Бурение': 'drilling', 'Подъем': 'lifting', 'Перевозка': 'transport', 'Бетонирование': 'concrete'},
    'soil': {'Твердый': 'firm', 'Скала': 'rock', 'Мягкий': 'soft', 'Болото': 'swamp'},
    'weather': {'Сухо': 'dry', 'Дождь': 'rain', 'Слякоть': 'slush'},
}

LABELS = {
    'work': 'Работы',
    'soil': 'Грунт',
    'weather': 'Погода',
    'groundwater': 'Грунтовые воды',
    'near_powerline': 'Рядом ЛЭП',
    'obstacles': 'Препятствия',
    'narrow_access': 'Узкий подъезд',
    'night': 'Ночью',
    'lighting': 'Освещение',
    'duration_hours': 'Длительность, ч',
    'load_t': 'Масса груза, т',
    'radius_m': 'Вылет стрелы, м',
    'angle_deg': 'Угол, °',
    'capacity_table': 'Нет подходящей строки грузовой таблицы',
    'lift_purpose': 'Назначение подъёма',
    'equipment_type': 'Тип техники',
    'heavy': 'Тяжёлая техника',
    'capacity_ok': 'Грузоподъёмность достаточна',
    'access_risk': 'Риск подъезда',
}

PURPOSE = {
    'Груз': 'cargo',
    'Люди и инструмент': 'people',
}

BOOL_FIELDS = ('groundwater', 'near_powerline', 'obstacles', 'narrow_access', 'night', 'lighting')

NUM_FIELDS = ('duration_hours', 'load_t', 'radius_m', 'angle_deg')

STATUS = {
    'suitable': 'Подходит',
    'conditional': 'С условиями',
    'rejected': 'Отклонено',
    'unknown': 'Нужны данные',
    'pending': 'На проверке',
    'conflict': 'Конфликт',
    'approved': 'Подтверждено',
}
