from aiogram import Bot, Dispatcher, types, executor, filters
import api_token
import datetime
import mysql.connector
import datetime
import pytz
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from moviepy.video.io.VideoFileClip import VideoFileClip
from dateutil import parser

# Инициализируем бот
bot = Bot(api_token.TOKEN)

# Инициализируем диспетчер для обработки команд и событий
dp = Dispatcher(bot)

# ----------------------------------------Глобальные переменные -----------------------------------------------------
recipe_name = ''
recipe_time = ''
recipe_ingredients = ''
recipe_instructions = ''
current_page = 0
total_recipes = 0
last_recipe_id = 0
result = []
message = ''
random_recipe_data = []
cursor = None
user_id = ''
username = ''
# --------------------------------------------------------------------------------------------------------------------

# ---------------------------------------Параметры для подключения к БД-----------------------------------------------
db_config = {
    'user': 'lisika31',
    'password': '123321',
    'host': 'localhost',
    'database': 'Cookbook',
    'raise_on_warnings': True
}

# Установка соединения с БД
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()
# --------------------------------------------------------------------------------------------------------------------

# -------------------------------Извлечение command_name из таблицы---------------------------------------------------
query = "SELECT command_name FROM recipes"
conn.ping(reconnect=True)
cursor.execute(query)
result = cursor.fetchall()

st_command = []
for row in result:
    st_command.append(row[0])
# --------------------------------------------------------------------------------------------------------------------

# -------------------------------Глобальные переменные для клавиатур---------------------------------------------------
kb = [
    [KeyboardButton(text='Рецепты'), KeyboardButton(text='Фильтрация')],
    [KeyboardButton(text='Поиск'), KeyboardButton(text='Случайный рецепт'), KeyboardButton(text='Помощь')]
]

kb2 = [
    [KeyboardButton(text='Выпечка'), KeyboardButton(text='Блюда с мясом'), KeyboardButton(text='Закуски')],
    [KeyboardButton(text='Супы'), KeyboardButton(text='Салаты'), KeyboardButton(text='Овощные блюда')],
    [KeyboardButton(text='Блюда из рыбы'), KeyboardButton(text='Гарниры')],
    [KeyboardButton(text='Отменить')]
]

kb_search = [
    [InlineKeyboardButton(text='Поиск по ингредиенту'), InlineKeyboardButton(text='Поиск по названию')],
    [InlineKeyboardButton(text='Отменить')]
]

main_menu_button = KeyboardButton(text='Главное меню')
# --------------------------------------------------------------------------------------------------------------------

# -------------------------Функция для записи информации о пользователе----------------------------------------------
async def write_user_info(user_id, username):
    ekt_tz = pytz.timezone('Asia/Yekaterinburg')
    current_date = datetime.datetime.now(ekt_tz).strftime('%Y-%m-%d %H:%M:%S')
    try:
        cursor.execute("SELECT * FROM users WHERE ID_user = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            conn.ping(reconnect=True)
            cursor.execute("UPDATE users SET data_last = %s WHERE ID_user = %s", (current_date, user_id))
            conn.commit()
        else:
            conn.ping(reconnect=True)
            cursor.execute("INSERT INTO users (id_user, name_user, data_st, data_last) VALUES (%s, %s, %s, %s)",
                           (user_id, username, current_date, current_date))
            conn.commit()
    except Exception as e:
        print("Ошибка при записи информации о пользователе:", e)
# --------------------------------------------------------------------------------------------------------------------


# ---------------------------------------- Функция для извлечения id и ника-------------------------------------------
async def get_user_info(message):
    global user_id, username
    user_id = message.from_user.id
    username = message.from_user.username
    if message.from_user.username is None:
        username = "ник_отсутствует"
# --------------------------------------------------------------------------------------------------------------------

# ------------------------------------------------ Команда /statistics------------------------------------------------
@dp.message_handler(commands=['statistics'])
async def statistics_command(message: types.Message):
    chat_id = message.chat.id
    admin_chat_id = 886254616  # ID чата администратора
    i = 0  # Инициализация счетчика

    if chat_id == admin_chat_id:
        # Выполнение запроса к базе данных
        conn.ping(reconnect=True)
        cursor.execute("SELECT name_user, data_st, data_last FROM users")
        rows = cursor.fetchall()

        # Формирование сообщения с данными из таблицы users
        statistics_text = "Статистика:\n\n"
        for row in rows:
            name_user, data_st, data_last = row
            i += 1  # Увеличение счетчика

            # Форматирование дат в формат dd.mm.yy
            data_st_datetime = parser.parse(data_st)
            data_last_datetime = parser.parse(data_last)
            data_st_formatted = data_st_datetime.strftime("%d.%m.%y %H:%M")
            data_last_formatted = data_last_datetime.strftime("%d.%m.%y %H:%M")

            statistics_text += f"{i}. @{name_user}, {data_st_formatted} - {data_last_formatted}\n"

        await bot.send_message(message.chat.id, statistics_text)
    else:
        await bot.send_message(message.chat.id, "Данная функция доступна только администратору.")
# --------------------------------------------------------------------------------------------------------------------

@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.DOCUMENT, types.ContentType.VIDEO_NOTE, types.ContentType.VENUE, types.ContentType.LOCATION])
async def handle_unsupported_content(message):
    if message.content_type == types.ContentType.PHOTO:
        content_type_name = "изображения"
    elif message.content_type == types.ContentType.DOCUMENT:
        content_type_name = "файлы"
    elif message.content_type == types.ContentType.VIDEO_NOTE:
        content_type_name = "видео-сообщения"
    elif message.content_type == types.ContentType.VENUE:
        content_type_name = "местоположение"
    elif message.content_type == types.ContentType.LOCATION:
        content_type_name = "местоположение"
    await message.reply(f"Извините, я не умею обрабатывать {content_type_name}😔. Ознакомьтесь с возможными командами /help и повторите запрос.")

