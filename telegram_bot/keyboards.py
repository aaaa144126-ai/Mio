from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from models import Term, Subject, Lecture, Material

MATERIAL_ICONS = {"note": "📄", "video": "🎥", "link": "🔗"}
MATERIAL_LABELS = {"note": "مذكرة", "video": "فيديو", "link": "رابط"}


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 تصفح المحتوى", callback_data="browse:terms")],
        [InlineKeyboardButton("🆘 طلب مساعدة", callback_data="help:new")],
        [InlineKeyboardButton("📋 الطلبات المفتوحة", callback_data="help:list:1")],
    ])


def terms_keyboard():
    terms = Term.query.order_by(Term.order).all()
    rows = [[InlineKeyboardButton(t.name, callback_data=f"browse:term:{t.id}")] for t in terms]
    if not rows:
        rows = [[InlineKeyboardButton("لا يوجد ترمات مضافة بعد", callback_data="noop")]]
    rows.append([InlineKeyboardButton("⬅️ رجوع", callback_data="browse:home")])
    return InlineKeyboardMarkup(rows)


def subjects_keyboard(term_id):
    subjects = Subject.query.filter_by(term_id=term_id).order_by(Subject.order).all()
    rows = [[InlineKeyboardButton(s.name, callback_data=f"browse:subject:{s.id}")] for s in subjects]
    if not rows:
        rows = [[InlineKeyboardButton("لا يوجد مواد مضافة بعد", callback_data="noop")]]
    rows.append([InlineKeyboardButton("⬅️ رجوع للترمات", callback_data="browse:terms")])
    return InlineKeyboardMarkup(rows)


def lectures_keyboard(subject_id):
    subject = Subject.query.get(subject_id)
    lectures = Lecture.query.filter_by(subject_id=subject_id).order_by(Lecture.order).all()
    rows = [[InlineKeyboardButton(l.name, callback_data=f"browse:lecture:{l.id}")] for l in lectures]
    if not rows:
        rows = [[InlineKeyboardButton("لا يوجد محاضرات مضافة بعد", callback_data="noop")]]
    rows.append([InlineKeyboardButton("⬅️ رجوع للمواد", callback_data=f"browse:term:{subject.term_id}")])
    return InlineKeyboardMarkup(rows)


def materials_keyboard(lecture_id):
    lecture = Lecture.query.get(lecture_id)
    materials = Material.query.filter_by(lecture_id=lecture_id).all()
    rows = []
    for m in materials:
        icon = MATERIAL_ICONS.get(m.material_type, "📎")
        rows.append([InlineKeyboardButton(f"{icon} {m.title}", callback_data=f"browse:material:{m.id}")])
    if not rows:
        rows = [[InlineKeyboardButton("لا يوجد مواد مضافة بعد", callback_data="noop")]]
    rows.append([InlineKeyboardButton("⬅️ رجوع للمحاضرات", callback_data=f"browse:subject:{lecture.subject_id}")])
    return InlineKeyboardMarkup(rows)


def back_to_material_keyboard(lecture_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ رجوع للمحاضرة", callback_data=f"browse:lecture:{lecture_id}")]
    ])


def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]])


def claim_keyboard(request_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🙋 أنا هساعد في الطلب ده", callback_data=f"help:claim:{request_id}")]
    ])


def requests_list_keyboard(requests, page):
    rows = []
    for r in requests:
        label = f"#{r.id} - {r.subject_name or 'عام'}"
        rows.append([InlineKeyboardButton(label, callback_data=f"help:view:{r.id}")])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"help:list:{page - 1}"))
    nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"help:list:{page + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="browse:home")])
    return InlineKeyboardMarkup(rows)


def admin_terms_keyboard():
    terms = Term.query.order_by(Term.order).all()
    rows = [[InlineKeyboardButton(t.name, callback_data=f"a:term:{t.id}")] for t in terms]
    rows.append([InlineKeyboardButton("➕ ترم جديد", callback_data="a:newterm")])
    return InlineKeyboardMarkup(rows)


def admin_subjects_keyboard(term_id):
    subjects = Subject.query.filter_by(term_id=term_id).order_by(Subject.order).all()
    rows = [[InlineKeyboardButton(s.name, callback_data=f"a:subject:{s.id}")] for s in subjects]
    rows.append([InlineKeyboardButton("➕ مادة جديدة", callback_data="a:newsubject")])
    return InlineKeyboardMarkup(rows)


def admin_lectures_keyboard(subject_id):
    lectures = Lecture.query.filter_by(subject_id=subject_id).order_by(Lecture.order).all()
    rows = [[InlineKeyboardButton(l.name, callback_data=f"a:lecture:{l.id}")] for l in lectures]
    rows.append([InlineKeyboardButton("➕ محاضرة جديدة", callback_data="a:newlecture")])
    return InlineKeyboardMarkup(rows)


def admin_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 مذكرة", callback_data="a:type:note")],
        [InlineKeyboardButton("🎥 فيديو", callback_data="a:type:video")],
        [InlineKeyboardButton("🔗 رابط", callback_data="a:type:link")],
    ])


def admin_skip_desc_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⏭ تخطي الوصف", callback_data="a:skipdesc")]])
