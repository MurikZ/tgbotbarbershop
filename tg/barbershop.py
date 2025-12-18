import asyncio
import logging
import os
import random
from aiohttp import web
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, InlineKeyboardMarkup, \
    InlineKeyboardButton, BotCommand, PreCheckoutQuery
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode

API_TOKEN = os.getenv("BOT_TOKEN") # Замени!
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище данных
user_data = {}  # {user_id: {"step": "main", "service": "...", ...}}
user_scores = {}  # {user_id: 100}
user_bets = {}  # {user_id: {"game": "...", ...}}

# ========== КЛАВИАТУРЫ ==========
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✂️ Записаться на стрижку")],
        [KeyboardButton(text="🎮 Игры"), KeyboardButton(text="🏆 Мой счет")]
    ],
    resize_keyboard=True
)

services_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✂️ Мужская стрижка"), KeyboardButton(text="🧔 Стрижка + борода")],
        [KeyboardButton(text="🧔 Коррекция бороды"), KeyboardButton(text="👑 Стрижка под ноль")],
        [KeyboardButton(text="👨‍🦳 Окантовка"), KeyboardButton(text="💎 Премиум (все включено)")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

time_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="10:00"), KeyboardButton(text="11:00"), KeyboardButton(text="12:00")],
        [KeyboardButton(text="13:00"), KeyboardButton(text="14:00"), KeyboardButton(text="15:00")],
        [KeyboardButton(text="16:00"), KeyboardButton(text="17:00")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

games_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚽ Угадай счет"), KeyboardButton(text="🎲 Брось кубик")],
        [KeyboardButton(text="🔙 В главное меню")]
    ],
    resize_keyboard=True
)

confirm_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 Оплатить 50%"), KeyboardButton(text="❌ Отменить запись")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# Цены
PRICES = {
    "✂️ Мужская стрижка": 120000,
    "🧔 Стрижка + борода": 180000,
    "🧔 Коррекция бороды": 80000,
    "👑 Стрижка под ноль": 100000,
    "👨‍🦳 Окантовка": 50000,
    "💎 Премиум (все включено)": 250000
}

TEAMS = ["ЦСКА", "Спартак", "Зенит", "Динамо", "Локомотив", "Краснодар"]


# ========== ГЛАВНОЕ МЕНЮ ==========
@dp.message(CommandStart())
async def start_command(message: Message):
    """Главная команда /start"""
    user_id = message.from_user.id
    user_scores[user_id] = user_scores.get(user_id, 0)

    # Сбрасываем состояние пользователя
    user_data[user_id] = {"step": "main"}

    await message.answer(
        "⚔️ *Добро пожаловать в BarberKing!* ⚔️\n\n"
        "Только для настоящих мужчин. Записывайся на стрижку, играй в ожидании!\n\n"
        f"🏆 *Твой счет:* {user_scores[user_id]} очков\n\n"
        "*Выбери действие:*",
        reply_markup=main_kb,
        parse_mode=ParseMode.MARKDOWN
    )


# ========== ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ ==========
@dp.message(F.text == "✂️ Записаться на стрижку")
async def start_booking(message: Message):
    """Начать процесс записи"""
    user_id = message.from_user.id
    user_data[user_id] = {"step": "choosing_service"}

    await message.answer(
        "*Выбери услугу:*\n\n"
        "• ✂️ Мужская стрижка - 1200₽\n"
        "• 🧔 Стрижка + борода - 1800₽\n"
        "• 🧔 Коррекция бороды - 800₽\n"
        "• 👑 Стрижка под ноль - 1000₽\n"
        "• 👨‍🦳 Окантовка - 500₽\n"
        "• 💎 Премиум (все включено) - 2500₽",
        reply_markup=services_kb,
        parse_mode=ParseMode.MARKDOWN
    )


@dp.message(F.text == "🎮 Игры")
async def games_menu(message: Message):
    """Меню игр"""
    user_id = message.from_user.id
    user_data[user_id] = {"step": "games_menu"}

    await message.answer(
        f"🎮 *Игры в ожидании!*\n\n"
        f"🏆 Твой счет: {user_scores.get(user_id, 0)} очков\n\n"
        f"Зарабатывай очки, попади в топ-3 и получи скидку 50%!",
        reply_markup=games_kb,
        parse_mode=ParseMode.MARKDOWN
    )