@dp.message_handler(content_types=[types.ContentType.AUDIO, types.ContentType.STICKER, types.ContentType.VOICE, types.ContentType.CONTACT, types.ContentType.POLL])
async def handle_unsupported_content(message):
    if message.content_type == types.ContentType.AUDIO:
        content_type_name = "аудио"
    elif message.content_type == types.ContentType.STICKER:
        content_type_name = "стикеры"
    elif message.content_type == types.ContentType.VOICE:
        content_type_name = "голосовые сообщения"
    elif message.content_type == types.ContentType.CONTACT:
        content_type_name = "контактную информацию пользователей"
    elif message.content_type == types.ContentType.POLL:
        content_type_name = "опросы"
    await message.reply(f"Извините, я не умею обрабатывать {content_type_name}😔. Ознакомьтесь с возможными командами /help и повторите запрос.")

# -------------------------------------------------- Команда /start --------------------------------------------------
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    global cursor, username, user_id
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    user_id = message.from_user.id
    username = message.from_user.username
    if message.from_user.username is None:
        username = "ник_отсутствует"
    await write_user_info(user_id, username)
    await bot.send_message(message.chat.id,
                           "Привет, я твой личный помощник в кулинарном мире. В себе я собрал все рецепты великолепной "
                           "Юлии Кукса❤️", reply_markup=keyboard)
# --------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------- Команда /help ---------------------------------------------------
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    global cursor
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    helps = f"У Вас возникли трудности?\nНапишите администратору: @lisika31. Или используйте предложенные " \
            f"команды: \n/start – перезапуск \n/help – возможные команды"

    await get_user_info(message)
    await write_user_info(user_id, username)
    await bot.send_message(message.chat.id, helps, reply_markup=keyboard)
# --------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------- Кнопка "Помощь" ---------------------------------------------------
@dp.message_handler(lambda message: message.text == 'Помощь')
async def get_help(message: types.Message):
    global cursor
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    helps = f"У Вас возникли трудности?\nНапишите администратору: @lisika31. Или используйте предложенные " \
            f"команды: \n/start – перезапуск \n/help – возможные команды"

    await get_user_info(message)
    await write_user_info(user_id, username)
    await bot.send_message(message.chat.id, helps, reply_markup=keyboard)
