import logging
import asyncio
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

BOT_TOKEN = "8183835724:AAHKgrxI-gKaWw8k-nyBKFRj7NZf9rxCSu4"

ADMIN_CHAT_IDS = [1513456162, 403956138, 1639043122]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

last_message_time = {}
pending_replies = {}  # کلید: conversation_id، مقدار: dict با user_id، نوع پیام و admins_replied (ست ادمین‌ها)

conversation_counter = 1

BAD_WORDS = {
    "کیر", "کیری", "کص", "کصی", "کونی", "کون", "ممه", "جاکش", "جاکشی",
    "کصکش", "کصلیس", "حرومزاده", "مادرجنده", "جنده", "مادرقحبه", "مادر",
    "قحبه", "گه", "گهی", "دیوث", "مار", "جنده", "ننه", "پولی", "تخم",
    "حروم", "ولدزنا", "زنازاده", "سیکتیر", "سیک", "سیک تیر", "کصننت", "کص",
    "ننت", "گاییدن", "میگام", "بگارفته", "بگایی", "زن کصده", "کصمادر",
    "کص مادر", "زن جنده", "زن کص ده", "کونی مقام", "آب کون", "اوبی", "OBI",
    "obi", "اب کون", "ننتو گاییدم", "زنت رو گاییدم", "زنتو گاییدم", 
    "زنت رو گاییدم", "میکنمت", "دودول", "دول", "دولاب", "میگامت", "کیرم",
    "کیرمی", "کونده", "خایه", "تخمام", "عن", "ننه بیزنسی", "ننه پولی",
    "100 تومنی", "کص زنت"
}

def contains_bad_word(text):
    if not text:
        return False
    text_lower = text.lower()
    for bad_word in BAD_WORDS:
        if bad_word in text_lower:
            return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 سلام رفیق!\n"
        "به ربات تیم امنیت سایبری EclipticaSec خوش اومدی! 🚀\n\n"
        "هر سوال یا مشکلی داشتی بهم بگو، اینجا برای کمک هستیم! 🔐"
    )
    await update.message.reply_text(text)

async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global conversation_counter
    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name or "کاربر"

    now = datetime.datetime.now()
    last_time = last_message_time.get(user_id)
    if last_time and (now - last_time).total_seconds() < 60:
        await update.message.reply_text("⏳ لطفا کمی صبر کن و بعد دوباره پیام بده!")
        return
    last_message_time[user_id] = now

    text = update.message.text

    if contains_bad_word(text):
        report_text = (
            f"⚠️ <b>پیام شامل کلمات زشت دریافت شد!</b>\n"
            f"👤 کاربر: @{username}\n"
            f"🆔 شناسه کاربر: <code>{user_id}</code>\n"
            f"💬 متن پیام:\n"
            f"───────────────────\n"
            f"{text}\n"
            f"───────────────────"
        )
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=report_text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"ارسال پیام به ادمین {admin_id} با خطا مواجه شد: {e}")
        await update.message.reply_text("😄 لطفاً کمی مودب‌تر باش، رفیق!")
        return

    conversation_id = conversation_counter
    conversation_counter += 1
    pending_replies[conversation_id] = {"user_id": user_id, "type": "text", "admins_replied": set()}

    admin_text = (
        "📩 <b>پیام جدید از کاربر</b>\n"
        f"👤 نام کاربری: @{username}\n"
        f"🆔 شناسه کاربر: <code>{user_id}</code>\n\n"
        "💬 متن پیام:\n"
        "───────────────────\n"
        f"{text}\n"
        "───────────────────\n\n"
        f"✍️ برای پاسخ دادن، دستور زیر را استفاده کن:\n"
        f"<code>/reply {conversation_id} پاسخ شما</code>\n\n"
        "⏳ لطفاً در پاسخگویی دقت کن و صبور باش!"
    )

    for admin_id in ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"ارسال پیام به ادمین {admin_id} با خطا مواجه شد: {e}")

    await update.message.reply_text("پیامتون ارسال شد. لطفاً منتظر پاسخ تیم EclipticaSec باشید.✅")

