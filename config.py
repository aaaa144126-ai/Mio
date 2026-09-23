import os
from dotenv import load_dotenv

load_dotenv()

# توكن البوت من BotFather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# آي ديز الأدمنز (تليجرام)، مفصولة بفاصلة، مثال: "111111111,222222222"
ADMIN_IDS = [
    int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]

# رابط السيرفر بعد النشر (بيتستخدم لضبط الـ webhook)، مثال:
# https://your-app.onrender.com
BASE_URL = os.environ.get("BASE_URL", "")

# باسورد لوحة تحكم الأدمن على الموقع
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

# مفتاح سري لجلسات فلاسك
SECRET_KEY = os.environ.get("SECRET_KEY", "please-change-this-secret-key")

# قاعدة البيانات
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///nursing_bot.db")

# اسم كلية/فرقة البوت (يظهر في الواجهة)
BOT_TITLE = os.environ.get("BOT_TITLE", "بوت الفرقة التالتة - تمريض")
