import asyncio
import logging
import threading

import requests
from flask import (
    Flask, request, render_template, redirect, url_for, session, flash, abort
)
from telegram import Update

from config import (
    BOT_TOKEN, ADMIN_IDS, BASE_URL, ADMIN_PASSWORD, SECRET_KEY,
    DATABASE_URL, BOT_TITLE
)
from models import db, Term, Subject, Lecture, Material, HelpRequest
from telegram_bot import build_application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SECRET_KEY"] = SECRET_KEY
db.init_app(app)

with app.app_context():
    db.create_all()

# ---------------- تشغيل بوت تليجرام في ثريد منفصل مع event loop خاص بيه ----------------

telegram_app = build_application()
bot_loop = asyncio.new_event_loop()


def _run_loop():
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_forever()


threading.Thread(target=_run_loop, daemon=True).start()
asyncio.run_coroutine_threadsafe(telegram_app.initialize(), bot_loop).result()

if BASE_URL:
    webhook_url = f"{BASE_URL.rstrip('/')}/webhook/{BOT_TOKEN}"
    asyncio.run_coroutine_threadsafe(
        telegram_app.bot.set_webhook(webhook_url), bot_loop
    ).result()
    logger.info("Webhook set to %s", webhook_url)


async def _process_update(data):
    update = Update.de_json(data, telegram_app.bot)
    with app.app_context():
        await telegram_app.process_update(update)


@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    asyncio.run_coroutine_threadsafe(_process_update(data), bot_loop)
    return "ok"


# ---------------- الموقع العام (تصفح فقط) ----------------

@app.route("/")
def home():
    terms = Term.query.order_by(Term.order).all()
    return render_template("home.html", terms=terms, bot_title=BOT_TITLE)


@app.route("/term/<int:term_id>")
def view_term(term_id):
    term = Term.query.get_or_404(term_id)
    return render_template("term.html", term=term, bot_title=BOT_TITLE)


@app.route("/subject/<int:subject_id>")
def view_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    return render_template("subject.html", subject=subject, bot_title=BOT_TITLE)


@app.route("/lecture/<int:lecture_id>")
def view_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    return render_template("lecture.html", lecture=lecture, bot_title=BOT_TITLE)


@app.route("/material/<int:material_id>/download")
def download_material(material_id):
    """بيجيب رابط تحميل مباشر من تليجرام لحظيًا (الرابط بيتجدد كل مرة)"""
    material = Material.query.get_or_404(material_id)
    if not material.telegram_file_id:
        if material.url:
            return redirect(material.url)
        abort(404)
    resp = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
        params={"file_id": material.telegram_file_id}, timeout=15
    )
    result = resp.json()
    if not result.get("ok"):
        abort(404)
    file_path = result["result"]["file_path"]
    return redirect(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}")


# ---------------- لوحة تحكم الأدمن (ويب) ----------------

def admin_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return func(*args, **kwargs)
    return wrapper


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("الباسورد غلط")
    return render_template("admin_login.html", bot_title=BOT_TITLE)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    terms = Term.query.order_by(Term.order).all()
    open_requests = HelpRequest.query.filter_by(status="open").order_by(HelpRequest.created_at.desc()).all()
    return render_template("admin_dashboard.html", terms=terms, open_requests=open_requests, bot_title=BOT_TITLE)


@app.route("/admin/term/add", methods=["POST"])
@admin_required
def admin_add_term():
    name = request.form.get("name", "").strip()
    if name:
        db.session.add(Term(name=name, order=Term.query.count()))
        db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/subject/add", methods=["POST"])
@admin_required
def admin_add_subject():
    term_id = int(request.form.get("term_id"))
    name = request.form.get("name", "").strip()
    if name:
        db.session.add(Subject(term_id=term_id, name=name, order=Subject.query.filter_by(term_id=term_id).count()))
        db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/lecture/add", methods=["POST"])
@admin_required
def admin_add_lecture():
    subject_id = int(request.form.get("subject_id"))
    name = request.form.get("name", "").strip()
    if name:
        db.session.add(Lecture(subject_id=subject_id, name=name, order=Lecture.query.filter_by(subject_id=subject_id).count()))
        db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/lecture/<int:lecture_id>")
@admin_required
def admin_view_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    return render_template("admin_lecture.html", lecture=lecture, bot_title=BOT_TITLE)


@app.route("/admin/material/add", methods=["POST"])
@admin_required
def admin_add_material():
    """
    بيرفع الملف مباشرة لتليجرام (لشات الأدمن) عشان ناخد منه telegram_file_id
    ونضمن تخزين دائم ومجاني، أو بيحفظ رابط لو المستخدم دخل رابط بدل ملف.
    """
    lecture_id = int(request.form.get("lecture_id"))
    material_type = request.form.get("material_type")
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip() or None
    url = request.form.get("url", "").strip() or None
    file = request.files.get("file")

    if not title:
        flash("لازم تكتب عنوان")
        return redirect(url_for("admin_view_lecture", lecture_id=lecture_id))

    telegram_file_id = None
    telegram_file_type = None

    if file and file.filename:
        if not ADMIN_IDS:
            flash("لازم تضيف ADMIN_IDS في الإعدادات عشان رفع الملفات يشتغل")
            return redirect(url_for("admin_view_lecture", lecture_id=lecture_id))
        storage_chat_id = ADMIN_IDS[0]
        method = "sendVideo" if material_type == "video" else "sendDocument"
        field_name = "video" if material_type == "video" else "document"
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
            data={"chat_id": storage_chat_id},
            files={field_name: (file.filename, file.stream, file.mimetype)},
            timeout=60,
        )
        result = resp.json()
        if not result.get("ok"):
            flash(f"فشل رفع الملف: {result.get('description')}")
            return redirect(url_for("admin_view_lecture", lecture_id=lecture_id))
        msg_result = result["result"]
        if "document" in msg_result:
            telegram_file_id = msg_result["document"]["file_id"]
            telegram_file_type = "document"
        elif "video" in msg_result:
            telegram_file_id = msg_result["video"]["file_id"]
            telegram_file_type = "video"
    elif not url:
        flash("لازم ترفع ملف أو تكتب رابط")
        return redirect(url_for("admin_view_lecture", lecture_id=lecture_id))

    material = Material(
        lecture_id=lecture_id,
        material_type=material_type,
        title=title,
        description=description,
        telegram_file_id=telegram_file_id,
        telegram_file_type=telegram_file_type,
        url=url,
        added_by="admin (web)",
    )
    db.session.add(material)
    db.session.commit()
    flash("تم إضافة المادة بنجاح")
    return redirect(url_for("admin_view_lecture", lecture_id=lecture_id))


@app.route("/admin/material/<int:material_id>/delete", methods=["POST"])
@admin_required
def admin_delete_material(material_id):
    material = Material.query.get_or_404(material_id)
    lecture_id = material.lecture_id
    db.session.delete(material)
    db.session.commit()
    return redirect(url_for("admin_view_lecture", lecture_id=lecture_id))


@app.route("/admin/requests")
@admin_required
def admin_requests():
    requests_ = HelpRequest.query.order_by(HelpRequest.created_at.desc()).all()
    return render_template("admin_requests.html", requests=requests_, bot_title=BOT_TITLE)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
