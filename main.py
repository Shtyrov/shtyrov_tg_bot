from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from API_TOKEN import API_TOKEN
from Calendar import GeneralCalendar, UserCalendar
from locale import setlocale, LC_ALL

setlocale(LC_ALL, 'ru_RU.UTF-8')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
cl = GeneralCalendar('data.json')

REQESTS = {}


@dp.message_handler(commands=['start', 'help'])    # Старт и вывод клавиатурных кнопок
async def send_welcome(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Показать все события"),
            types.KeyboardButton(text="Показать мои события"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer("Привет!\n Это бот, агрегирующий академические события в области философии",
                         reply_markup=keyboard)


@dp.message_handler(commands=list(cl.all_events_ids))    # Детализация событий
async def give_detailed_information(message: types.Message):
    event = cl.get_event(message.text.strip('/'))
    user_id = message.from_user.id

    inline_button = InlineKeyboardMarkup(row_width=2)
    url_button = InlineKeyboardButton(text='Подробнее:', url=event.link)  # Не будет ли сбой если у события нет ссылки?
    inline_button.add(url_button)

    if user_id not in event.audience:
        add_button = InlineKeyboardButton(text='Добавить:', callback_data=f'add_to_user_calendar:{event.id}')
        inline_button.add(add_button)
    else:
        dell_button = InlineKeyboardButton(text='Удалить:', callback_data=f'remove_from_user_calendar:{event.id}')
        inline_button.add(dell_button)

    await message.answer(event.get_full_description(), reply_markup=inline_button)


@dp.callback_query_handler(lambda c: c.data.startswith('add_to_user_calendar'))    # Эта функция перехватывает запрос из inline-клавиатуры. ВОПРОС - какому аргументу передается лямбда=функция? (при указании аргумента 'func' выдает ошибку)
async def process_callback_add_event(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    event_id = callback_query.data.split(":")[1]
    user_cl = UserCalendar(cl, user_id)

    user_cl.add_event(event_id)

    await bot.answer_callback_query(callback_query.id)    # Что делает эта строчка?
    await bot.send_message(callback_query.from_user.id, f'Добавили сообытие /{event_id} в ваш календарь')


@dp.callback_query_handler(lambda c: c.data.startswith('remove_from_user_calendar'))    # Эта функция перехватывает запрос из inline-клавиатуры. ВОПРОС - какому аргументу передается лямбда=функция? (при указании аргумента 'func' выдает ошибку)
async def process_callback_add_event(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    event_id = callback_query.data.split(":")[1]
    user_cl = UserCalendar(cl, user_id)

    user_cl.del_event(event_id)

    await bot.answer_callback_query(callback_query.id)    # Что делает эта строчка?
    await bot.send_message(callback_query.from_user.id, f'Удалили сообытие /{event_id} из вашего календаря')


@dp.message_handler()
async def handler(message: types.Message):   # Обработка запросов. ВСЕГДА ИДЕТ ПОСЛЕ ОБРАБОТКИ СЛЕШЕВЫХ ЗАПРОСОВ

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
