"""
موديلات قاعدة البيانات لبوت طلاب التمريض - الفرقة التالتة
التقسيم: Term (ترم) -> Subject (مادة) -> Lecture (محاضرة) -> Material (مذكرة/فيديو/رابط)
+ HelpRequest لطلبات مساعدة الطلاب
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Term(db.Model):
    __tablename__ = "terms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # مثال: الترم الأول
    order = db.Column(db.Integer, default=0)

    subjects = db.relationship(
        "Subject", backref="term", cascade="all, delete-orphan",
        order_by="Subject.order"
    )

    def __repr__(self):
        return f"<Term {self.name}>"


class Subject(db.Model):
    __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)  # مثال: تشريح
    order = db.Column(db.Integer, default=0)

    lectures = db.relationship(
        "Lecture", backref="subject", cascade="all, delete-orphan",
        order_by="Lecture.order"
    )

    def __repr__(self):
        return f"<Subject {self.name}>"


class Lecture(db.Model):
    __tablename__ = "lectures"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)  # مثال: المحاضرة الأولى - مقدمة
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    materials = db.relationship(
        "Material", backref="lecture", cascade="all, delete-orphan",
        order_by="Material.created_at"
    )

    def __repr__(self):
        return f"<Lecture {self.name}>"


class Material(db.Model):
    """
    مادة داخل المحاضرة: مذكرة (ملف تليجرام) / فيديو (رابط أو ملف) / رابط عادي
    لو النوع ملف: بنخزن telegram_file_id بس (تخزين تليجرام مجاني وأبدي)
    لو النوع رابط: بنخزن url
    """
    __tablename__ = "materials"
    id = db.Column(db.Integer, primary_key=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey("lectures.id"), nullable=False)
    material_type = db.Column(db.String(20), nullable=False)  # note / video / link
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))

    # للملفات المرفوعة عن طريق تليجرام (مذكرات PDF، فيديوهات مرفوعة)
    telegram_file_id = db.Column(db.String(300))
    telegram_file_type = db.Column(db.String(30))  # document / video

    # للروابط (يوتيوب، درايف، إلخ)
    url = db.Column(db.String(1000))

    added_by = db.Column(db.String(150))  # اسم/يوزر الأدمن اللي رفع
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Material {self.title} ({self.material_type})>"


class HelpRequest(db.Model):
    """طلبات مساعدة الطلاب - أي طالب محتاج مساعدة في مادة/محاضرة معينة"""
    __tablename__ = "help_requests"
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(150))
    telegram_user_id = db.Column(db.BigInteger, nullable=False)
    telegram_username = db.Column(db.String(150))
    subject_name = db.Column(db.String(150))
    description = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.String(20), default="open")  # open / claimed / done
    claimed_by_username = db.Column(db.String(150))
    claimed_by_user_id = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<HelpRequest {self.id} - {self.status}>"
