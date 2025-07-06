import os
import asyncio
import nest_asyncio
nest_asyncio.apply()
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Файлы данных
USERS_FILE = "users.txt"
REPEATS_FILE = "repeats.txt"

# ----------------- Работа с файлами -----------------

def load_users() -> set:
    if not os.path.exists(USERS_FILE):
        return set()
    with open(USERS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_user(chat_id: int):
    users = load_users()
    if str(chat_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{chat_id}\n")

def remove_user(chat_id: int):
    users = load_users()
    users.discard(str(chat_id))
    with open(USERS_FILE, "w") as f:
        for uid in users:
            f.write(f"{uid}\n")

def load_repeats() -> dict:
    if not os.path.exists(REPEATS_FILE):
        return {}
    with open(REPEATS_FILE, "r") as f:
        return {
            line.strip().split(":", 1)[0]: int(line.strip().split(":", 1)[1])
            for line in f if ":" in line
        }

def save_repeat(chat_id: int, count: int):
    data = load_repeats()
    data[str(chat_id)] = count
    with open(REPEATS_FILE, "w") as f:
        for uid, cnt in data.items():
            f.write(f"{uid}:{cnt}\n")

def get_user_repeat(chat_id: int) -> int:
    return load_repeats().get(str(chat_id), 1)

# ----------------- Команды -----------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    await update.message.reply_text("✅ Вы подписаны на напоминания.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_user(chat_id)
    await update.message.reply_text("❌ Вы отписались от напоминаний.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Команды:\n"
        "/start — включить напоминания\n"
        "/stop — отключить напоминания\n"
        "/replays <число> — установить количество повторов\n"
        "/test — проверить работу бота\n"
        
        "/help — справка"
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает!")



async def replays_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args

    if not args or not args[0].isdigit():
        await update.message.reply_text("❗ Использование: /replays <число от 1 до 10>")
        return

    count = int(args[0])
    if count < 1 or count > 10:
        await update.message.reply_text("❗ Введите число от 1 до 10.")
        return

    save_repeat(chat_id, count)
    await update.message.reply_text(f"🔁 Повторов установлено: {count}")

# ----------------- Напоминания -----------------

async def send_reminders(app: Application):
    users = load_users()
    repeats = load_repeats()

    for user_id in users:
        repeat_count = repeats.get(user_id, 1)
        try:
            for i in range(repeat_count):
                await app.bot.send_message(chat_id=int(user_id), text="🔔 Напоминание: зайдите в Старс Банк")
                if i + 1 < repeat_count:
                    await asyncio.sleep(10)
        except Exception as e:
            print(f"❌ Ошибка при отправке пользователю {user_id}: {e}")

# ----------------- Настройка Telegram меню -----------------

async def on_startup(app: Application):
    commands = [BotCommand("start", "Включить напоминания"),
        BotCommand("stop", "Отключить напоминания"),
        BotCommand("replays", "Установить количество повторов"),
        BotCommand("test", "Проверить работу бота"),

        BotCommand("help", "Справка"),
    ]
    await app.bot.set_my_commands(commands)

# ----------------- Главная функция -----------------

async def main():
    app = Application.builder().token(TOKEN).post_init(on_startup).build()

    # Команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("test", test_command))

    app.add_handler(CommandHandler("replays", replays_command))

    # Планировщик
    scheduler = AsyncIOScheduler()
    times = [(21, 1), (9, 1), (19, 1)]
    for hour, minute in times:
        scheduler.add_job(send_reminders, 'cron', hour=hour, minute=minute, args=[app])
    scheduler.start()

    print("Денис иди нахуй отсюда.")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
