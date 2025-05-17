from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

from app import create_app
from app.database import db
from mail import send_email
from key_gen import generate_otp
from test_db import (
    get_user_by_field, verify_password,
     add_two_factor_secret, get_two_factor_secret, delete_two_factor_secret
)

import os

# Flask
flask_app = create_app()
flask_app.app_context().push()

# Состояния
STATE = {
    "EMAIL": "email",
    "PASSWORD": "password",
    "CODE": "code",
    "AD_TITLE": "ad_title",
    "AD_DESC": "ad_desc",
    "AD_CATEGORY": "ad_category",
    "AD_PRICE": "ad_price",
    "AD_PHOTO": "ad_photo"
}

user_states = {}
user_data = {}
user_sessions = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("🔐 Авторизация")],
        [KeyboardButton("➕ Новое объявление")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=markup)


async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_states[uid] = STATE["EMAIL"]
    await update.message.reply_text("Введите email:")


async def new_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_sessions:
        await update.message.reply_text("❗ Сначала авторизуйтесь командой /auth")
        return
    user_data[uid] = {}
    user_states[uid] = STATE["AD_TITLE"]
    await update.message.reply_text("Введите заголовок объявления:")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text


    # Обработка кнопок
    if text == "🔐 Авторизация":
        return await auth(update, context)
    elif text == "➕ Новое объявление":
        return await new_ad(update, context)

    state = user_states.get(uid)



    if state == STATE["EMAIL"]:
        user_data[uid] = {"email": text}
        user_states[uid] = STATE["PASSWORD"]
        await update.message.reply_text("Введите пароль:")

    elif state == STATE["PASSWORD"]:
        email = user_data[uid]["email"]
        user = get_user_by_field("email", email)
        if user and verify_password(email, text):
            code = generate_otp()
            send_email(email, code)
            add_two_factor_secret(user.id, code)
            db.session.commit()
            user_data[uid]["user_id"] = user.id
            user_states[uid] = STATE["CODE"]
            await update.message.reply_text("📩 Введите код, отправленный на email:")
        else:
            await update.message.reply_text("❌ Неверный email или пароль")
            user_states.pop(uid, None)
            user_data.pop(uid, None)

    elif state == STATE["CODE"]:
        user_id = user_data[uid]["user_id"]
        if text == get_two_factor_secret(user_id):
            delete_two_factor_secret(user_id)
            db.session.commit()
            user_sessions[uid] = user_id
            user_states.pop(uid, None)
            user_data.pop(uid, None)
            await update.message.reply_text("✅ Авторизация успешна!")
        else:
            await update.message.reply_text("❌ Неверный код")

    elif state == STATE["AD_TITLE"]:
        user_data[uid]["title"] = text
        user_states[uid] = STATE["AD_DESC"]
        await update.message.reply_text("Введите описание:")

    elif state == STATE["AD_DESC"]:
        user_data[uid]["description"] = text
        user_states[uid] = STATE["AD_CATEGORY"]
        await update.message.reply_text("Введите категорию:")

    elif state == STATE["AD_CATEGORY"]:
        user_data[uid]["category"] = text
        user_states[uid] = STATE["AD_PRICE"]
        await update.message.reply_text("Введите цену:")

    elif state == STATE["AD_PRICE"]:
        try:
            user_data[uid]["price"] = float(text)
        except ValueError:
            await update.message.reply_text("Введите корректную цену (например 1000.0):")
            return
        user_data[uid]["photos"] = []
        user_states[uid] = STATE["AD_PHOTO"]
        await update.message.reply_text("Отправьте фото объявления. После этого отправьте /done")

# Фото
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if user_states.get(uid) != STATE["AD_PHOTO"]:
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    path = f"/static/images/{file.file_id}.jpg"
    os.makedirs("app/static/images", exist_ok=True)
    await file.download_to_drive(f"app/{path}")
    user_data[uid]["photos"].append(path)

    await update.message.reply_text("Фото добавлено. Добавьте ещё или введите /done")



async def ad_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    from app.database import Advertisement, Image

    data = user_data[uid]
    ad = Advertisement(
        title=data["title"],
        description=data["description"],
        category=data["category"],
        price=data["price"],
        user_id=user_sessions[uid]
    )
    db.session.add(ad)
    db.session.commit()

    for i, path in enumerate(data["photos"]):
        db.session.add(Image(
            advertisement_id=ad.id,
            filename=path,
            url_path=path,
            is_main=(i == 0)
        ))

    db.session.commit()
    user_states.pop(uid, None)
    user_data.pop(uid, None)

    await update.message.reply_text("✅ Объявление добавлено!")

# main
def main():
    application = Application.builder().token("8159558258:AAEZpaZb7gyIXOv9sa6cBHXEaCWMQwBYppQ").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("auth", auth))
    application.add_handler(CommandHandler("new_ad", new_ad))
    application.add_handler(CommandHandler("done", ad_done))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
