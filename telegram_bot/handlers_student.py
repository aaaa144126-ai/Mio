import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, CommandHandler, filters
)

from models import db, Term, Subject, Lecture, Material, HelpRequest
from config import BOT_TITLE, ADMIN_IDS
from telegram_bot import keyboards as kb

logger = logging.getLogger(__name__)

ASK_SUBJECT, ASK_DESC = range(2)
PAGE_SIZE = 5


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"👋 أهلاً بيك في {BOT_TITLE}\n\n"
        "من هنا تقدر:\n"
        "📚 تتصفح المحاضرات والمذكرات والروابط بتاعة كل مادة\n"
        "🆘 تطلب مساعدة من زمايلك في مادة معينة\n"
        "📋 تشوف طلبات زمايلك وتساعدهم\n\n"
        "اختار من تحت:"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=kb.main_menu_keyboard())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=kb.main_menu_keyboard())


async def browse_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # browse:home | browse:terms | browse:term:<id> | browse:subject:<id> | browse:lecture:<id> | browse:material:<id>
    parts = data.split(":")

    if data == "browse:home":
        await start(update, context)
        return

    if data == "browse:terms":
        await query.edit_message_text("📚 اختار الترم:", reply_markup=kb.terms_keyboard())
        return

    kind = parts[1]
    if kind == "term":
        term_id = int(parts[2])
        term = Term.query.get(term_id)
        await query.edit_message_text(
            f"📚 {term.name}\nاختار المادة:", reply_markup=kb.subjects_keyboard(term_id)
        )
    elif kind == "subject":
        subject_id = int(parts[2])
        subject = Subject.query.get(subject_id)
        await query.edit_message_text(
            f"📖 {subject.name}\nاختار المحاضرة:", reply_markup=kb.lectures_keyboard(subject_id)
        )
    elif kind == "lecture":
        lecture_id = int(parts[2])
        lecture = Lecture.query.get(lecture_id)
        await query.edit_message_text(
            f"🗂 {lecture.name}\nالمواد المتاحة:", reply_markup=kb.materials_keyboard(lecture_id)
        )
    elif kind == "material":
        material_id = int(parts[2])
        material = Material.query.get(material_id)
        caption = f"{kb.MATERIAL_ICONS.get(material.material_type, '📎')} {material.title}"
        if material.description:
            caption += f"\n{material.description}"
        try:
            if material.material_type == "link" or (material.url and not material.telegram_file_id):
                caption += f"\n\n🔗 {material.url}"
                await query.message.reply_text(caption, reply_markup=kb.back_to_material_keyboard(material.lecture_id))
            elif material.telegram_file_type == "video":
                await query.message.reply_video(
                    material.telegram_file_id, caption=caption,
                    reply_markup=kb.back_to_material_keyboard(material.lecture_id)
                )
            else:
                await query.message.reply_document(
                    material.telegram_file_id, caption=caption,
                    reply_markup=kb.back_to_material_keyboard(material.lecture_id)
                )
        except Exception as