# --------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------- Кнопка "Рецепты" ------------------------------------------------
@dp.message_handler(lambda message: message.text == 'Рецепты')
async def get_recipes(message: types.Message):
    global cursor, keyboard, current_page
    current_page = 0
    conn.ping(reconnect=True)
    cursor = conn.cursor()
    keyboard = InlineKeyboardMarkup(row_width=2)
    prev_button = InlineKeyboardButton(text='Предыдущая', callback_data='prev_page')
    next_button = InlineKeyboardButton(text='Следующая', callback_data='next_page')
    keyboard.add(prev_button, next_button)
    await get_user_info(message)
    await write_user_info(user_id, username)
    await bot.send_message(message.chat.id, "Рецепты:")
    cursor.execute('SELECT COUNT(*) FROM recipes')
    total_recipes = cursor.fetchone()[0]
    query = f'SELECT * FROM recipes LIMIT 5 OFFSET {current_page * 5}'
    cursor.execute(query)
    result = cursor.fetchall()
    response = f"(Страница {current_page + 1}): \n\n"
    for row in result:
        response += f"✨{row[1]}✨\n"
        response += f"Количество порций: {row[8]}\n"
        response += f"Подробнее: /detelis_{row[0]}\n\n"
    await bot.send_message(message.chat.id, response, reply_markup=keyboard)
# -------------------------------------------------------------------------------------------------------------------

# ------------------------------------------- Кнопки "Предыдущая" и "Следующая" -------------------------------------
@dp.callback_query_handler(lambda callback_query: callback_query.data in ['prev_page', 'next_page'])
async def handle_pagination(callback_query: types.CallbackQuery):
    global current_page
    if callback_query.data == 'next_page':
        current_page += 1
    elif callback_query.data == 'prev_page':
        current_page -= 1
    if current_page < 0:
        current_page = 0
    query = f'SELECT * FROM recipes LIMIT 5 OFFSET {current_page * 5}'
    conn.ping(reconnect=True)
    cursor.execute(query)
    result = cursor.fetchall()
    if not result:
        await bot.send_message(callback_query.message.chat.id, "К сожалению, это была последняя страница. "
                                                               "Вернитесь назад")
        return
    response = f"(Страница {current_page + 1}): \n\n"
    for row in result:
        response += f"✨{row[1]}✨\n"
        response += f"Количество порций: {row[8]}\n"
        response += f"Подробнее: /detelis_{row[0]}\n\n"
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text=response, reply_markup=keyboard)
    await bot.answer_callback_query(callback_query.id)
# -------------------------------------------------------------------------------------------------------------------

# ------------------------------------------Кнопка "Главное меню"----------------------------------------------------
@dp.message_handler(lambda message: message.text == 'Главное меню')
async def main_menu(message: types.Message):
    global keyboard
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   one_time_keyboard=True)

    await get_user_info(message)
    await write_user_info(user_id, username)
    await message.answer("Выберите действие из меню:", reply_markup=keyboard)
# -------------------------------------------------------------------------------------------------------------------

# ------------------------------------------Кнопка "Фильтрация"-------------------------------------------------------
@dp.message_handler(lambda message: message.text == 'Фильтрация')
async def get_recipe(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb2)
    await bot.send_message(message.chat.id, "Выберите действие из меню:", reply_markup=keyboard)

@dp.message_handler(
    lambda message: message.text in ['Выпечка', 'Блюда с мясом', 'Закуски', 'Супы', 'Салаты', 'Овощные блюда',
                                     'Блюда из рыбы', 'Гарниры'])
async def get_recipes(message: types.Message):
    filter = message.text
    conn.ping(reconnect=True)
    query = f"SELECT * FROM recipes WHERE View = '{filter}'"
    cursor.execute(query)
    result = cursor.fetchall()
    if not result:
        await bot.send_message(message.chat.id, "Нет рецептов по выбранному фильтру")
        return
    response = ""
    for row in result:
        response += f"✨{row[1]}✨\n"
        response += f"Количество порций: {row[8]}\n"
        response += f"Подробнее: /detelis_{row[0]}\n\n"

    await bot.send_message(message.chat.id, response)
    await get_user_info(message)
    await write_user_info(user_id, username)
# -------------------------------------------------------------------------------------------------------------------

# ------------------------------------------Кнопка "Отменить"-------------------------------------------------------
@dp.message_handler(lambda message: message.text == 'Отменить')
async def main_menu(message: types.Message):
    global keyboard
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Выберите действие из меню:", reply_markup=keyboard)
# -------------------------------------------------------------------------------------------------------------------

