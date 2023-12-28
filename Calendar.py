import json
from datetime import datetime, date
from Event import Conference


class GeneralCalendar:
    instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.instance:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, db: str):
        self.db = db  # Указывается путь к файлу с базой данных

        self.all_events_ids = set()
        for lst in self.load_db().values():
            for e in lst:
                self.all_events_ids.add(e['id'])
        # self.update_bd()    # Пока не включать

    def load_db(self):    # возвращает данные из бд
        with open(self.db, 'r', encoding='UTF-8') as old_file:
            return json.load(old_file)

    def dump_db(self, data):    # загружает данные в бд
        with open(self.db, 'w', encoding='UTF-8') as new_file:
            json.dump(data, new_file)

    def update_bd(self):
        calendar = self.load_db()
        # for k in calendar.keys():
        #    if datetime.strptime(k, '%y%m%d') < date.today():
        #        del calendar[k]
        calendar = sorted(calendar)
        self.dump_db(calendar)
        # Доделать перекидывание устаревших событий в отдельный файл
        # Если существуют даты, для которых нет ни одного события, то такие элементы должны быть удалены

    def add_event(self, event):    # переводит событеи в json формат и если такого события нет в бд, добавляет его
        calendar = self.load_db()
        event_json = event.json_format()
        dt = event_json['date']
        calendar.setdefault(dt, [])
        if event not in [Conference(**e) for e in calendar[dt]]:
            calendar[dt].append(event_json)
            self.all_events_ids.add(event.id)
            self.dump_db(calendar)

    def del_event(self, event):
        calendar = self.load_db()
        event_json = event.json_format()
        dt = event_json['date']
        if event in [Conference(**e) for e in calendar.get(dt, [])]:
            calendar[dt].remove(event_json)
        # Доделать логику удаления события
        # Удалять id из all_id
        self.dump_db(calendar)

    def get_event(self, event_id):
        calendar = self.load_db()
        for lst in calendar.values():
            for json_event in lst:
                if json_event['id'] == event_id:
                    return Conference(**json_event)

    def get_all_events_test(self):
        calendar = self.load_db()
        result = []
        for dt, lst in calendar.items():
            for json_event in lst:
                result.append(Conference(**json_event))
        return result

    def get_all_events(self):
        calendar = self.load_db()
        answer = ''
        for dt, lst in calendar.items():    # дата выдается в неправильном формате
            answer += dt + '\n'
            for json_event in lst:
                answer += '* ' + Conference(**json_event).get_brief_description() + '\n'
            answer += '\n'
        return answer


class UserCalendar:
    def __init__(self, general_calendar: GeneralCalendar, user_id):
        self.user_id = user_id
        self.db = general_calendar
        self.all_event_ids = []

        self.all_event_ids = set()
        for lst in self.db.load_db().values():
            for e in lst:
                if self.user_id in e['audience']:
                    self.all_event_ids.add(e['id'])

    def add_event(self, event_id):
        calendar = self.db.load_db()
        for lst in calendar.values():
            for json_event in lst:
                if json_event['id'] == event_id:
                    json_event['audience'].append(self.user_id)
        self.db.dump_db(calendar)

    def del_event(self, event_id):
        calendar = self.db.load_db()
        for lst in calendar.values():
            for json_event in lst:
                if json_event['id'] == event_id:
                    json_event['audience'].remove(self.user_id)
        self.db.dump_db(calendar)

    def get_all_events(self):
        calendar = self.db.load_db()
        answer = ''
        for dt, lst in calendar.items():    # дата выдается в неправильном формате
            if any(map(lambda e: self.user_id in e['audience'], lst)):
                answer += dt + '\n'
            else:
                continue
            for json_event in lst:
                if self.user_id in json_event['audience']:
                    answer += '* ' + Conference(**json_event).get_brief_description() + '\n'
            answer += '\n'
        if not answer:
            return 'В вашем календаре нет событий'
        return answer

    def get_all_events_test(self):
        calendar = self.db.load_db()
        result = []
        for dt, lst in calendar.items():
            for json_event in lst:
                if self.user_id in json_event['audience']:
                    result.append(Conference(**json_event))
        return result