@dp.message(F.text == "🏆 Мой счет")
async def show_score(message: Message):
    """Показать счет"""
    user_id = message.from_user.id
    score = user_scores.get(user_id, 0)

    # Определяем ранг
    if score >= 1000:
        rank = "👑 КОРОЛЬ БАРБЕРШОПА"
    elif score >= 500:
        rank = "⚔️ МАСТЕР БРИТВЫ"
    elif score >= 200:
        rank = "✂️ АСС БАРБЕРА"
    elif score >= 100:
        rank = "🧔 ГУРУ БОРОДЫ"
    elif score >= 50:
        rank = "🪒 НОВИЧОК"
    else:
        rank = "🧼 НАЧИНАЮЩИЙ"

    await message.answer(
        f"🏆 *ТВОЙ СТАТУС*\n\n"
        f"*Ранг:* {rank}\n"
        f"*Очки:* {score}\n\n"
        f"*Топ-3 месяца получают скидку 50% на Премиум!*",
        reply_markup=main_kb,
        parse_mode=ParseMode.MARKDOWN
    )


# ========== ПРОЦЕСС ЗАПИСИ (ШАГ 1: УСЛУГА) ==========
@dp.message(F.text.in_(list(PRICES.keys())))
async def choose_service(message: Message):
    """Выбор услуги"""
    user_id = message.from_user.id

    # Проверяем, что пользователь на нужном шаге
    if user_id not in user_data or user_data[user_id].get("step") != "choosing_service":
        await message.answer("Пожалуйста, начни запись сначала: /start", reply_markup=main_kb)
        return

    user_data[user_id]["service"] = message.text
    user_data[user_id]["step"] = "choosing_time"

    await message.answer(
        f"✅ *Выбрано:* {message.text}\n"
        f"💰 *Цена:* {PRICES[message.text] // 100}₽\n\n"
        "Теперь выбери удобное время:",
        reply_markup=time_kb,
        parse_mode=ParseMode.MARKDOWN
    )


# ========== ПРОЦЕСС ЗАПИСИ (ШАГ 2: ВРЕМЯ) ==========
@dp.message(F.text.in_(["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]))
async def choose_time(message: Message):
    """Выбор времени"""
    user_id = message.from_user.id

    if user_id not in user_data or user_data[user_id].get("step") != "choosing_time":
        await message.answer("Пожалуйста, выбери сначала услугу!", reply_markup=main_kb)
        return

    user_data[user_id]["time"] = message.text
    user_data[user_id]["step"] = "entering_name"

    await message.answer(
        "✍️ *Введи свое имя:*\n\n"
        "Например: *Алексей* или *Дмитрий*\n"
        "Только имя, без фамилии.",
        parse_mode=ParseMode.MARKDOWN
    )


# ========== ПРОЦЕСС ЗАПИСИ (ШАГ 3: ИМЯ) ==========
@dp.message(F.text.regexp(r'^[А-Яа-яA-Za-z]{2,20}$'))
async def enter_name(message: Message):
    """Ввод имени (только буквы, 2-20 символов)"""
    user_id = message.from_user.id

    if user_id not in user_data or user_data[user_id].get("step") != "entering_name":
        await message.answer("Пожалуйста, начни запись сначала!", reply_markup=main_kb)
        return

    user_data[user_id]["name"] = message.text
    user_data[user_id]["step"] = "confirmation"

    data = user_data[user_id]
    service_price = PRICES[data["service"]] // 100
    prepayment = service_price // 2  # 50%

    await message.answer(
        f"📋 *ПОДТВЕРЖДЕНИЕ ЗАПИСИ*\n\n"
        f"👤 *Имя:* {data['name']}\n"
        f"✂️ *Услуга:* {data['service']}\n"
        f"💰 *Полная цена:* {service_price}₽\n"
        f"💳 *Предоплата (50%):* {prepayment}₽\n"
        f"⏰ *Время:* {data['time']}\n\n"
        f"*Для подтверждения требуется внести предоплату.*\n"
        f"Отмена возможна за 3 часа до визита.\n\n"
        f"*Что делаем дальше?*",
        reply_markup=confirm_kb,
        parse_mode=ParseMode.MARKDOWN
    )


# ========== КНОПКИ "НАЗАД" ==========
@dp.message(F.text == "🔙 Назад")
async def back_button(message: Message):
    """Обработчик кнопки Назад"""
    user_id = message.from_user.id

    if user_id not in user_data:
        await start_command(message)
        return

    current_step = user_data[user_id].get("step", "main")

    if current_step == "choosing_service":
        # Возврат в главное меню
        user_data[user_id]["step"] = "main"
        await message.answer("Возвращаюсь в главное меню:", reply_markup=main_kb)

    elif current_step == "choosing_time":
        # Возврат к выбору услуги
        user_data[user_id]["step"] = "choosing_service"
        await message.answer("Выбери услугу:", reply_markup=services_kb)

    elif current_step == "entering_name":
        # Возврат к выбору времени
        user_data[user_id]["step"] = "choosing_time"
        await message.answer("Выбери время:", reply_markup=time_kb)

    elif current_step == "confirmation":
        # Возврат к вводу имени
        user_data[user_id]["step"] = "entering_name"
        await message.answer("Введи свое имя:")

    elif current_step == "games_menu":
        # Возврат в главное меню из игр
        user_data[user_id]["step"] = "main"
        await message.answer("Главное меню:", reply_markup=main_kb)

    else:
        await start_command(message)


@dp.message(F.text == "🔙 В главное меню")
async def back_to_main_from_games(message: Message):
    """Возврат из игр в главное меню"""
    user_id = message.from_user.id
    user_data[user_id] = {"step": "main"}
    await start_command(message)


# ========== ИГРЫ ==========
@dp.message(F.text == "⚽ Угадай счет")
async def guess_score_game(message: Message):
    """Игра 'Угадай счет'"""
    user_id = message.from_user.id
    user_data[user_id] = {"step": "playing_game"}

    # Выбираем команды
    team1, team2 = random.sample(TEAMS, 2)
    real_score = f"{random.randint(0, 5)}:{random.randint(0, 5)}"

    user_bets[user_id] = {
        "teams": f"{team1} - {team2}",
        "correct_score": real_score,
        "bet": None
    }

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1:0", callback_data="bet_1:0"),
             InlineKeyboardButton(text="2:0", callback_data="bet_2:0")],
            [InlineKeyboardButton(text="2:1", callback_data="bet_2:1"),
             InlineKeyboardButton(text="3:1", callback_data="bet_3:1")],
            [InlineKeyboardButton(text="1:1", callback_data="bet_1:1"),
             InlineKeyboardButton(text="3:2", callback_data="bet_3:2")],
        ]
    )

    await message.answer(
        f"⚽ *Угадай счет матча!*\n\n"
        f"*{team1}* 🆚 *{team2}*\n\n"
        f"Выбери свой прогноз:",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )


