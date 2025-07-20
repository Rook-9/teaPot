from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ChatMemberUpdated
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters,
    ConversationHandler, ChatMemberHandler
)
import logging
import database as db
from utils import format_entry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# состояния основного меню и поиска
CHOOSING_ACTION, CHOOSING_FORMAT, CHOOSING_CRITERIA, TYPING_QUERY, CHOOSING_DELETE_ENTRY, CONFIRM_DELETE = range(6)


# состояния для ввода новой записи
INPUT_NAME, INPUT_DESC, INPUT_BREW, INPUT_PRICE, INPUT_RATING, CONFIRM = range(6, 12)

# Скрипт создания таблицы и инициализации базы данных
db.init_db()

BTN_VIEW_TABLE = "📄 Просмотр таблицы"
BTN_LAST_ENTRY = "📌 Последняя запись"
BTN_ADD_ENTRY = "➕ Добавить запись"
BTN_SEARCH = "🔍 Поиск по таблице"
BTN_TEXT = "📝 Текст"
BTN_AUDIO = "🎤 Аудио"
BTN_PHOTO = "📷 Фото"
BTN_BACK = "🔙 Назад"
BTN_BACK_TO_MENU = "🔙 Главное меню"
BTN_NEXT_PAGE = "➡️ Далее"
BTN_PREV_PAGE = "⬅️ Назад"
BTN_RATING = "🌟 По рейтингу"
BTN_NAME = "📝 По названию"
BTN_SAVE = "✅ Сохранить"
BTN_EDIT = "✏️ Изменить"
BTN_DELETE = "🗑 Удалить"
PAGE_SIZE = 5 # Количество записей на странице
SHOWING_PAGE = 100  # любое уникальное число, не пересекающееся с другими
BTN_DELETE_ENTRY = "🗑 Удалить запись"


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [BTN_ADD_ENTRY, BTN_SEARCH],
            [BTN_LAST_ENTRY, BTN_VIEW_TABLE], [BTN_DELETE_ENTRY]
        ],
        resize_keyboard=True
    )

# Главный обработчик команд
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_text(
        "🆘 <b>Чем я могу помочь?</b>\n\n"
        "Вот что умеет TeaPot:\n\n"
        "➕ <b>Добавить запись</b> — запиши информацию о чае\n"
        "📄 <b>Просмотр таблицы</b> — листай свои записи\n"
        "📌 <b>Последняя запись</b> — покажу самую свежую\n"
        "🔍 <b>Поиск</b> — ищи по названию или рейтингу\n"
        "🗑 <b>Удалить запись</b> — убери ненужное\n\n"
        "↩️ <b>Назад</b> — отмена текущего действия\n"
        "/cancel — экстренная остановка\n\n"
        "👉 В любой момент жми /start, чтобы вернуться в главное меню.",
        parse_mode='HTML'
    )


#скрипт для видиомости меню
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🍵 Добро пожаловать в TeaPot! Выбери действие:",
        reply_markup=main_menu_keyboard()
    )
    return CHOOSING_ACTION

async def welcome_on_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update.my_chat_member, ChatMemberUpdated):
        if update.my_chat_member.new_chat_member.status == "member":
            user_id = update.effective_user.id
            text = (
                "🍵 <b>Привет! Добро пожаловать в TeaPot — бот-дневник для чаеманов.</b>\n\n"
                "Сохраняй заметки о чаях, оценивай, сортируй и возвращайся к лучшим вкусам позже.\n\n"
                "Нажми кнопку ниже или просто выбери действие ☕"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True),
                parse_mode="HTML"
            )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    if not context.user_data.get("started"):
        context.user_data["started"] = True

        text = (
            "🍵 <b>Привет! Добро пожаловать в TeaPot — бот-дневник для чаеманов.</b>\n\n"
            "Сохраняй заметки о чаях, оценивай, сортируй и возвращайся к лучшим вкусам позже.\n\n"
            "Нажми кнопку ниже или просто выбери действие ☕"
        )

        await update.message.reply_html(
            text,
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(BTN_VIEW_TABLE)]],
                resize_keyboard=True
            )
        )

        # Можно подождать пару секунд или просто завершить функцию
        return CHOOSING_ACTION

    # Показываем меню
    await update.message.reply_text(
        "🍵 Что будем делать?",
        reply_markup=main_menu_keyboard()
    )
    return CHOOSING_ACTION