async def handle_user_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global conversation_counter
    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name or "کاربر"

    now = datetime.datetime.now()
    last_time = last_message_time.get(user_id)
    if last_time and (now - last_time).total_seconds() < 10:
        await update.message.reply_text("⏳ لطفا کمی صبر کن و بعد دوباره فایل بفرست!")
        return
    last_message_time[user_id] = now

    photo_file = update.message.photo[-1]
    caption = update.message.caption

    if contains_bad_word(caption):
        await update.message.reply_text("🚫 لطفاً کپشن عکس حاوی کلمات نامناسب نباشد.")
        report_text = (
            f"⚠️ <b>کپشن عکس شامل کلمات زشت است!</b>\n"
            f"👤 کاربر: @{username}\n"
            f"🆔 شناسه کاربر: <code>{user_id}</code>\n\n"
            f"📷 عکس با کپشن:\n"
            f"{caption}\n"
            "───────────────────"
        )
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=report_text, parse_mode="HTML")
                await context.bot.send_photo(chat_id=admin_id, photo=photo_file.file_id, caption=caption)
            except Exception as e:
                logger.error(f"ارسال کپشن زشت عکس به ادمین {admin_id} با خطا مواجه شد: {e}")
        return

    conversation_id = conversation_counter
    conversation_counter += 1
    pending_replies[conversation_id] = {"user_id": user_id, "type": "photo", "file_id": photo_file.file_id, "admins_replied": set()}

    admin_text = (
        "📩 <b>عکس جدید از کاربر دریافت شد</b>\n"
        f"👤 نام کاربری: @{username}\n"
        f"🆔 شناسه کاربر: <code>{user_id}</code>\n\n"
        f"📷 عکس با کپشن:\n"
        "───────────────────\n"
        f"{caption or 'کپشنی وجود ندارد'}\n"
        "───────────────────\n\n"
        f"✍️ برای پاسخ دادن، دستور زیر را استفاده کن:\n"
        f"<code>/reply {conversation_id} پاسخ شما</code>\n\n"
        "⏳ لطفاً در پاسخگویی دقت کن و صبور باش!"
    )

    for admin_id in ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
            await context.bot.send_photo(chat_id=admin_id, photo=photo_file.file_id, caption=caption)
        except Exception as e:
            logger.error(f"ارسال عکس به ادمین {admin_id} با خطا مواجه شد: {e}")

    await update.message.reply_text("عکس شما دریافت شد. لطفاً منتظر پاسخ تیم EclipticaSec باشید.✅")

async def handle_user_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global conversation_counter
    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name or "کاربر"

    now = datetime.datetime.now()
    last_time = last_message_time.get(user_id)
    if last_time and (now - last_time).total_seconds() < 10:
        await update.message.reply_text("⏳ لطفا کمی صبر کن و بعد دوباره فایل بفرست!")
        return
    last_message_time[user_id] = now

    voice = update.message.voice

    conversation_id = conversation_counter
    conversation_counter += 1
    pending_replies[conversation_id] = {"user_id": user_id, "type": "voice", "file_id": voice.file_id, "admins_replied": set()}

    admin_text = (
        "📩 <b>ویس جدید از کاربر دریافت شد</b>\n"
        f"👤 نام کاربری: @{username}\n"
        f"🆔 شناسه کاربر: <code>{user_id}</code>\n\n"
        f"🎤 ویس:\n"
        "───────────────────\n\n"
        f"✍️ برای پاسخ دادن، دستور زیر را استفاده کن:\n"
        f"<code>/reply {conversation_id} پاسخ شما</code>\n\n"
        "⏳ لطفاً در پاسخگویی دقت کن و صبور باش!"
    )

    for admin_id in ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
            await context.bot.send_voice(chat_id=admin_id, voice=voice.file_id)
        except Exception as e:
            logger.error(f"ارسال ویس به ادمین {admin_id} با خطا مواجه شد: {e}")

    await update.message.reply_text("ویس شما دریافت شد. لطفاً منتظر پاسخ تیم EclipticaSec باشید.✅")

