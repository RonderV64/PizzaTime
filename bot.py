import telebot
import sqlite3
from datetime import datetime
from telebot import types

bot = telebot.TeleBot('7322289325:AAEH0-OsjN6Fd__yj9ugVYxivyINCPDm7uc')
conn = sqlite3.connect('bd.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы для хранения сообщений, если она еще не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, 
user_name TEXT, 
pizza TEXT,  
address TEXT, 
number INTEGER, 
time DATETIME)''')
conn.commit()

# Статусы для отслеживания состояния пользователя
USER_STATE = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Выбрать пиццу")
    button2 = types.KeyboardButton("Время доставки")
    button3 = types.KeyboardButton("Наш адрес")
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, "Привет! Это лучшая пиццерия города Саратов!\nДля выбора пиццы - нажми на кнопку ниже.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    
    if message.text == "Выбрать пиццу":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button4 = types.KeyboardButton("Четыре сыра")
        button5 = types.KeyboardButton("Авторская")
        button6 = types.KeyboardButton("Пепперони")
        button7 = types.KeyboardButton("Маргарита")
        button8 = types.KeyboardButton("На главную")
        button9 = types.KeyboardButton("Отменить заказ")
        markup.add(button4, button5, button6, button7, button9)
        bot.send_message(chat_id, "Отлично! Выберите пиццу.", reply_markup=markup)
    elif message.text in ["Четыре сыра", "Авторская", "Пепперони", "Маргарита"]:
        user_pizza = message.text
        user_name = message.from_user.username if message.from_user.username else "Без имени"
        cursor.execute('INSERT INTO messages (user_name, pizza ) VALUES (?, ?)', (user_name, user_pizza))
        conn.commit()
        USER_STATE[chat_id] = "WAITING_FOR_ADDRESS"
        bot.send_message(chat_id, "Укажите адрес доставки, строго по примеру: 'Г. Саратов, ул.Петрова, д.25, кв.25, эт.25'.\nОбращаем Ваше внимание, что доставка осуществляется только по г. Саратов.")
    elif chat_id in USER_STATE and USER_STATE[chat_id]  == "WAITING_FOR_ADDRESS" and message.text == "Отменить заказ":   
            del USER_STATE[chat_id]
            start_message(message)
            user_name = message.from_user.username if message.from_user.username else "Без имени"
            cursor.execute('DELETE FROM messages WHERE user_name = ?', (user_name,))
            conn.commit()
    elif chat_id in USER_STATE and USER_STATE[chat_id] == "WAITING_FOR_ADDRESS":
        address = message.text
        if any(city in address for city in ["Г.Саратов", "Г.саратов", "г.Саратов", "г.саратов"]):
            USER_STATE[chat_id] = "WAITING_FOR_PHONE"
            address = message.text
            user_name = message.from_user.username if message.from_user.username else "Без имени"
            cursor.execute('UPDATE messages SET address = ? WHERE user_name = ?', (message.text, user_name ))
            conn.commit()
            bot.send_message(chat_id, "Введите номер телефона, строго по примеру '89005554433'.")
        else:
            bot.send_message(chat_id, "Пожалуйста, укажите корректный адрес доставки: 'г.Саратов' или 'Г.Саратов'.")
    elif chat_id in USER_STATE and USER_STATE[chat_id] == "WAITING_FOR_PHONE":
        phone = message.text
        if phone.isdigit() and (len(phone) == 11 or (len(phone) == 10 and phone.startswith('8'))):
            user_name = message.from_user.username if message.from_user.username else "Без имени"
            cursor.execute('UPDATE messages SET number = ? WHERE user_name = ?', (message.text, user_name ))
            conn.commit()
            chat_id = message.chat.id
            user_name = message.from_user.username if message.from_user.username else "Без имени"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button10 = types.KeyboardButton("На главую")
            button11 = types.KeyboardButton("Отмена")
            markup.add(button10, button11)
            bot.send_message(chat_id, "Отлично! Ожидайте звонка для подтверждения заказа.", reply_markup=markup)
            # Получение данных только для текущего пользователя
            cursor.execute('SELECT user_name, pizza, address, number FROM messages WHERE user_name = ?', (user_name,))
            results = cursor.fetchall()
            if results:
                response = "Ваш заказ:\n"
                for row in results:
                    user_name = row[0]
                    pizza = row[1]
                    address = row[2]
                    phone_number = row[3]
                    response += f'Имя: {user_name}, Пицца: {pizza}, Адрес: {address}, Номер телефона: {phone_number}\n'
                bot.send_message(chat_id, response)
            else:
                bot.send_message(chat_id, "У вас нет заказа.")
            USER_STATE[chat_id] = "DONE"    
        else:
            bot.send_message(chat_id, "Пожалуйста, укажите корректный номер телефона.")
    elif chat_id in USER_STATE and USER_STATE[chat_id] == "DONE" and message.text == "На главую":
        start_message(message)
        del USER_STATE[chat_id]
    elif chat_id in USER_STATE and USER_STATE[chat_id] == "DONE" and message.text == "Отмена":
        start_message(message)
        del USER_STATE[chat_id]
        user_name = message.from_user.username if message.from_user.username else "Без имени"
        cursor.execute('DELETE FROM messages WHERE user_name = ?', (user_name,))
        conn.commit()
    if message.text == "Время доставки":
        current_time = datetime.now()
        hour = current_time.hour
        if 6 <= hour < 10:
            bot.send_message(chat_id, "Примерное время ожидания 40 минут.")
        elif 10 <= hour < 16:
            bot.send_message(chat_id, "Примерное время ожидания 1 час 15 минут.")
        elif 16 <= hour < 20:
            bot.send_message(chat_id, "Примерное время ожидания 1 час 40 минут.")
        elif 20 <= hour:
            bot.send_message(chat_id, "К сожалению, мы закрыты. Мы работаем для вас каждый день с 8:00 до 20:00.")
    elif message.text == "Наш адрес":
        latitude = 51.529681
        longitude = 45.978191
        bot.send_location(chat_id, latitude, longitude)
        bot.send_message(chat_id, "Мы находимся по адресу: г.Саратов, Ул.Политехническая, 77.")


bot.polling()