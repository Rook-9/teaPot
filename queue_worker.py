import pika
import speech_recognition as sr
from PIL import Image
import pytesseract
import os
from pydub import AudioSegment
import database as db
import logging

# --- Логирование ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- Подключение к RabbitMQ ---
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='tea_diary_queue')

# --- Обработка голосовых ---
def process_voice(user_id, file_path):
    logger.info(f"🔊 Starting voice processing for user {user_id}")

    wav_path = file_path.replace(".ogg", ".wav")
    try:
        audio = AudioSegment.from_file(file_path, format="ogg")
        audio.export(wav_path, format="wav")
        logger.info(f"✅ Converted {file_path} → {wav_path}")
    except Exception as e:
        logger.error(f"❌ Failed to convert audio: {e}")
        return

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="en-US")
            logger.info(f"📝 Transcription: {text}")
            db.save_entry(user_id, description=text)
    except Exception as e:
        logger.error(f"❌ Speech recognition failed: {e}")
    finally:
        os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

# --- Обработка изображений ---
def process_photo(user_id, file_path):
    logger.info(f"🖼️ Starting photo processing for user {user_id}")
    try:
        text = pytesseract.image_to_string(Image.open(file_path))
        logger.info(f"📝 OCR Result: {text[:50]}...")
        db.save_entry(user_id, description=text)
    except Exception as e:
        logger.error(f"❌ OCR error: {e}")
    finally:
        os.remove(file_path)

# --- Callback для очереди ---
def callback(ch, method, properties, body):
    try:
        data = body.decode().split(":")
        media_type, user_id, file_path = data[0], int(data[1]), data[2]
        logger.info(f"📩 Received task: {media_type} for user {user_id}")

        if media_type == "voice":
            process_voice(user_id, file_path)
        elif media_type == "photo":
            process_photo(user_id, file_path)
        else:
            logger.warning(f"⚠️ Unknown media type: {media_type}")
    except Exception as e:
        logger.error(f"❌ Failed to handle message: {e}")

# --- Запуск слушателя ---
channel.basic_consume(
    queue='tea_diary_queue',
    on_message_callback=callback,
    auto_ack=True
)

logger.info("🔧 Worker is running. Waiting for tasks...")
channel.start_consuming()
