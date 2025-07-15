import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
RABBITMQ_URL = 'amqp://localhost:5672'  # Update for production
QUEUE_NAME = 'tea_diary_queue'

if TELEGRAM_TOKEN is None:
    raise ValueError("❌ TELEGRAM_TOKEN is not set in environment variables.")