from datetime import datetime
from random import randint


class Conference:
    def __init__(self, date, title, place, format=None, deadline=None, description=None, price=None, link=None, audience=None, id=None):
        if type(date) == str:
            try:
                date = datetime.strptime(date, '%y%m%d')
            except Exception:
                raise ValueError('Введенная дата не соответствует формату')
        self.date = date

        if deadline and type(deadline) == str:
            try:
                deadline = datetime.strptime(deadline, '%y%m%d')
            except Exception:
                raise ValueError('Введенная дата не соответствует формату')
        self.deadline = deadline

        self.title = title
        self.place = place
        self.format = format
        self.description = description
        self.price = price
        self.link = link    # Этот параметр должен быть обязательным

        if not audience:
            audience = []
        self.audience = audience
        if not id:
            id = datetime.strftime(self.date, '%y%m%d') + '_' + str(randint(0, 99)) + chr(randint(65, 90))
        self.id = id

    def __eq__(self, other):
        self_params = {k: v for k, v in self.__dict__.items() if k != 'id'}
        other_params = {k: v for k, v in other.__dict__.items() if k != 'id'}
        return self_params == other_params

    def json_format(self):  # Эта функция не фозвращает отдельный календарь, а меняет параметры события!!!
        json_file = {}
        for k, v in self.__dict__.items():
            if k in ('date', 'deadline') and v is not None:
                v = datetime.strftime(getattr(self, k), '%y%m%d')
            json_file[k] = v
        return json_file

    def get_date(self):
        return self.date.strftime('%d %b %Y')

    def get_brief_description(self):
        return f'{self.title}\nПодробнее: /{self.id}'

    def get_full_description(self):
        result = f'{self.title}\n' \
                 f' * Когда: {self.get_date()}\n' \
                 f' * Где: {self.place}\n' \
                 f' * Дедлайн: {self.deadline.strftime("%d %b %Y") if self.deadline else "отсутствует"}\n' \
                 f' * Формат участия: {self.format if self.format else "не уточнено"}\n' \
                 f' * Описание: {self.description if self.description else "отсутствует"}\n' \
                 f' * Цена: {self.price if self.price else "бесплатно"}\n'
        return result
