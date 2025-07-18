import unittest
from unittest.mock import AsyncMock, MagicMock
from bot import input_name, input_rating, input_price, INPUT_DESC, INPUT_RATING, INPUT_PRICE, CONFIRM, INPUT_NAME
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

class TestTeaBot(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Создаем моки для update и context
        self.update = MagicMock(spec=Update)
        self.context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Настраиваем мок для сообщения
        self.message = MagicMock(spec=Message)
        self.update.message = self.message
        
        # Настраиваем user_data
        self.context.user_data = {}
        
        # Мокируем reply_text
        self.message.reply_text = AsyncMock()

    async def test_input_name_valid(self):
    # Тест с валидным именем
        self.message.text = "Зеленый чай"
        result = await input_name(self.update, self.context)
        self.assertEqual(result, INPUT_DESC)
        self.assertEqual(self.context.user_data["tea_name"], "Зеленый чай")  # Исправлено с input_name на tea_name
        self.message.reply_text.assert_called_with("Добавь описание:")

    async def test_input_name_too_long(self):
        # Тест с слишком длинным именем
        long_name = "Очень длинное название чая, которое явно превышает установленный лимит в сто символов и поэтому должно быть отвергнуто валидацией"
        self.message.text = long_name
        result = await input_name(self.update, self.context)
        self.assertEqual(result, INPUT_NAME)  #  (остаемся в том же состоянии)
        self.message.reply_text.assert_called_with("Название слишком длинное. Максимум 100 символов.")

    async def test_input_rating_valid_integer(self):
        # Тест с валидной целой оценкой
        self.message.text = "8"
        result = await input_rating(self.update, self.context)
        self.assertEqual(result, INPUT_PRICE)  
        self.assertEqual(self.context.user_data["rating"], 8.0)
        self.message.reply_text.assert_called_with("Укажи цену в лари за 100г (Например 12.50):")

    async def test_input_rating_valid_float(self):
        # Тест с валидной дробной оценкой
        self.message.text = "8.5"
        result = await input_rating(self.update, self.context)
        self.assertEqual(result, INPUT_PRICE) 
        self.assertEqual(self.context.user_data["rating"], 8.5)
        self.message.reply_text.assert_called_with("Укажи цену в лари за 100г (Например 12.50):")

    async def test_input_rating_invalid(self):
        # Тест с невалидной оценкой
        test_cases = [
            ("11", "Введи число от 1 до 10."),
            ("0", "Введи число от 1 до 10."),
            ("abc", "Введи число от 1 до 10."),
        ]
        
        for rating, expected_message in test_cases:
            with self.subTest(rating=rating):
                self.message.text = rating
                result = await input_rating(self.update, self.context)
                self.assertEqual(result, INPUT_RATING)
                self.message.reply_text.assert_called_with(expected_message)
                self.message.reply_text.reset_mock()

    async def test_input_price_valid(self):

    # Тест с валидной ценой
    # Необходимо заполнить user_data всеми требуемыми полями
        self.context.user_data = {
            "tea_name": "Зеленый чай",
            "description": "Ароматный чай",
            "how_to_brew": "80°C, 3 минуты",
            "rating": 8.5
    }
    
        test_cases = [
            ("12", 12.0),
            ("12.5", 12.5),
            ("12.50", 12.5),
            ("0", 0.0),
    ]
    
        for price, expected in test_cases:
            with self.subTest(price=price):
                self.message.text = price
                result = await input_price(self.update, self.context)
                self.assertEqual(result, CONFIRM)
                self.assertEqual(self.context.user_data["price"], expected)
                # Проверяем, что другие данные не изменились
                self.assertEqual(self.context.user_data["tea_name"], "Зеленый чай")
                self.assertEqual(self.context.user_data["description"], "Ароматный чай")
                self.assertEqual(self.context.user_data["how_to_brew"], "80°C, 3 минуты")
                self.assertEqual(self.context.user_data["rating"], 8.5)

    async def test_input_price_invalid(self):
        # Тест с невалидной ценой
        test_cases = [
            ("-5", "Цена не может быть отрицательной. Попробуйте еще раз."),
            ("abc", "Введи цену числом (например: 12.50)."),
        ]
        
        for price, expected_message in test_cases:
            with self.subTest(price=price):
                self.message.text = price
                result = await input_price(self.update, self.context)
                self.assertEqual(result, INPUT_PRICE)  # 
                self.message.reply_text.assert_called_with(expected_message)
                self.message.reply_text.reset_mock()

if __name__ == "__main__":
    unittest.main()