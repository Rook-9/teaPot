def format_entry(entry) -> str:
    return (
        f"🍵 <b>{entry.tea_name}</b>\n"
        f"💬 <i>{entry.description}</i>\n"
        f"🔧 Заварка: {entry.how_to_brew}\n"
        f"🌟 Оценка: {entry.rating}/10\n"
        f"💰 Цена: {entry.price}₾\n"
        f"📅 Дата: {entry.created_at.strftime('%Y-%m-%d %H:%M')}"
    )