@dp.callback_query(F.data.startswith("bet_"))
async def process_bet(callback_query):
    """Обработка ставки"""
    user_id = callback_query.from_user.id
    user_bet = callback_query.data.split("_")[1]

    if user_id not in user_bets or user_bets[user_id]["bet"] is not None:
        await callback_query.answer("Уже сделал ставку!")
        return

    user_bets[user_id]["bet"] = user_bet
    correct_score = user_bets[user_id]["correct_score"]

    await callback_query.message.edit_text(
        f"⚽ *Матч начался!*\n\n"
        f"{user_bets[user_id]['teams']}\n"
        f"Твой прогноз: *{user_bet}*\n\n"
        f"⏳ Идет игра...",
        parse_mode=ParseMode.MARKDOWN
    )

    await asyncio.sleep(2)

    if user_bet == correct_score:
        user_scores[user_id] = user_scores.get(user_id, 0) + 50
        result = f"✅ *ТОЧНО В ЦЕЛЬ!*\nПобедил {correct_score}\n\n🎉 *+50 очков!*"
    else:
        user_scores[user_id] = max(0, user_scores.get(user_id, 0) - 10)
        result = f"❌ *Не угадал...*\nРеальный счет: {correct_score}\n\n📉 *-10 очков*"

    await callback_query.message.edit_text(
        f"⚽ *Матч окончен!*\n\n"
        f"{user_bets[user_id]['teams']}\n"
        f"🏁 *Результат:* {correct_score}\n\n"
        f"{result}\n"
        f"🏆 *Твой счет:* {user_scores.get(user_id, 0)} очков",
        parse_mode=ParseMode.MARKDOWN
    )

    user_bets.pop(user_id, None)
    user_data[user_id] = {"step": "games_menu"}
    await callback_query.answer()


@dp.message(F.text == "🎲 Брось кубик")
async def dice_game(message: Message):
    """Игра 'Брось кубик'"""
    user_id = message.from_user.id
    user_data[user_id] = {"step": "playing_game"}

    # Отправляем кубик
    dice_msg = await message.answer_dice(emoji="🎲")
    await asyncio.sleep(4)

    dice_value = dice_msg.dice.value

    if dice_value == 6:
        reward = 30
        result = "🎉 *КРИТИЧЕСКИЙ УСПЕХ!* +30 очков"
    elif dice_value >= 4:
        reward = 10
        result = f"✅ *Неплохо!* Выпало {dice_value}. +10 очков"
    else:
        reward = 5
        result = f"⚡ *Могло быть лучше.* Выпало {dice_value}. +5 очков"

    user_scores[user_id] = user_scores.get(user_id, 0) + reward

    await message.answer(
        f"🎲 *Бросок кубика!*\n\n"
        f"Выпало: *{dice_value}*\n\n"
        f"{result}\n"
        f"🏆 *Твой счет:* {user_scores[user_id]} очков",
        reply_markup=games_kb,
        parse_mode=ParseMode.MARKDOWN
    )

    user_data[user_id] = {"step": "games_menu"}