# ---------------------------------------Кнопка "Случайный рецепт"---------------------------------------------------
@dp.message_handler(filters.Text(equals='Случайный рецепт'))
async def random_recipe(message: types.Message):
    global cursor, random_recipe_data
    cursor = conn.cursor()
    conn.ping(reconnect=True)
    cursor.execute('SELECT * FROM recipes ORDER BY RAND() LIMIT 1')
    result = cursor.fetchone()
    if result:
        recipe_id = result[0]
        recipe_name = result[1]
        recipe_ingredients = result[2]
        recipe_instructions = result[3]
        recipe_time = result[4]
        recipe_view = result[5]
        recipe_energy = result[7]
        recipe_portions = result[8]
        random_recipe_data = [recipe_id, recipe_name, recipe_ingredients, recipe_instructions,
                              recipe_time, recipe_view, recipe_energy, recipe_portions]
        response = f"🌟 Название: {recipe_name} 🌟\n\n"
        response += f"Количество порций: {recipe_portions}\n"
        response += f"Время приготовления: {recipe_time}\n\n"
        details_button = InlineKeyboardButton(text='Подробнее', callback_data=f'details_{recipe_id}')
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[details_button]])
        photo_path = f'Files/{recipe_name}.PNG'
        with open(photo_path, 'rb') as photo:
            await bot.send_photo(message.chat.id, photo, caption=response, reply_markup=inline_keyboard)
    else:
        await message.reply("Извините, случайный рецепт не найден.")
# ------------------------------------------------------------------------------------------------------------------

# ------------------------------------------------- Команда /detelis_ -----------------------------------------------
@dp.message_handler(lambda message: message.text.startswith('/') and message.text[1:] in st_command)
async def recipe_details_callback(message: types.Message):
    global cursor
    command = message.text[1:]
    query1 = "SELECT Name, Ingredients, Preparation, energy_value  FROM recipes WHERE command_name = %s"
    conn.ping(reconnect=True)
    cursor.execute(query1, (command,))
    recipe_data = cursor.fetchone()
    response = ""
    if recipe_data:
        recipe_name = recipe_data[0]
        recipe_ingredients = recipe_data[1]
        recipe_instructions = recipe_data[2]
        recipe_energy = recipe_data[3]
        response += f"✨" + recipe_name + f"✨\n\n"
        response += f"Ингредиенты: \n" + recipe_ingredients + f"\n\n"
        response += f"Приготовление: \n" + recipe_instructions + f"\n\n"
        response += f"Пищевая ценность (100 грамм): \n" + recipe_energy + f"\n\n"
        video_path = 'Files/' + recipe_name + '.mp4'
        video_clip = VideoFileClip(video_path)
        original_width = video_clip.size[0]
        original_height = video_clip.size[1]
        video_clip.close()
        back_button = InlineKeyboardButton(text="Назад", callback_data="back")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
    with open(video_path, 'rb') as video:
        await bot.send_video(message.chat.id, video, width=original_width, height=original_height,
                             caption=response, reply_markup=keyboard)
    recipe_chat_id = message.chat.id
# -------------------------------------------------------------------------------------------------------------------

# --------------------------------------Команда /details_-----------------------------------------------------------
@dp.callback_query_handler(lambda query: query.data.startswith('details_'))
async def recipe_details_callback(query: types.CallbackQuery):
    global random_recipe_data
    recipe_name = random_recipe_data[1]
    recipe_ingredients = random_recipe_data[2]
    recipe_instructions = random_recipe_data[3]
    recipe_energy = random_recipe_data[6]

    response = ""
    response += f"✨" + recipe_name + f"✨\n\n"
    response += f"Ингредиенты: \n" + recipe_ingredients + f"\n\n"
    response += f"Приготовление: \n" + recipe_instructions + f"\n\n"
    response += f"Пищевая ценность (100 грамм): \n" + recipe_energy + f"\n\n"

    video_path = f'Files/{recipe_name}.mp4'
    video_clip = VideoFileClip(video_path)
    original_width = video_clip.size[0]
    original_height = video_clip.size[1]
    video_clip.close()

    back_button = InlineKeyboardButton(text="Назад", callback_data="back")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])

    with open(video_path, 'rb') as video:
        sent_message = await bot.send_video(query.message.chat.id, video, width=original_width,
                                            height=original_height,
                                            caption=response, reply_markup=keyboard)
    recipe_chat_id = query.message.chat.id
