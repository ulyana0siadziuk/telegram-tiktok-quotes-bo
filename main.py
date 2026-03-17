import requests
import urllib.parse
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import yt_dlp
import os
from deep_translator import GoogleTranslator

TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = '@Quetos_bot'

ZEN_QUOTES_API_URL = "https://zenquotes.io/api/random"


def fetch_random_quote_from_api():
    try:
        response = requests.get(ZEN_QUOTES_API_URL)
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            quote_text = data[0].get("q", "Текст не найден")
            quote_author = data[0].get("a", "Автор неизвестен")
            return f'"{quote_text}"\n\n— {quote_author}', quote_text
        else:
            print(f"Неожиданный формат ответа от ZenQuotes: {data}")
            return "Ошибка: Неожиданный формат ответа от API цитат.", None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API ZenQuotes: {e}")
        return "Не удалось получить цитату. Попробуйте позже.", None
    except Exception as e:
        print(f"Непредвиденная ошибка при получении цитаты: {e}")
        return "Произошла внутренняя ошибка.", None

def generate_tiktok_search_link(translated_quote):
    if not translated_quote:
        return None
    encoded_query = urllib.parse.quote(translated_quote)
    return f"https://www.tiktok.com/search?q={encoded_query}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Напиши /quote, чтобы получить случайную цитату и ссылку на поиск видео в TikTok.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Используй /quote для получения случайной цитаты и ссылки на поиск видео в TikTok по этой цитате.')

# Команда /quote (получает цитату + ссылку на поиск TikTok)
async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quote_message, search_query = fetch_random_quote_from_api()

    if search_query:
        try:
            translated_text = GoogleTranslator(source='auto', target='ru').translate(search_query)
            original_quote = f" *{search_query}*"
            translated_quote = f" *{translated_text}*"


            tiktok_search_link = generate_tiktok_search_link(translated_text)

            if tiktok_search_link:
                full_message = f"{translated_quote}\n\n [Найти видео по этой цитате в TikTok]({tiktok_search_link})"
                await update.message.reply_text(full_message, parse_mode='Markdown')
            else:
                await update.message.reply_text(translated_quote)
        except Exception as e:
            print(f"Ошибка перевода: {e}")
            await update.message.reply_text(f"{quote_message}\n\n Перевод не выполнен.")
    else:
        await update.message.reply_text(quote_message)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


async def tiktok_download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажи ссылку на TikTok после команды")
        return

    url = context.args[0]
    await update.message.reply_text("Скачиваю видео...")

    try:
        ydl_opts = {
            'outtmpl': 'tiktok_video.%(ext)s',
            'format': 'mp4/best',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file)

        os.remove(filename)

    except Exception as e:
        print(f"Ошибка при скачивании TikTok-видео: {e}")
        await update.message.reply_text("Видео задерживается.")


if __name__ == '__main__':
    print('Бот запускается...')
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('quote', quote_command))
    app.add_handler(CommandHandler('tiktok', tiktok_download_command))

    app.add_error_handler(error)

    print('Бот ожидает...')
    app.run_polling(poll_interval=1)