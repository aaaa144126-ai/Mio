from telegram.ext import Application
from config import BOT_TOKEN


def build_application():
    application = Application.builder().token(BOT_TOKEN).build()

    from telegram_bot.handlers_student import register_student_handlers
    from telegram_bot.handlers_admin import register_admin_handlers

    # الأدمن الأول عشان أوامر الأدمن تتفحص قبل الهاندلرز العامة
    register_admin_handlers(application)
    register_student_handlers(application)

    return application