# ------------------------------------------------------------------------------------------------------------------

# -----------------------------------------Кнопка "Назад"-----------------------------------------------------------
@dp.callback_query_handler(lambda query: query.data == "back")
async def back_callback(query: types.CallbackQuery):

    await query.message.delete()
# ------------------------------------------------------------------------------------------------------------------

# -------------------------------------------Кнопка "Поиск"---------------------------------------------------------
@dp.message_handler(lambda message: message.text == 'Поиск')
async def get_recipes(message: types.Message):
    keyboard = ReplyKeyboardMarkup(keyboard=kb_search, resize_keyboard=True)
    await get_user_info(message)
    await write_user_info(user_id, username)
    await message.answer("Выберите каким способом будет происходить поиск:", reply_markup=keyboard)


ingredient_handler_active = False
name_handler_active = False


@dp.message_handler(lambda message: message.text == 'Поиск по ингредиенту' and not ingredient_handler_active)
async def search_by_ingredient_handler(message: types.Message):
    global ingredient_handler_active
    ingredient_handler_active = True

    await get_user_info(message)
    await write_user_info(user_id, username)
    await message.answer("Введите ингредиент для поиска:")


@dp.message_handler(lambda message: ingredient_handler_active, state="*")
async def handle_ingredient(message: types.Message):
    ingredient = message.text
    await search_by_ingredient(message, ingredient)


async def search_by_ingredient(message: types.Message, ingredient: str):
    global ingredient_handler_active, keyboard
    conn.ping(reconnect=True)
    cursor.execute("SELECT * FROM recipes WHERE Ingredients LIKE %s", ('%' + ingredient + '%',))
    recipes = cursor.fetchall()
    keyboard = ReplyKeyboardMarkup(keyboard=kb_search, resize_keyboard=True)
    if recipes:
        response = ""
        for row in recipes:
            response += f"✨{row[1]}✨ \nКоличество порций: {row[8]} \nПодробнее: /detelis_{row[0]}\n\n"
        await bot.send_message(message.chat.id, response, reply_markup=keyboard)
    
        await get_user_info(message)
        await write_user_info(user_id, username)
    else:
        await message.answer(f"К сожалению, рецептов с ингредиентом '{ingredient}' не найдено. Повторите запрос.")
    ingredient_handler_active = False


@dp.message_handler(lambda message: message.text == 'Поиск по названию' and not name_handler_active)
async def search_by_Name_handler(message: types.Message):
    global name_handler_active
    name_handler_active = True

    await get_user_info(message)
    await write_user_info(user_id, username)
    await message.answer("Введите часть или полное название для поиска:")


@dp.message_handler(lambda message: name_handler_active, state="*")
async def handle_Name(message: types.Message):
    name = message.text
    await search_by_Name(message, name)


async def search_by_Name(message: types.Message, Name: str):
    global name_handler_active, keyboard
    conn.ping(reconnect=True)
    cursor.execute("SELECT * FROM recipes WHERE Name LIKE %s", ('%' + Name + '%',))
    keyboard = ReplyKeyboardMarkup(keyboard=kb_search, resize_keyboard=True)
    recipes = cursor.fetchall()
    if recipes:
        response = ""
        for row in recipes:
            response += f"✨{row[1]}✨ \nКоличество порций: {row[8]} \nПодробнее: /detelis_{row[0]}\n\n"
        await bot.send_message(message.chat.id, response, reply_markup=keyboard)
    
        await get_user_info(message)
        await write_user_info(user_id, username)
    else:
        await message.answer(f"К сожалению, рецептов с названием '{Name}' не найдено. Повторите запрос.")
    name_handler_active = False

# ------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------Ответ бота------------------------------------------------------
@dp.message_handler()
async def handle_unknown_message(message: types.Message):

    await get_user_info(message)
    await write_user_info(user_id, username)
    await message.reply("Извините, я Вас не понимаю😔. Ознакомтесть с возможныи командами /help и повторите запрос.")
# ----------------------------------------------------------------------------------

# Функция для запуска бота
def start_bot():
    executor.start_polling(dp, skip_updates=False)

# Запускаем бота
if __name__ == '__main__':
    start_bot()
