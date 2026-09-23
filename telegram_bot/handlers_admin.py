import logging
from functools import wraps
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, CommandHandler, filters
)

from models import db, Term, Subject, Lecture, Material, HelpRequest
from config import ADMIN_IDS
from telegram_bot import keyboards as kb

logger = logging.getLogger(__name__)

(CHOOSE_TERM, NEW_TERM, CHOOSE_SUBJECT, NEW_SUBJECT, CHOOSE_LECTURE,
 NEW_LECTURE, CHOOSE_TYPE, ASK_TITLE, ASK_CONTENT, ASK_DESC) = range(10)


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or user.id not in ADMIN_IDS:
            if update.message:
                await update.message.reply_text("🚫 الأمر ده للأدمن بس.")
            elif update.callback_query:
                await update.callback_query.answer("🚫 للأدمن بس", show_alert=True)
            return ConversationHandler.END
        return await func(update, context)
    return wrapper


@admin_only
async def addmaterial_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_material"] = {}
    await update.message.reply_text("📚 اختار الترم أو ضيف ترم جديد:", reply_markup=kb.admin_terms_keyboard())
    return CHOOSE_TERM


async def choose_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "a:newterm":
        await query.edit_message_text("اكتب اسم الترم الجديد (مثال: الترم الأول):")
        return NEW_TERM
    term_id = int(query.data.split(":")[2])
    context.user_data["new_material"]["term_id"] = term_id
    await query.edit_message_text("📖 اختار المادة أو ضيف مادة جديدة:", reply_markup=kb.admin_subjects_keyboard(term_id))
    return CHOOSE_SUBJECT


async def new_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    count = Term.query.count()
    term = Term(name=name, order=count)
    db.session.add(term)
    db.session.commit()
    context.user_data["new_material"]["term_id"] = term.id
    await update.message.reply_text(
        f"✅ تم إضافة الترم: {name}\n📖 اختار المادة أو ضيف مادة جديدة:",
        reply_markup=kb.admin_subjects_keyboard(term.id),
    )
    return CHOOSE_SUBJECT


async def choose_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "a:newsubject":
        await query.edit_message_text("اكتب اسم المادة الجديدة:")
        return NEW_SUBJECT
    subject_id = int(query.data.split(":")[2])
    context.user_data["new_material"]["subject_id"] = subject_id
    await query.edit_message_text(
        "🗂 اختار المحاضرة أو ضيف