# ========== ОПЛАТА ==========
@dp.message(F.text == "💳 Оплатить 50%")
async def process_payment(message: Message):
    """Обработчик оплаты"""
    user_id = message.from_user.id

    if user_id not in user_data or user_data[user_id].get("step") != "confirmation":
        await message.answer("❌ Нет активной записи для оплаты!", reply_markup=main_kb)
        return

    data = user_data[user_id]
    price = PRICES[data["service"]] // 2  # 50% предоплата

    try:
        await bot.send_invoice(
            chat_id=user_id,
            title=f"BarberKing: {data['service']}",
            description=f"Запись на {data['time']}. Предоплата 50%",
            payload=f"booking_{user_id}_{int(datetime.now().timestamp())}",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Предоплата", amount=price)],
            start_parameter="barber_booking"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=confirm_kb)


@dp.message(F.text == "❌ Отменить запись")
async def cancel_booking(message: Message):
    """Отмена записи"""
    user_id = message.from_user.id
    if user_id in user_data:
        user_data.pop(user_id, None)

    await message.answer(
        "❌ Запись отменена.\n\n"
        "Можешь создать новую в любое время!",
        reply_markup=main_kb
    )


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение оплаты"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    """Успешная оплата"""
    user_id = message.from_user.id

    if user_id in user_data and user_data[user_id].get("step") == "confirmation":
        data = user_data[user_id]

        await message.answer(
            f"🎉 *ОПЛАТА ПРИНЯТА!*\n\n"
            f"✅ *Ты записан в BarberKing!*\n\n"
            f"📋 *Детали:*\n"
            f"• 👤 Имя: {data['name']}\n"
            f"• ✂️ Услуга: {data['service']}\n"
            f"• ⏰ Время: {data['time']}\n"
            f"• 💰 Предоплата: {PRICES[data['service']] // 200}₽\n\n"
            f"📍 *Адрес:* ул. Мужская, 13\n"
            f"📞 *Телефон:* +7 (999) 123-45-67\n\n"
            f"⚠️ *Приходи за 5 минут до записи!*\n\n"
            f"🎮 *Пока ждешь - поиграй в игры!*",
            reply_markup=main_kb,
            parse_mode=ParseMode.MARKDOWN
        )

        # Дарим бонус за оплату
        user_scores[user_id] = user_scores.get(user_id, 0) + 25

        user_data.pop(user_id, None)  # Очищаем данные

    else:
        await message.answer(
            "✅ Оплата принята!\n\n"
            "Свяжись с администратором для уточнения деталей записи.",
            reply_markup=main_kb
        )


# ========== ОБРАБОТКА ЛЮБЫХ ДРУГИХ СООБЩЕНИЙ ==========
@dp.message()
async def handle_other_messages(message: Message):
    """Обработка всех остальных сообщений"""
    user_id = message.from_user.id

    # Проверяем, что не обработано другими хэндлерами
    if user_id not in user_data:
        await message.answer(
            "👋 Привет! Я бот BarberKing.\n\n"
            "Нажми /start чтобы начать!",
            reply_markup=main_kb
        )
        return

    current_step = user_data[user_id].get("step", "main")

    if current_step == "entering_name":
        # Если пользователь вводит имя, но оно не прошло валидацию
        await message.answer(
            "❌ Имя должно содержать только буквы (2-20 символов).\n"
            "Попробуй еще раз, например: *Алексей*",
            parse_mode=ParseMode.MARKDOWN
        )

    else:
        # Во всех остальных случаях показываем главное меню
        await start_command(message)


# ========== ЗАПУСК БОТА ==========
async def set_bot_commands():
    """Настройка команд бота"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="❓ Помощь"),
    ]
    await bot.set_my_commands(commands)


# ========== ЗАПУСК БОТА И HTTP СЕРВЕРА ==========
async def on_startup(app):
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))

async def handle(request):
    return web.Response(text="OK")

def run():
    app = web.Application()
    app.router.add_get("/", handle)
    app.on_startup.append(on_startup)
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

if __name__ == "__main__":
    run()