async def handle_user_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global conversation_counter
    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name or "کاربر"

    now = datetime.datetime.now()
    last_time = last_message_time.get(user_id)
    if last_time and (now - last_time).total_seconds() < 10:
        await update.message.reply_text("⏳ لطفا کمی صبر کن و بعد دوباره فایل بفرست!")
        return
    last_message_time[user_id] = now

    video = update.message.video
    caption = update.message.caption

    conversation_id = conversation_counter
    conversation_counter += 1
    pending_replies[conversation_id] = {"user_id": user_id, "type": "video", "file_id": video.file_id, "admins_replied": set()}

    admin_text = (
        "📩 <b>ویدیو جدید از کاربر دریافت شد</b>\n"
        f"👤 نام کاربری: @{username}\n"
        f"🆔 شناسه کاربر: <code>{user_id}</code>\n\n"
        f"🎥 ویدیو با کپشن:\n"
        "───────────────────\n"
        f"{caption or 'کپشنی وجود ندارد'}\n"
        "───────────────────\n\n"
        f"✍️ برای پاسخ دادن، دستور زیر را استفاده کن:\n"
        f"<code>/reply {conversation_id} پاسخ شما</code>\n\n"
        "⏳ لطفاً در پاسخگویی دقت کن و صبور باش!"
    )

    for admin_id in ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
            await context.bot.send_video(chat_id=admin_id, video=video.file_id, caption=caption)
        except Exception as e:
            logger.error(f"ارسال ویدیو به ادمین {admin_id} با خطا مواجه شد: {e}")

    await update.message.reply_text("ویدیو شما دریافت شد. لطفاً منتظر پاسخ تیم EclipticaSec باشید.✅")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id not in ADMIN_CHAT_IDS:
        await update.message.reply_text("⛔ این دستور فقط برای ادمین‌هاست.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت دستور اشتباه است.\nمثال: /reply 5 پاسخ شما")
        return

    try:
        reply_to_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ شناسه پیام باید عدد باشد.")
        return

    reply_text = " ".join(args[1:])

    if reply_to_id not in pending_replies:
        await update.message.reply_text("❌ پیامی با این شناسه پیدا نشد.")
        return

    data = pending_replies[reply_to_id]
    user_id = data["user_id"]

    # بررسی اینکه آیا این ادمین قبلا جواب داده یا نه
    if "admins_replied" not in data:
        data["admins_replied"] = set()
    if user.id in data["admins_replied"]:
        await update.message.reply_text("❌ شما قبلاً به این پیام پاسخ داده‌اید.")
        return

    # ارسال پیام پاسخ به کاربر
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🛡️ پاسخ از تیم EclipticaSec:\n\n{reply_text}"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ ارسال پیام به کاربر با خطا مواجه شد:\n{e}")
        return

    data["admins_replied"].add(user.id)

    # اگر این اولین پاسخ است، به بقیه ادمین‌هایی که جواب ندادن پیام اطلاع بده
    if len(data["admins_replied"]) == 1:
        admin_username = user.username or user.first_name or str(user.id)
        not_replied_admins = [aid for aid in ADMIN_CHAT_IDS if aid not in data["admins_replied"]]
        for admin_id in not_replied_admins:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"⚠️ ادمین @{admin_username} به پیام شماره {reply_to_id} پاسخ داده است."
                )
            except Exception as e:
                logger.error(f"ارسال اطلاع به ادمین {admin_id} با خطا مواجه شد: {e}")

    # حذف پیام از pending_replies (می‌تونی این خط رو حذف کنی اگر میخوای پیام بمونه تا همه جواب بدن)
    del pending_replies[reply_to_id]

    await update.message.reply_text("پاسخ شما ثبت و ارسال شد.✅")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reply", handle_admin_reply))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_user_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_user_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_user_voice))
    application.add_handler(MessageHandler(filters.VIDEO, handle_user_video))

    print("🤖 ربات داره اجرا میشه...")
    application.run_polling()

if __name__ == "__main__":
    main()