# Обработка выбора из главного меню
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END
    text = update.message.text
    if text == BTN_ADD_ENTRY:
        keyboard = [[BTN_TEXT, BTN_AUDIO, BTN_PHOTO], [BTN_BACK]]
        await update.message.reply_text(
            "Выбери формат ввода:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CHOOSING_FORMAT

    elif text == BTN_LAST_ENTRY:
        entries = db.get_entries(update.message.from_user.id)
        if entries:
            last = entries[0]
            await update.message.reply_text(
                f"🧾 Последняя запись:\n\n"
                f"Название: {last[2]}\nОписание: {last[3]}\nЗаварка: {last[4]}\n"
                f"Оценка: {last[5]}/10\nЦена: {last[6]}₾\nДата: {last[7]}"
            )
        else:
            await update.message.reply_text("Нет записей.")
        return CHOOSING_ACTION

    elif text == BTN_VIEW_TABLE:
        context.user_data["current_page"] = 0
        return await show_entries_page(update, context)
    
    elif text == BTN_SEARCH:
        await search_entries(update, context)
        return CHOOSING_CRITERIA
    
    elif text == BTN_DELETE_ENTRY:
        return await delete_entry_start(update, context)
    
    else:
        await update.message.reply_text("Не понял команду.")
        return CHOOSING_ACTION

async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    page = context.user_data.get("current_page", 0)

    if text == BTN_NEXT_PAGE:
        context.user_data["current_page"] = page + 1
    elif text == BTN_PREV_PAGE and page > 0:
        context.user_data["current_page"] = page - 1
    elif text == BTN_BACK_TO_MENU:
        context.user_data["current_page"] = 0
        await update.message.reply_text("Возвращаюсь в меню...", reply_markup=main_menu_keyboard())
        return CHOOSING_ACTION

    return await show_entries_page(update, context)

# Вывод всех записей в таблице
async def show_all_entries(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    entries = db.show_all_entries(user_id)

    if not entries:
        await update.message.reply_text("Нет записей в дневнике.")
    else:
        response = ""
        for i, row in enumerate(entries, start=1):
            response += format_entry(row) + "\n\n"

        await update.message.reply_text(response[:4000])  # Telegram limit
    return CHOOSING_ACTION

async def show_entries_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    page = context.user_data.get("current_page", 0)
    offset = page * PAGE_SIZE

    total = db.count_entries(user_id)
    entries = db.get_entries_paginated(user_id, PAGE_SIZE, offset)

    if not entries:
        await update.message.reply_text("Нет записей.")
        return CHOOSING_ACTION

    reply = f"📄 Страница {page + 1} из {(total + PAGE_SIZE - 1) // PAGE_SIZE}\n\n"
    for row in entries:
        reply += format_entry(row) + "\n\n"

    buttons = []
    if page > 0:
        buttons.append(BTN_PREV_PAGE)
    if offset + PAGE_SIZE < total:
        buttons.append(BTN_NEXT_PAGE)

    await update.message.reply_text(
        reply,
        reply_markup=ReplyKeyboardMarkup([buttons + [BTN_BACK_TO_MENU]], resize_keyboard=True)
    )

    return SHOWING_PAGE

async def delete_entry_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("delete_entry_start triggered")
    user_id = update.message.from_user.id
    entries = db.get_entries_paginated(user_id, limit=10, offset=0)  # можно без пагинации

    if not entries:
        await update.message.reply_text("У тебя пока нет записей для удаления.")
        return CHOOSING_ACTION

    context.user_data["delete_candidates"] = entries

    reply = "Выбери номер записи для удаления:\n\n"
    for i, row in enumerate(entries, 1):
        reply += f"{i}. {row[2]} — {row[4]} — {row[5]}/10\n"

    await update.message.reply_text(reply)
    return CHOOSING_DELETE_ENTRY

async def choose_entry_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Введи номер записи.")
        return CHOOSING_DELETE_ENTRY

    index = int(text) - 1
    entries = context.user_data.get("delete_candidates", [])
    if index < 0 or index >= len(entries):
        await update.message.reply_text("Неверный номер.")
        return CHOOSING_DELETE_ENTRY

    entry = entries[index]
    context.user_data["entry_to_delete"] = entry

    await update.message.reply_text(
        f"Удалить запись:\n🍵 {entry[2]}\n💬 {entry[3]}\n🌟 {entry[5]}/10\n\nПодтвердить?",
        reply_markup=ReplyKeyboardMarkup([["✅ Да", "❌ Нет"]], resize_keyboard=True)
    )
    return CONFIRM_DELETE

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()
    if choice == "✅ Да":
        entry = context.user_data.get("entry_to_delete")
        if entry:
            db.delete_entry(entry[0])  # предполагаем, что row[0] — это ID записи
            await update.message.reply_text("Запись удалена ✅")
    else:
        await update.message.reply_text("Удаление отменено.")

    return await show_menu(update, context)  # возвращаемся в главное меню

# Поиск по базе данных
async def search_entries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 Выбери критерий для поиска:",
        reply_markup=ReplyKeyboardMarkup(
            [[BTN_RATING, BTN_NAME], [BTN_BACK]],
            resize_keyboard=True
        )
    )
    return CHOOSING_CRITERIA

# пользователь выбрал критерий
async def choose_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == BTN_NAME:
        context.user_data["search_by"] = "name"
        await update.message.reply_text("📝 Введи название чая:")
        return TYPING_QUERY

    elif text == BTN_RATING:
        context.user_data["search_by"] = "rating"
        await update.message.reply_text("🌟 Введи минимальный рейтинг (1–10):")
        return TYPING_QUERY

    elif text == BTN_BACK:
        await show_menu(update, context)
        return CHOOSING_ACTION

    else:
        await update.message.reply_text("❗ Пожалуйста, выбери из предложенного списка.")
        return CHOOSING_CRITERIA
    

# пользователь ввёл значение для поиска
async def handle_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    value = update.message.text
    criterion = context.user_data.get("search_by")

    results = []

    if criterion == "name":
        results = db.search_by_name(user_id, value)
    elif criterion == "rating":
        try:
            rating = int(value)
            results = db.search_by_rating(user_id, rating)
        except ValueError:
            await update.message.reply_text("❗ Введи целое число от 1 до 10.")
            return TYPING_QUERY

    if not results:
        await update.message.reply_text("❌ Ничего не найдено.")
    else:
        reply = "\n\n".join([
            f"🍵 {row[2]}\n💬 {row[3]}\n🔧 {row[4]}\n🌟 {row[5]}/10\n💰 {row[6]}₾"
            for row in results
        ])
        await update.message.reply_text(reply)

    await update.message.reply_text(
    "🔍 Что дальше?",
    reply_markup=main_menu_keyboard()
)
    return CHOOSING_ACTION


# Обработка выбора формата
async def choose_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END
    if update.message.text == BTN_TEXT:
        await update.message.reply_text("Как называется чай?", reply_markup=ReplyKeyboardRemove())
        return INPUT_NAME
    elif update.message.text == BTN_BACK:
        await show_menu(update, context)
        return CHOOSING_ACTION
    else:
        await update.message.reply_text("🔧 Этот формат пока в разработке. Выбери 'Текст'.")
        return CHOOSING_FORMAT

# Сбор данных по шагам
async def input_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text
    if len(name) > 100:
        await update.message.reply_text("Название слишком длинное. Максимум 100 символов.")
        return INPUT_NAME
    
    context.user_data["tea_name"] = update.message.text
    await update.message.reply_text("Добавь описание:")
    return INPUT_DESC

async def input_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Особенности заварки?")
    return INPUT_BREW

async def input_brew(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["how_to_brew"] = update.message.text
    await update.message.reply_text("Оцени от 1 до 10:")
    return INPUT_RATING

async def input_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        rating = float(update.message.text)
        if not (1 <= rating <= 10):
            raise ValueError
        context.user_data["rating"] = round(rating, 1)  # округляем до 1 знака после запятой
    except ValueError:
        await update.message.reply_text("Введи число от 1 до 10.")
        return INPUT_RATING

    await update.message.reply_text("Укажи цену в лари за 100г (Например 12.50):")
    return INPUT_PRICE

async def input_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text)
        if price < 0:
            await update.message.reply_text("Цена не может быть отрицательной. Попробуйте еще раз.")
            return INPUT_PRICE
        context.user_data["price"] = round(price, 2)  # Округляем до копеек
    except ValueError:
        await update.message.reply_text("Введи цену числом (например: 12.50).")
        return INPUT_PRICE
    
    # Подтверждение
    data = context.user_data
    keyboard = [[BTN_SAVE, BTN_EDIT], [BTN_DELETE]]
    await update.message.reply_text(
        f"Проверь данные:\n\n"
        f"Название: {data['tea_name']}\n"
        f"Описание: {data['description']}\n"
        f"Заварка: {data['how_to_brew']}\n"
        f"Оценка: {data['rating']}/10\n"
        f"Цена: {data['price']}₾",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        return CONFIRM
    
    text = update.message.text

    if text == BTN_SAVE:
        user_id = update.message.from_user.id
        data = context.user_data

        db.save_entry(
            user_id,
            tea_name=data["tea_name"],
            description=data["description"],
            how_to_brew=data["how_to_brew"],
            rating=data["rating"],
            price=data["price"]
        )

        # Очищаем временные данные
        context.user_data.clear()

        # Отправляем сообщение + заново показываем главное меню
        await update.message.reply_text(
            "✅ Запись сохранена!",
            reply_markup=main_menu_keyboard()
        )
        return CHOOSING_ACTION

    elif text == BTN_EDIT:
        # Просто возвращаемся к первому шагу, без трогания main_menu
        await update.message.reply_text("Хорошо, начнём сначала. Как называется чай?")
        return INPUT_NAME

    elif text == BTN_DELETE:
        context.user_data.clear()
        await update.message.reply_text(
            "🚫 Запись удалена.",
            reply_markup=main_menu_keyboard()
        )
        return CHOOSING_ACTION

    else:
        await update.message.reply_text("Пожалуйста, нажми кнопку «Сохранить», «Изменить» или «Удалить».")
        return CONFIRM

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Действие отменено.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

def main():
    from config import TELEGRAM_TOKEN
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.Regex("^Поиск по таблице$"), search_entries),],
        states={
            SHOWING_PAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pagination)],
            CHOOSING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            CHOOSING_FORMAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_format)],
            CHOOSING_CRITERIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_criteria)],
            CHOOSING_DELETE_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_entry_to_delete)],
            CONFIRM_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete)],
            INPUT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_name)],
            INPUT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_desc)],
            INPUT_BREW: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_brew)],
            INPUT_RATING: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_rating)],
            INPUT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_price)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            TYPING_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(ChatMemberHandler(welcome_on_open, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv)
    logger.info("✅ Bot started")
    application.run_polling()

if __name__ == "__main__":
    main()
