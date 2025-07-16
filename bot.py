from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters,
    ConversationHandler
)
import logging
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# состояния основного меню и поиска
CHOOSING_ACTION, CHOOSING_FORMAT, CHOOSING_CRITERIA, TYPING_QUERY = range(4)


# состояния для ввода новой записи
INPUT_NAME, INPUT_DESC, INPUT_BREW, INPUT_PRICE, INPUT_RATING, CONFIRM = range(4, 10)

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
BTN_RATING = "🌟 По рейтингу"
BTN_NAME = "📝 По названию"
BTN_SAVE = "✅ Сохранить"
BTN_EDIT = "✏️ Изменить"
BTN_DELETE = "🗑 Удалить"


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [BTN_ADD_ENTRY, BTN_SEARCH],
            [BTN_LAST_ENTRY, BTN_VIEW_TABLE]
        ],
        resize_keyboard=True
    )


# Главный обработчик команд
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Привет! Я бот для ведения чайного дневника. "
        "Используй /start для начала."
    )


#скрипт для видиомости меню
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    
    await update.message.reply_text(
        "🍵 Добро пожаловать в Tea Diary! Выбери действие:",
        reply_markup=main_menu_keyboard()
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    await update.message.reply_text(
        "🍵 Добро пожаловать в Tea Diary!",
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
        return await show_all_entries(update, context)

    
    elif text == BTN_SEARCH:
        await search_entries(update, context)
        return CHOOSING_CRITERIA

    else:
        await update.message.reply_text("Не понял команду.")
        return CHOOSING_ACTION

# Вывод всех записей в таблице
async def show_all_entries(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    entries = db.show_all_entries(user_id)

    if not entries:
        await update.message.reply_text("Нет записей в дневнике.")
    else:
        response = ""
        for i, row in enumerate(entries, start=1):
            response += (
                f"{i}. 🍵 {row[2]}\n"
                f"💬 {row[3]}\n"
                f"🔧 {row[4]}\n"
                f"🌟 {row[5]}/10\n"
                f"💰 {row[6]}₾\n"
                f"📅 {row[7]}\n\n"
            )
        await update.message.reply_text(response[:4000])  # Telegram limit
    return CHOOSING_ACTION

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
        rating = int(update.message.text)
        if not (1 <= rating <= 10):
            raise ValueError
        context.user_data["rating"] = rating
    except ValueError:
        await update.message.reply_text("Введи число от 1 до 10.")
        return INPUT_RATING

    await update.message.reply_text("Укажи цену:")
    return INPUT_PRICE

async def input_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["price"] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введи цену числом.")
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
            CHOOSING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            CHOOSING_FORMAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_format)],
            CHOOSING_CRITERIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_criteria)],
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

    application.add_handler(conv)
    logger.info("✅ Bot started")
    application.run_polling()

if __name__ == "__main__":
    main()
