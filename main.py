from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from API_TOKEN import API_TOKEN
from Calendar import GeneralCalendar, UserCalendar
from locale import setlocale, LC_ALL

import plotly.express as px
import pandas as pd
import kaleido


setlocale(LC_ALL, 'ru_RU.UTF-8')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
cl = GeneralCalendar('data.json')

REQESTS = {}


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Показать все события"),
            types.KeyboardButton(text="Показать мои события"),
            types.KeyboardButton(text="Показать карту")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer("Привет!\n Это бот, агрегирующий академические события в области философии",
                         reply_markup=keyboard)


@dp.message_handler(commands=list(cl.all_events_ids))
async def give_detailed_information(message: types.Message):
    event = cl.get_event(message.text.strip('/'))
    user_id = message.from_user.id

    inline_button = InlineKeyboardMarkup(row_width=2)
    url_button = InlineKeyboardButton(text='Подробнее:', url=event.link)
    inline_button.add(url_button)

    if user_id not in event.audience:
        add_button = InlineKeyboardButton(text='Добавить:', callback_data=f'add_to_user_calendar:{event.id}')
        inline_button.add(add_button)
    else:
        dell_button = InlineKeyboardButton(text='Удалить:', callback_data=f'remove_from_user_calendar:{event.id}')
        inline_button.add(dell_button)

    await message.answer(event.get_full_description(), reply_markup=inline_button)


@dp.callback_query_handler(lambda c: c.data.startswith('add_to_user_calendar'))
async def add_event(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    event_id = callback_query.data.split(":")[1]
    user_cl = UserCalendar(cl, user_id)

    user_cl.add_event(event_id)

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f'Добавили сообытие /{event_id} в ваш календарь')


@dp.callback_query_handler(lambda c: c.data.startswith('remove_from_user_calendar'))
async def remove_event(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    event_id = callback_query.data.split(":")[1]
    user_cl = UserCalendar(cl, user_id)

    user_cl.del_event(event_id)

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f'Удалили сообытие /{event_id} из вашего календаря')


@dp.message_handler()
async def handler(message: types.Message):

    if message.text in ('Показать все события', 'Показать мои события'):

        user_id = message.from_user.id
        REQESTS[user_id] = {'all': {}, 'own': {}}
        events, key = [], ''

        if message.text == 'Показать все события':
            events = cl.get_all_events_test()
            key = 'all'
        elif message.text == 'Показать мои события':
            events = UserCalendar(cl, user_id).get_all_events_test()
            if not events:
                await message.answer('В вашем календаре пока нет событий')
            key = 'own'

        curr_page = 1
        page = []
        for e in events:
            page.append(e)
            if len(page) == 4:    # кол-во событий на странице
                REQESTS[user_id][key].setdefault(curr_page, []).extend(page)
                page = []
                curr_page += 1
        if page:
            REQESTS[user_id][key].setdefault(curr_page, []).extend(page)

        answer = ''
        for e in REQESTS[user_id][key][1]:
            answer += e.get_date() + '\n' + '* ' + e.get_brief_description() + '\n\n'

        markup = InlineKeyboardMarkup().add(InlineKeyboardButton(" ", callback_data=f" "),
                                            InlineKeyboardButton("2>", callback_data=f"turn_page:2:{key}")
                                            if len(REQESTS[user_id][key]) > 1 else
                                            InlineKeyboardButton(" ", callback_data=f" "))

        await message.answer(answer, reply_markup=markup)

    if message.text == 'Показать карту':
        data = {}
        for e in cl.get_all_events_test():
            data.setdefault(e.place, 0)
            data[e.place] += 1

        df = pd.DataFrame.from_dict(data, orient='index', columns=['Количество конференций'])

        coords = {'Москва': (55.755773, 37.618423),
                  'Санкт-Петербург': (59.938806, 30.314278),
                  'Екатеринбург': (56.838002, 60.597295),
                  'Новосибирск': (55.028739, 82.90692799999999),
                  'Казань': (55.795793, 49.106585),
                  'Волгоград': (48.707103, 44.516939),
                  'Ростов-на-Дону': (47.227151, 39.744972),
                  'Нижний Новгород': (56.323902, 44.002267),
                  'Владивосток': (43.134019, 131.928379)}

        df['Город'] = df.index
        df['lat'] = [coords[city][0] for city in data]
        df['lon'] = [coords[city][1] for city in data]

        fig = px.scatter_mapbox(df, lat='lat', lon='lon', hover_name='Город', hover_data=['Количество конференций'],
                                size='Количество конференций', zoom=1, height=400)

        fig.update_layout(mapbox_style='open-street-map')

        fig.show()
        fig.write_image("map.png")
        with open('map.png', 'rb') as photo:
            await message.answer_photo(photo)


@dp.callback_query_handler(text_startswith="turn_page")
async def page_turning(call: types.CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    page_number = int(call.data.split(":")[1])
    key = call.data.split(":")[2]
    next_button, prev_button = ' ', ' '

    if page_number < max(REQESTS[user_id][key]):
        next_button = page_number + 1
    if page_number > min(REQESTS[user_id][key]):
        prev_button = page_number - 1

    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton(f'<{prev_button}' if prev_button != ' ' else prev_button,
                             callback_data=f'turn_page:{prev_button}:{key}'),
        InlineKeyboardButton(f'{next_button}>' if next_button != ' ' else next_button,
                             callback_data=f'turn_page:{next_button}:{key}'),
    )

    answer = ''
    for e in REQESTS[user_id][key][page_number]:
        answer += e.get_date() + '\n' + '* ' + e.get_brief_description() + '\n\n'

    await call.message.edit_text(answer, reply_markup=markup)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
