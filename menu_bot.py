import html
import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone

import telebot
from telebot import types
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("BOT_TOKEN topilmadi. .env faylini tekshiring.")

# .env ichida: ADMIN_IDS=123456789,987654321  (/myid buyrug'i bilan ID bilib olinadi)
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()
}

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

TZ = timezone(timedelta(hours=5))  # O'zbekiston vaqti
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "menu_data.json")
LOCK = threading.RLock()
REMIND_BEFORE_MIN = 15

DAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
DAYS_QQ = ["Dúyshembi", "Siyshembi", "Sárshembi", "Piyshembi", "Juma", "Shembi", "Ekshembi"]

# ---------- Doimiy ma'lumotlar ----------
CURATOR = {"name": "Avezova Ziyada", "phone": "+998 91 395 08 76", "tg": "Avezova_Ziyada"}
STAROSTA = {"name": "Abbaz Amaniyazov", "phone": "+998 95 887 04 98", "tg": "AbbazAmaniyazov"}
CREATOR = {"name": "Jumabaev Toqtarbay", "phone": "+998 88 021 10 26", "tg": "qwertyz1026"}


def person(title, p):
    return (
        f"{title}\n"
        f"👤 <b>{html.escape(p['name'])}</b>\n"
        f"📞 {p['phone']}\n"
        f"✈️ @{p['tg']}"
    )


CLASSMATES = [
    "Amandauletov Erbol Raxatovich",
    "Kuriyarov Pazilbek Sagindikovich",
    "Jumamuratov Arislanbek Oralbay uli",
    "Jumabayev Toqtarbay Ongarbayevich",
    "Amanjolov Erkebulan Amangeldi uli",
    "Xudaybergenov Tilewbergen Bayrambay uli",
    "Kojabaev Bayrambay Dauletbay uli",
    "Koblanbayev Nursultan Abay uli",
    "Seytbaev Esbergen Azat uli",
    "Babajanov Sardar Baxiyjan uli",
    "Maxsetbaev Nurlan Baxitbay uli",
    "Jumabayeva Gulmira Baxadir qizi",
    "Abilkasimov Jaqsiliq Karamatdin uli",
    "Bekniyazov Toreniyaz Salamatdin uli",
    "Begniyazova Miyasar Xojabay qizi",
    "Aytmuratov Tursinbek Anvarovich",
    "Jaumitbaev Jasur Baxadir uli",
    "Joldasbaev Aydos Saparbaevich",
    "Janabaev Hasilbek Omar uli",
    "Kosibaev Paluanatdin Kadirbay uli",
    "Otarbaev Alisher Ongarbay uli",
    "Sarsenbayev Sultanbek Kengesbay uli",
    "Jumamuratov Davletmurat Alimbay uli",
    "Uzaqbergenov Azizbek Quatbek uli",
    "Tileubaev Begis Tuelbaevich",
    "Seytbaev Sharapat Janabay uli",
    "Adenbaev Saydamin Abipnazar uli",
    "Kenesbaev Maxsud Nurlibay uli",
    "Kalbaev Karjaubay Nurlibay uli",
]


def default_mates():
    mates = [
        {"name": CURATOR["name"], "role": "Kurator", "tg": CURATOR["tg"], "phone": CURATOR["phone"]},
        {"name": STAROSTA["name"], "role": "Starosta", "tg": STAROSTA["tg"], "phone": STAROSTA["phone"]},
    ]
    mates += [{"name": n} for n in CLASSMATES if n != STAROSTA["name"]]
    return mates


MONTHS_QQ = [
    "", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
]

BIRTHDAYS = [
    {"name": "Miyasar", "day": 21, "month": 1, "year": 2001},
    {"name": "Qarjaw", "day": 24, "month": 1, "year": 2005},
    {"name": "Nursultan", "day": 25, "month": 2, "year": 2009},
    {"name": "Tilewbergen", "day": 26, "month": 3, "year": 2008},
    {"name": "Tawekel", "day": 2, "month": 4, "year": 2008},
    {"name": "Sunnetulla", "day": 9, "month": 4, "year": 2008},
    {"name": "Alisher", "day": 26, "month": 5, "year": 2008},
    {"name": "Sardar", "day": 27, "month": 5, "year": 2008},
    {"name": "Azizbek", "day": 7, "month": 6, "year": 2008},
    {"name": "Nurlan", "day": 21, "month": 7, "year": 2005},
    {"name": "Jaqsiliq", "day": 22, "month": 7, "year": 2008},
    {"name": "Tursinbek", "day": 31, "month": 7, "year": 2008},
    {"name": "Aydos", "day": 5, "month": 8, "year": 2008},
    {"name": "Saydamin", "day": 10, "month": 8, "year": 2008},
    {"name": "Sharapat", "day": 21, "month": 8, "year": 2008},
    {"name": "Erbol", "day": 26, "month": 8, "year": 2008},
    {"name": "Pazilbek", "day": 26, "month": 8, "year": 2007},
    {"name": "Gulmira", "day": 31, "month": 8, "year": 2008},
    {"name": "Dawletmurat", "day": 4, "month": 9, "year": 2008},
    {"name": "Maxsud", "day": 6, "month": 9, "year": 2008},
    {"name": "Erkebulan", "day": 1, "month": 10, "year": 2008},
    {"name": "Jasur", "day": 21, "month": 10, "year": 2008},
    {"name": "Toqtarbay", "day": 26, "month": 10, "year": 2001},
    {"name": "Esbergen", "day": 2, "month": 11, "year": 2005},
    {"name": "Hasilbek", "day": 6, "month": 11, "year": 2006},
    {"name": "Toreniyaz", "day": 8, "month": 11, "year": 2007},
    {"name": "Arislanbay", "day": 10, "month": 12, "year": 2008},
    {"name": "Sultanbek", "day": 16, "month": 12, "year": 2003},
    {"name": "Abbaz", "day": 22, "month": 12, "year": 1998},
]


# ---------- Saqlash ----------
def default_data():
    return {
        "group": "Katastr 1-a",
        "users": {},
        "subjects": [
            {
                "name": "🔬 Fizika",
                "lectures": [
                    {"title": "1-mavzu: Kinematika va dinamika", "type": "text",
                     "content": "Materiallar tez orada qo'shiladi."},
                    {"title": "2-mavzu: Molekulyar fizika", "type": "text",
                     "content": "Materiallar tez orada qo'shiladi."},
                ],
                "labs": [
                    {"title": "1-Lab: O'lchashlar va xatolar", "type": "text",
                     "content": "Materiallar tez orada qo'shiladi."},
                    {"title": "2-Lab: Qattiq jism zichligi", "type": "text",
                     "content": "Materiallar tez orada qo'shiladi."},
                ],
            },
            *[
                {"name": n, "lectures": [], "labs": []}
                for n in [
                    "🇬🇧 Chet (ingliz) tili",
                    "📐 Geodeziya 1-bo'lim",
                    "➗ Oliy matematika",
                    "🏛 O'zbekistonning eng yangi tarixi",
                    "📘 Qoraqalpoq tili",
                    "🇷🇺 Rus tili",
                ]
            ],
        ],
        "schedule_until": "2026-11-01",
        "schedule": {
            "0": [
                {
                    "time": "08:30",
                    "end": "09:50",
                    "name": "O'zbekistonning eng yangi tarixi",
                    "type": "Ma'ruza",
                    "teacher": "SARIBAYEVA N. B.",
                    "room": "",
                },
                {
                    "time": "11:30",
                    "end": "12:50",
                    "name": "Fizika",
                    "type": "Ma'ruza",
                    "teacher": "SAPARNIYAZOVA G. K.",
                    "room": "",
                },
            ],
            "1": [
                {
                    "time": "08:30",
                    "end": "09:50",
                    "name": "Geodeziya 1 bo'lim",
                    "type": "Ma'ruza",
                    "teacher": "KALIMBETOV J. B.",
                    "room": "308 3-korpus",
                },
                {
                    "time": "10:00",
                    "end": "11:20",
                    "name": "Chet (inglis) tili",
                    "type": "Amaliy",
                    "teacher": "ABDULLAEV M. A.",
                    "room": "308 3-korpus",
                },
                {
                    "time": "11:30",
                    "end": "12:50",
                    "name": "Geodeziya 1 bo'lim",
                    "type": "Amaliy",
                    "teacher": "KALIMBETOV J. B.",
                    "room": "308 3-korpus",
                },
            ],
            "2": [
                {
                    "time": "08:30",
                    "end": "09:50",
                    "name": "O'zbekistonning eng yangi tarixi",
                    "type": "Seminar",
                    "teacher": "SARIBAYEVA N. B.",
                    "room": "",
                },
                {
                    "time": "10:00",
                    "end": "11:20",
                    "name": "Oliy matematika",
                    "type": "Amaliy",
                    "teacher": "BEKIYEV A. B.",
                    "room": "308 3-korpus",
                },
                {
                    "time": "11:30",
                    "end": "12:50",
                    "name": "Qoraqalpoq tili",
                    "type": "Amaliy",
                    "teacher": "KUNNAZAROVA SH. M.",
                    "room": "",
                },
            ],
            "3": [
                {
                    "time": "08:30",
                    "end": "09:50",
                    "name": "Chet (inglis) tili",
                    "type": "Amaliy",
                    "teacher": "ABDULLAEV M. A.",
                    "room": "308 3-korpus",
                },
                {
                    "time": "10:00",
                    "end": "11:20",
                    "name": "Fizika",
                    "type": "Laboratoriya",
                    "teacher": "SAPARNIYAZOVA G. K.",
                    "room": "",
                },
                {
                    "time": "11:30",
                    "end": "12:50",
                    "name": "Oliy matematika",
                    "type": "Amaliy",
                    "teacher": "BEKIYEV A. B.",
                    "room": "308 3-korpus",
                },
            ],
            "4": [
                {
                    "time": "08:30",
                    "end": "09:50",
                    "name": "Oliy matematika",
                    "type": "Ma'ruza",
                    "teacher": "BEGLERBEKOV R. J.",
                    "room": "",
                },
                {
                    "time": "10:00",
                    "end": "11:20",
                    "name": "Chet (inglis) tili",
                    "type": "Amaliy",
                    "teacher": "ABDULLAEV M. A.",
                    "room": "308 3-korpus",
                },
                {
                    "time": "11:30",
                    "end": "12:50",
                    "name": "Geodeziya 1 bo'lim",
                    "type": "Ma'ruza",
                    "teacher": "KALIMBETOV J. B.",
                    "room": "308 3-korpus",
                },
            ],
            "5": [],
            "6": [],
        },
        "announcements": [
            {
                "date": "2026-10-17",
                "text": (
                    "🎉 <b>Jańalıq! Katastr 1-A Hub botı tolıq Qaraqalpaq tiline ótkerildi!</b> ✨\n\n"
                    "Endi botımızdıń barlıq bólimleri, Mini Qollanbası hám awdarmashısı "
                    "<b>Qaraqalpaq tilinde</b> isleydi!\n\n"
                    "📌 <b>Jańa múmkinshilikler:</b>\n"
                    "• 📚 <b>Pánler (Sabaqlar):</b> Barlıq 7 pánnen lekciya, ámeliy hám laboratoriya PDF materialları\n"
                    "• 📅 <b>Sabaq kestesi:</b> Búgingi (/bugin), erteńgi (/erten) hám háptelik (/keste) sabaqlar\n"
                    "• 🌐 <b>Awdarmashı:</b> Qaraqalpaqsha, Ózbekshe, Inglisshe hám Orıssha tez awdarma\n"
                    "• 👥 <b>Gruppa yordamshısı:</b> Hár kúni azanda 07:30 da sabaq kestesi hám 15 minut aldın esletpe!\n\n"
                    "🔄 Jańalanıwdı kóriw ushın 👉 /start basıń!"
                ),
            }
        ],
        "exams": [],
        "mates": default_mates(),
        "birthdays": BIRTHDAYS,
        "groups": {},
    }


SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or ""
CLOUD = bool(SUPABASE_URL and SUPABASE_KEY)
CLOUD_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}
CLOUD_ENDPOINT = f"{SUPABASE_URL}/rest/v1/bot_data"


def cloud_load():
    import requests

    r = requests.get(
        CLOUD_ENDPOINT, headers=CLOUD_HEADERS,
        params={"id": "eq.1", "select": "data"}, timeout=15,
    )
    r.raise_for_status()
    rows = r.json()
    return rows[0]["data"] if rows else None


def cloud_save(snapshot):
    import requests

    r = requests.post(
        CLOUD_ENDPOINT,
        headers={**CLOUD_HEADERS, "Prefer": "resolution=merge-duplicates"},
        params={"on_conflict": "id"},
        data=json.dumps({"id": 1, "data": snapshot}, ensure_ascii=False).encode("utf-8"),
        timeout=15,
    )
    r.raise_for_status()


def _upgrade_data(data):
    """Agar bazada eski namuna jadval qolib ketgan bo'lsa, yangisiga almashtiradi."""
    d = default_data()
    if data.get("schedule_until") != d.get("schedule_until"):
        data["schedule"] = d["schedule"]
        data["schedule_until"] = d["schedule_until"]
    if not data.get("announcements"):
        data["announcements"] = d["announcements"]
    if not data.get("birthdays"):
        data["birthdays"] = BIRTHDAYS
    data.setdefault("groups", {})
    return data


def load_data():
    if CLOUD:
        try:
            data = cloud_load()
            if data:
                print("Ma'lumotlar Supabase'dan yuklandi.")
                return _upgrade_data(data)
        except Exception as e:
            print("Supabase'dan o'qib bo'lmadi:", e)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                return _upgrade_data(json.load(f))
        except Exception:
            pass
    return default_data()


DATA = load_data()
_dirty = threading.Event()


def save():
    with LOCK:
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(DATA, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
    if CLOUD:
        _dirty.set()


def cloud_sync_loop():
    """O'zgarishlarni fonda Supabase'ga yozadi (bot kutib qolmasligi uchun)."""
    while True:
        _dirty.wait()
        time.sleep(2)  # ketma-ket o'zgarishlarni bitta yozuvga birlashtiradi
        _dirty.clear()
        try:
            with LOCK:
                snapshot = json.loads(json.dumps(DATA))
            cloud_save(snapshot)
        except Exception as e:
            print("Supabase'ga yozib bo'lmadi:", e)
            _dirty.set()
            time.sleep(10)


def is_admin(uid):
    return uid in ADMIN_IDS


def register_user(user):
    with LOCK:
        uid = str(user.id)
        name = " ".join(x for x in [user.first_name, user.last_name] if x)
        uname = user.username or ""
        u = DATA["users"].get(uid)
        if not u:
            u = {
                "joined": datetime.now(TZ).strftime("%Y-%m-%d"),
                "translations": 0,
                "remind": True,
                "name": name,
                "username": uname,
            }
            DATA["users"][uid] = u
            save()
        elif u.get("name") != name or u.get("username") != uname:
            u["name"] = name
            u["username"] = uname
            save()
        return u


def register_group(chat):
    if chat.type not in ("group", "supergroup"):
        return
    with LOCK:
        gid = str(chat.id)
        groups = DATA.setdefault("groups", {})
        title = chat.title or "Guruh"
        g = groups.get(gid)
        if not g:
            groups[gid] = {
                "title": title,
                "added": datetime.now(TZ).strftime("%Y-%m-%d"),
                "remind": True,
            }
            save()
        elif g.get("title") != title:
            g["title"] = title
            save()


user_direction = {}  # chat_id -> (src, dest)

DIRECTIONS = {
    "tr_uz_en": ("uz", "en", "🇺🇿 Qaraqalpaqsha / Ózbekshe → 🇬🇧 Inglisshe"),
    "tr_en_uz": ("en", "uz", "🇬🇧 Inglisshe → 🇺🇿 Qaraqalpaqsha / Ózbekshe"),
    "tr_ru_uz": ("ru", "uz", "🇷🇺 Orıssha → 🇺🇿 Qaraqalpaqsha / Ózbekshe"),
    "tr_uz_ru": ("uz", "ru", "🇺🇿 Qaraqalpaqsha / Ózbekshe → 🇷🇺 Orıssha"),
}


# ---------- Yordamchi UI ----------
def btn(text, data):
    return types.InlineKeyboardButton(text, callback_data=data)


def kb(*buttons, width=1):
    m = types.InlineKeyboardMarkup(row_width=width)
    m.add(*buttons)
    return m


BOT_NAME = "Katastr 1-A Hub"
BANNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "banner.jpg")
LINE = "━━━━━━━━━━━━━━━━━━"


def header(icon, title):
    return f"{icon} <b>{title}</b>\n{LINE}\n"


WEBAPP_URL = (os.getenv("WEBAPP_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
WEBAPP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webapp", "index.html")


def main_menu(uid=None, chat_type="private"):
    m = types.InlineKeyboardMarkup(row_width=2)
    if chat_type == "private" and WEBAPP_URL.startswith("https://"):
        m.add(
            types.InlineKeyboardButton(
                "📱 Mini Qollanbanı ashıw", web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/app")
            )
        )
    b = [
        btn("📚 Pánler (Sabaqlar)", "menu_subjects"),
        btn("📅 Sabaq kestesi", "menu_schedule"),
        btn("🌐 Awdarmashı", "menu_translation"),
        btn("📝 Imtixanlar", "menu_exams"),
        btn("📢 Daǵazalar", "menu_ann"),
        btn("👥 Gruppalaslar", "menu_mates"),
        btn("🎂 Tuwılǵan kúnler", "menu_birthdays"),
        btn("👤 Profilim", "menu_profile"),
        btn("ℹ️ Maǵlıwmat", "menu_info"),
    ]
    if chat_type == "private" and uid is not None and is_admin(uid):
        b.append(btn("🛠 Admin panel", "adm"))
    m.add(*b)
    return m


def show(call, text, markup=None):
    try:
        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id, reply_markup=markup
        )
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e):
            raise


def creator_footer():
    return "\n\n💻 Jaratıwshı: <b>{}</b> (@{})".format(CREATOR["name"], CREATOR["tg"])


def info_text():
    return (
        header("ℹ️", BOT_NAME)
        + "Kurslaslar ushın oqıw materialları, sabaq kestesi hám paydalı maǵlıwmatlar botı.\n\n"
        f"🎓 Gruppa: <b>{html.escape(DATA['group'])}</b>\n\n"
        + person("👩‍🏫 <b>Kurator</b>", CURATOR) + "\n\n"
        + person("⭐ <b>Starosta</b>", STAROSTA) + "\n\n"
        + person("💻 <b>Bot jaratıwshısı</b>", CREATOR)
    )


def group_welcome_text():
    return (
        f"🎓 <b>Assalawma aleykum, {html.escape(DATA['group'])} gruppası!</b> 👋\n"
        f"Men gruppanıń rásmiy yordamshı botıman (<b>{BOT_NAME}</b>).\n\n"
        "📌 <b>Gruppada ne qıla alaman?</b>\n"
        "• ☀️ Hár kúni azanda <b>07:30</b> da búgingi sabaq kestesin jiberemen\n"
        "• ⏰ Hár para baslanıwınan <b>15 minut aldın</b> esletemen\n"
        "• 📅 <i>«búgin ne sabaq?»</i>, <i>«erteń ne sabaq?»</i>, <i>«keste»</i> deseńiz — sabaq kestesin shıǵaraman\n"
        "• 📚 <i>«fizika pdf»</i>, <i>«matematika»</i>, <i>«geodeziya»</i>, <i>«tariyx»</i>, "
        "<i>«qaraqalpaq tili»</i>, <i>«ingliz tili»</i>, <i>«rus tili»</i> deseńiz — lekciya hám ámeliy PDF fayllardı beremen\n"
        "• 👩‍🏫 <i>«kurator nomeri»</i>, <i>«starosta nomeri»</i>, <i>«gruppa dizimi»</i> deseńiz — maǵlıwmat shıǵaraman\n"
        "• 🎂 <i>«tuwılǵan kúnler»</i> deseńiz — gruppalaslardıń tuwılǵan kúnlerin shıǵaraman\n"
        "• 🌐 Xabarǵa <i>Reply</i> qılıp <code>/tr</code> jazsańız — awdarma (tarjima) qılaman!"
        + creator_footer()
    )


@bot.message_handler(content_types=["new_chat_members"])
def on_new_chat_members(message):
    register_group(message.chat)
    try:
        me = bot.get_me()
        for member in message.new_chat_members or []:
            if member.id == me.id:
                bot.send_message(
                    message.chat.id,
                    group_welcome_text(),
                    reply_markup=main_menu(message.from_user.id, message.chat.type),
                )
                break
    except Exception:
        pass


# ---------- /start, /help, /myid ----------
@bot.message_handler(commands=["start"])
def send_welcome(message):
    register_group(message.chat)
    u = register_user(message.from_user)
    user_direction.pop(message.chat.id, None)
    if u.get("tr"):
        u.pop("tr", None)
        save()
    if message.chat.type in ("group", "supergroup"):
        bot.send_message(
            message.chat.id,
            group_welcome_text(),
            reply_markup=main_menu(message.from_user.id, message.chat.type),
        )
        return
    if os.path.exists(BANNER):
        try:
            with open(BANNER, "rb") as f:
                bot.send_photo(
                    message.chat.id, f,
                    caption=f"🎓 <b>{BOT_NAME}</b>\n{html.escape(DATA['group'])} gruppası ushın",
                )
        except Exception:
            pass
    bot.send_message(
        message.chat.id,
        f"Assalawma aleykum, <b>{html.escape(message.from_user.first_name or 'dos')}</b>! 👋\n"
        f"<b>{BOT_NAME}</b> — <b>{html.escape(DATA['group'])}</b> gruppasınıń jeke yordamshı botı."
        + creator_footer()
        + f"\n{LINE}\nKerekli bólimdi tańlań 👇",
        reply_markup=main_menu(message.from_user.id, message.chat.type),
    )


@bot.message_handler(commands=["help"])
def help_cmd(message):
    register_group(message.chat)
    bot.send_message(
        message.chat.id,
        "/start - bas menyu\n"
        "/bugin (/today) - búgingi sabaqlar\n"
        "/erten (/ertaga) - erteńgi sabaqlar\n"
        "/keste (/week) - háptelik sabaq kestesi\n"
        "/fanlar (/sabaqlar) - PDF hám lekciyalar\n"
        "/tuwilgankun (/bday) - tuwılǵan kúnler\n"
        "/tr - awdarma (tarjima)\n"
        "/profile - profilim\n"
        "/myid - Telegram ID",
    )


@bot.message_handler(commands=["myid"])
def myid(message):
    register_group(message.chat)
    bot.reply_to(message, f"Siziń ID: <code>{message.from_user.id}</code>")


@bot.message_handler(commands=["today", "bugin"])
def today_cmd(message):
    register_group(message.chat)
    bot.send_message(message.chat.id, today_text())


@bot.message_handler(commands=["ertaga", "erten"])
def tomorrow_cmd(message):
    register_group(message.chat)
    bot.send_message(message.chat.id, tomorrow_text())


@bot.message_handler(commands=["week", "hapte", "keste"])
def week_cmd(message):
    register_group(message.chat)
    bot.send_message(message.chat.id, week_text())


@bot.message_handler(commands=["fanlar", "sabaqlar", "pdf"])
def subjects_cmd(message):
    register_group(message.chat)
    bot.send_message(
        message.chat.id,
        header("📚", "Pánler / Sabaqlar") + "Pándi tańlań (PDF hám lekciyalar):",
        reply_markup=kb(
            *[btn(s["name"], f"s:{i}") for i, s in enumerate(DATA["subjects"])],
            btn("🏠 Bas menyu", "back_to_main"),
        ),
    )


@bot.message_handler(commands=["profile"])
def profile_cmd(message):
    register_group(message.chat)
    register_user(message.from_user)
    t, m = profile_view(message.from_user.id)
    bot.send_message(message.chat.id, t, reply_markup=m)


@bot.message_handler(commands=["tuwilgankun", "bday", "tugilgankun"])
def bday_cmd(message):
    register_group(message.chat)
    bot.send_message(
        message.chat.id,
        birthdays_text(),
        reply_markup=kb(btn("🏠 Bas menyu", "back_to_main")),
    )


@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    register_group(message.chat)
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Siz admin emessiz.")
        return
    bot.send_message(message.chat.id, "🛠 Admin panel:", reply_markup=admin_menu())


# ---------- Jadval ----------
def is_schedule_expired():
    until = DATA.get("schedule_until")
    if not until:
        return False
    try:
        exp_date = datetime.strptime(until, "%Y-%m-%d").date()
        return datetime.now(TZ).date() > exp_date
    except Exception:
        return False


def active_schedule():
    if is_schedule_expired():
        return {str(i): [] for i in range(7)}
    return DATA.get("schedule", {})


def fmt_lesson(x):
    t = f"{x['time']} - {x['end']}" if x.get("end") else x["time"]
    tp = f" ({html.escape(x['type'])})" if x.get("type") else ""
    line = f"🕒 <b>{html.escape(t)}</b> — <b>{html.escape(x['name'])}</b>{tp}"
    details = []
    if x.get("teacher"):
        details.append(f"👩‍🏫 {html.escape(x['teacher'])}")
    if x.get("room"):
        details.append(f"🚪 {html.escape(x['room'])}")
    if details:
        line += "\n     " + " • ".join(details)
    return line


def fmt_day(i):
    if is_schedule_expired():
        return "⏳ <i>Bul hápte ushın maǵlıwmat ele kiritilmegen.</i>"
    items = sorted(active_schedule().get(str(i), []), key=lambda x: x["time"])
    if not items:
        return "— sabaq joq"
    return "\n".join(fmt_lesson(x) for x in items)


def week_text():
    if is_schedule_expired():
        return (
            header("📅", "Háptelik sabaq kestesi")
            + "⏳ <i>Bul hápte ushın sabaq kestesi ele kiritilmegen (Maǵlıwmat ele kiritilmegen).</i>"
        )
    sch = active_schedule()
    days = [
        f"<b>{DAYS_QQ[i]}</b>\n{fmt_day(i)}"
        for i in range(7)
        if sch.get(str(i))
    ]
    if not days:
        return (
            header("📅", "Háptelik sabaq kestesi")
            + "⏳ <i>Bul hápte ushın sabaq kestesi ele kiritilmegen (Maǵlıwmat ele kiritilmegen).</i>"
        )
    return header("📅", "Háptelik sabaq kestesi") + "\n\n".join(days)


def day_schedule_text(i, prefix="📅"):
    return header(prefix, f"{DAYS_QQ[i]} — Sabaq kestesi") + fmt_day(i)


def today_text():
    i = datetime.now(TZ).weekday()
    return header("🕒", f"Búgingi sabaqlar — {DAYS_QQ[i]}") + fmt_day(i)


def tomorrow_text():
    i = (datetime.now(TZ).weekday() + 1) % 7
    return header("📅", f"Erteńgi sabaqlar — {DAYS_QQ[i]}") + fmt_day(i)


# ---------- Tuwılǵan kúnler ----------
def _bday_days_left(b, today=None):
    if today is None:
        today = datetime.now(TZ).date()
    m, d = int(b["month"]), int(b["day"])
    try:
        nxt = datetime(today.year, m, d).date()
    except ValueError:
        nxt = datetime(today.year, m, 28).date()
    if nxt < today:
        try:
            nxt = datetime(today.year + 1, m, d).date()
        except ValueError:
            nxt = datetime(today.year + 1, m, 28).date()
    left = (nxt - today).days
    age = nxt.year - int(b["year"])
    return left, age


def birthdays_text():
    today = datetime.now(TZ).date()
    bdays = DATA.get("birthdays") or BIRTHDAYS
    enriched = []
    for b in bdays:
        left, age = _bday_days_left(b, today)
        enriched.append((left, age, b))
    enriched.sort(key=lambda x: (x[0], x[2]["name"]))

    out = [header("🎂", f"Tuwılǵan kúnler — {html.escape(DATA['group'])}")]

    today_list = [x for x in enriched if x[0] == 0]
    if today_list:
        out.append("🎉 <b>BÚGIN TUWÍLǴAN KÚNI:</b>")
        for _, age, b in today_list:
            mname = MONTHS_QQ[b["month"]].lower()
            out.append(f"🥳 <b>{html.escape(b['name'])}</b> — {b['day']}-{mname} {b['year']} ({age} jas!) 🎂")
        out.append("")

    upcoming = [x for x in enriched if x[0] > 0][:3]
    if upcoming:
        out.append("⏳ <b>Eń jaqın tuwılǵan kúnler:</b>")
        for left, age, b in upcoming:
            mname = MONTHS_QQ[b["month"]].lower()
            when = "erteń! 🔥" if left == 1 else f"{left} kún qaldı"
            out.append(
                f"• <b>{html.escape(b['name'])}</b> — {b['day']}-{mname} ({age} jas, ⏳ {when})"
            )
        out.append(LINE)

    for m_idx in range(1, 13):
        m_items = [b for b in bdays if int(b["month"]) == m_idx]
        if not m_items:
            continue
        m_items.sort(key=lambda x: int(x["day"]))
        out.append(f"📅 <b>{m_idx}. {MONTHS_QQ[m_idx]}</b>")
        m_lower = MONTHS_QQ[m_idx].lower()
        for b in m_items:
            out.append(f"  • <b>{html.escape(b['name'])}</b> — {b['day']}-{m_lower} {b['year']}")
    return "\n".join(out)


# ---------- Profil ----------
def profile_view(uid):
    u = DATA["users"].get(str(uid), {})
    text = (
        header("👤", "Profilim")
        + f"🙍 Atı-jóni: {html.escape(u.get('name', '-'))}\n"
        f"🔗 Username: @{u.get('username') or '-'}\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"📆 Qosılǵan sáne: {u.get('joined', '-')}\n"
        f"🌐 Awdarmalar sanı: {u.get('translations', 0)}\n"
        f"⏰ Sabaq esletpesi: {'🔔 qosılǵan' if u.get('remind', True) else '🔕 óshirilgen'}"
    )
    m = kb(
        btn("🔕 Esletpeni óshiriw" if u.get("remind", True) else "🔔 Esletpeni qosıw", "toggle_remind"),
        btn("⬅️ Artqa", "back_to_main"),
    )
    return text, m


def second_section(subj_name):
    if "fizika" in subj_name.lower():
        return "🧪", "Laboratoriya"
    return "📝", "Ámeliy shınıǵıwlar"


# ---------- Admin ----------
def admin_menu():
    return kb(
        btn("➕ Ma'ruza qo'shish (PDF/matn)", "adm_add:lectures"),
        btn("➕ Amaliy / Lab qo'shish (PDF/matn)", "adm_add:labs"),
        btn("📚 Yangi fan qo'shish", "adm_subject"),
        btn("📅 Kun jadvalini o'zgartirish", "adm_sched"),
        btn("📢 E'lon yuborish", "adm_ann"),
        btn("📝 Imtihon qo'shish", "adm_exam"),
        btn("🗑 Imtihonlarni tozalash", "adm_clear:exams"),
        btn("🗑 E'lonlarni tozalash", "adm_clear:ann"),
        btn("👥 Guruhdosh qo'shish", "adm_mate"),
        btn("🎓 Guruh nomini o'zgartirish", "adm_group"),
        btn("🔄 Bazadan yangilash", "adm_reload"),
        btn("📊 Statistika", "adm_stats"),
        btn("⬅️ Orqaga", "back_to_main"),
    )


def ask(chat_id, text, handler, *args):
    msg = bot.send_message(chat_id, text + "\n\n(bekor qilish: /cancel)")
    bot.register_next_step_handler(msg, handler, *args)


def cancelled(message):
    if message.content_type == "text" and message.text.strip().startswith("/"):
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=admin_menu())
        return True
    return False


def step_group(message):
    if cancelled(message):
        return
    DATA["group"] = message.text.strip()
    save()
    bot.send_message(message.chat.id, "✅ Guruh nomi saqlandi.", reply_markup=admin_menu())


def step_subject(message):
    if cancelled(message):
        return
    DATA["subjects"].append({"name": message.text.strip(), "lectures": [], "labs": []})
    save()
    bot.send_message(message.chat.id, "✅ Fan qo'shildi.", reply_markup=admin_menu())


def step_item_title(message, si, kind):
    if cancelled(message):
        return
    ask(message.chat.id, "Endi matn yoki fayl (PDF/hujjat/rasm) yuboring:",
        step_item_content, si, kind, message.text.strip())


def step_item_content(message, si, kind, title):
    if message.content_type == "text" and message.text.startswith("/"):
        cancelled(message)
        return
    if message.content_type == "text":
        item = {"title": title, "type": "text", "content": message.text}
    elif message.content_type == "document":
        item = {"title": title, "type": "document", "content": message.document.file_id}
    elif message.content_type == "photo":
        item = {"title": title, "type": "photo", "content": message.photo[-1].file_id}
    else:
        ask(message.chat.id, "Faqat matn, hujjat yoki rasm yuboring.",
            step_item_content, si, kind, title)
        return
    DATA["subjects"][si][kind].append(item)
    save()
    bot.send_message(message.chat.id, "✅ Qo'shildi.", reply_markup=admin_menu())


def step_sched(message, day):
    if cancelled(message):
        return
    items = []
    for line in message.text.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            try:
                datetime.strptime(parts[0], "%H:%M")
                items.append({"time": parts[0], "name": parts[1]})
            except ValueError:
                pass
    if not items:
        ask(message.chat.id, "Format noto'g'ri. Misol:\n09:00 Fizika\n10:30 Matematika",
            step_sched, day)
        return
    if is_schedule_expired():
        DATA["schedule"] = {str(i): [] for i in range(7)}
    DATA["schedule"][str(day)] = items
    today_d = datetime.now(TZ).date()
    days_ahead = (6 - today_d.weekday()) if today_d.weekday() < 6 else 7
    DATA["schedule_until"] = (today_d + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    save()
    bot.send_message(
        message.chat.id,
        f"✅ {DAYS_QQ[day]} kestesi jańalandı (ámelde: {DATA['schedule_until']} shekem).",
        reply_markup=admin_menu(),
    )


def step_ann(message):
    if cancelled(message):
        return
    text = html.escape(message.text)
    DATA["announcements"].append(
        {"date": datetime.now(TZ).strftime("%Y-%m-%d"), "text": text}
    )
    save()
    sent = 0
    for uid in list(DATA["users"]):
        try:
            bot.send_message(int(uid), f"📢 <b>E'lon / Daǵaza</b>\n\n{text}")
            sent += 1
        except Exception:
            pass
    gsent = 0
    for gid in list(DATA.get("groups", {})):
        try:
            bot.send_message(int(gid), f"📢 <b>Gruppa ushın daǵaza (E'lon):</b>\n{LINE}\n{text}")
            gsent += 1
        except Exception:
            pass
    bot.send_message(
        message.chat.id,
        f"✅ {sent} ta foydalanuvchi va {gsent} ta guruhga yuborildi.",
        reply_markup=admin_menu(),
    )


def step_exam(message):
    if cancelled(message):
        return
    parts = message.text.strip().split(maxsplit=1)
    try:
        datetime.strptime(parts[0], "%Y-%m-%d")
        name = parts[1]
    except (ValueError, IndexError):
        ask(message.chat.id, "Format: YYYY-MM-DD Fan nomi\nMasalan: 2026-12-20 Fizika", step_exam)
        return
    DATA["exams"].append({"date": parts[0], "name": name})
    save()
    bot.send_message(message.chat.id, "✅ Imtihon qo'shildi.", reply_markup=admin_menu())


def step_mate(message):
    if cancelled(message):
        return
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts) < 2:
        ask(message.chat.id, "Format: Ism Familiya, @nik, telefon(ixtiyoriy)", step_mate)
        return
    DATA["mates"].append(
        {"name": parts[0], "tg": parts[1].lstrip("@"), "phone": parts[2] if len(parts) > 2 else ""}
    )
    save()
    bot.send_message(message.chat.id, "✅ Guruhdosh qo'shildi.", reply_markup=admin_menu())


def handle_admin(call):
    data = call.data
    chat_id = call.message.chat.id
    if data == "adm":
        show(call, "🛠 Admin panel:", admin_menu())
    elif data.startswith("adm_add:"):
        kind = data.split(":")[1]
        m = kb(*[btn(s["name"], f"adm_sub:{kind}:{i}") for i, s in enumerate(DATA["subjects"])],
               btn("⬅️ Orqaga", "adm"))
        show(call, "Qaysi fanga?", m)
    elif data.startswith("adm_sub:"):
        _, kind, si = data.split(":")
        ask(chat_id, "Sarlavhani yuboring (masalan: 3-mavzu: Termodinamika):",
            step_item_title, int(si), kind)
    elif data == "adm_subject":
        ask(chat_id, "Yangi fan nomini yuboring (emoji bilan ham bo'ladi):", step_subject)
    elif data == "adm_sched":
        show(call, "Qaysi kun?", kb(
            *[btn(d, f"adm_day:{i}") for i, d in enumerate(DAYS)], btn("⬅️ Orqaga", "adm"), width=2))
    elif data.startswith("adm_day:"):
        day = int(data.split(":")[1])
        ask(chat_id, f"{DAYS[day]} jadvalini yuboring, har qatorda bitta dars:\n"
                     "09:00 Fizika\n10:30 Matematika", step_sched, day)
    elif data == "adm_ann":
        ask(chat_id, "E'lon matnini yuboring (hammaga jo'natiladi):", step_ann)
    elif data == "adm_exam":
        ask(chat_id, "Format: YYYY-MM-DD Fan nomi\nMasalan: 2026-12-20 Fizika", step_exam)
    elif data == "adm_clear:exams":
        DATA["exams"] = []
        save()
        bot.send_message(chat_id, "🗑 Imtihonlar tozalandi.")
    elif data == "adm_clear:ann":
        DATA["announcements"] = []
        save()
        bot.send_message(chat_id, "🗑 E'lonlar tozalandi.")
    elif data == "adm_mate":
        ask(chat_id, "Format: Ism Familiya, @nik, telefon(ixtiyoriy)", step_mate)
    elif data == "adm_group":
        ask(chat_id, "Guruh nomi/raqamini yuboring:", step_group)
    elif data == "adm_reload":
        with LOCK:
            fresh = load_data()
            DATA.clear()
            DATA.update(fresh)
        bot.send_message(chat_id, "✅ Ma'lumotlar bazadan yangilandi.", reply_markup=admin_menu())
    elif data == "adm_stats":
        users = DATA["users"].values()
        groups = DATA.get("groups", {})
        tr = sum(u.get("translations", 0) for u in users)
        bot.send_message(
            chat_id,
            f"📊 Foydalanuvchilar: {len(users)}\n"
            f"👥 Ulangan guruhlar: {len(groups)}\n"
            f"🌐 Tarjimalar: {tr}",
        )


# ---------- Tugmalar ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)
    register_group(call.message.chat)
    chat_id = call.message.chat.id
    chat_type = call.message.chat.type
    uid = call.from_user.id
    data = call.data

    if data.startswith("adm"):
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "⛔ Faqat admin uchun", show_alert=True)
            return
        handle_admin(call)

    elif data == "back_to_main":
        user_direction.pop(chat_id, None)
        u = register_user(call.from_user)
        if u.get("tr"):
            u.pop("tr", None)
            save()
        show(call, header("🏠", "Bas menyu") + f"🎓 {html.escape(DATA['group'])}\nBólimdi tańlań 👇",
             main_menu(uid, chat_type))

    elif data == "menu_translation":
        user_direction.pop(chat_id, None)
        show(call, header("🌐", "Awdarmashı") + "Awdarma baǵdarın tańlań:", kb(
            *[btn(v[2], k) for k, v in DIRECTIONS.items()], btn("⬅️ Artqa", "back_to_main")))

    elif data in DIRECTIONS:
        src, dest, label = DIRECTIONS[data]
        user_direction[chat_id] = (src, dest)
        u = register_user(call.from_user)
        u["tr"] = [src, dest]
        save()
        show(call, header("🌐", "Awdarmashı") + f"✅ Baǵdar: <b>{label}</b>\n\n"
             "✍️ Endi awdarma qılınatuǵın tekstti jiberiń.",
             kb(btn("⬅️ Artqa", "menu_translation")))

    elif data == "menu_subjects":
        show(call, header("📚", "Pánler (Sabaqlar)") + "Pándi tańlań:", kb(
            *[btn(s["name"], f"s:{i}") for i, s in enumerate(DATA["subjects"])],
            btn("⬅️ Artqa", "back_to_main")))

    elif data.startswith("s:"):
        i = int(data[2:])
        s = DATA["subjects"][i]
        if s.get("single"):
            items = s.get("lectures") or []
            body = "Materialdı tańlań (ústine bassańız fayl ashıladı):" if items else "Ele qosılmaǵan."
            show(call, header("📚", html.escape(s["name"])) + body, kb(
                *[btn(it["title"], f"it:{i}:l:{j}") for j, it in enumerate(items)],
                btn("⬅️ Pánlerge qaytıw", "menu_subjects")))
        else:
            sec_icon, sec_name = second_section(s["name"])
            show(call, header("📚", html.escape(s["name"])) + "Bólimdi tańlań:", kb(
                btn(f"📖 Lekciyalar ({len(s['lectures'])})", f"sl:{i}"),
                btn(f"{sec_icon} {sec_name} ({len(s['labs'])})", f"sb:{i}"),
                btn("⬅️ Pánlerge qaytıw", "menu_subjects")))

    elif data.startswith(("sl:", "sb:")):
        i = int(data[3:])
        kind = "lectures" if data.startswith("sl:") else "labs"
        s = DATA["subjects"][i]
        icon, name = ("📖", "Lekciyalar") if kind == "lectures" else second_section(s["name"])
        body = "Temanı tańlań (ústine bassańız fayl jiberiledi):" if s[kind] else "Ele qosılmaǵan."
        show(call, header(icon, f"{html.escape(s['name'])} — {name}") + body, kb(
            *[btn(it["title"], f"it:{i}:{kind[0]}:{j}") for j, it in enumerate(s[kind])],
            btn("⬅️ Artqa", f"s:{i}")))

    elif data.startswith("it:"):
        _, i, k, j = data.split(":")
        item = DATA["subjects"][int(i)]["lectures" if k == "l" else "labs"][int(j)]
        cap = f"<b>{html.escape(item['title'])}</b>"
        if item["type"] == "text":
            bot.send_message(chat_id, f"{cap}\n{LINE}\n{html.escape(item['content'])}")
        elif item["type"] == "document":
            bot.send_document(chat_id, item["content"], caption=cap)
        else:
            bot.send_photo(chat_id, item["content"], caption=cap)

    elif data == "menu_schedule":
        show(call, header("📅", "Sabaq kestesi") + "Tańlań:", kb(
            btn("📅 Háptelik", "sch_week"), btn("🕒 Búgin", "sch_today"),
            btn("📆 Erteń", "sch_tomorrow"),
            btn("⬅️ Artqa", "back_to_main"), width=2))

    elif data == "sch_week":
        show(call, week_text(), kb(btn("⬅️ Artqa", "menu_schedule")))

    elif data == "sch_today":
        show(call, today_text(), kb(btn("⬅️ Artqa", "menu_schedule")))

    elif data == "sch_tomorrow":
        show(call, tomorrow_text(), kb(btn("⬅️ Artqa", "menu_schedule")))

    elif data == "menu_ann":
        anns = DATA["announcements"][-5:][::-1]
        body = "\n\n".join(f"🗓 <i>{a['date']}</i>\n{a['text']}" for a in anns) if anns else "Daǵazalar joq."
        show(call, header("📢", "Sońǵı daǵazalar") + body, kb(btn("⬅️ Artqa", "back_to_main")))

    elif data == "menu_exams":
        today = datetime.now(TZ).date()
        lines = []
        for e in sorted(DATA["exams"], key=lambda x: x["date"]):
            d = datetime.strptime(e["date"], "%Y-%m-%d").date()
            left = (d - today).days
            if left >= 0:
                lines.append(f"📝 <b>{html.escape(e['name'])}</b>\n     🗓 {e['date']} — ⏳ {left} kún qaldı")
        body = "\n\n".join(lines) if lines else "Rejelestirilgen imtixan joq."
        show(call, header("📝", "Imtixanlar") + body, kb(btn("⬅️ Artqa", "back_to_main")))

    elif data == "menu_mates":
        lines = []
        n = 0
        for m in DATA["mates"]:
            if m.get("role"):
                line = f"⭐ <b>{m['role']}:</b> {html.escape(m['name'])}"
            else:
                n += 1
                line = f"{n}. {html.escape(m['name'])}"
            if m.get("tg"):
                line += f" — @{m['tg']}"
            if m.get("phone"):
                line += f" — {m['phone']}"
            lines.append(line)
        show(call, header("👥", f"Gruppalaslar — {html.escape(DATA['group'])}") + "\n".join(lines),
             kb(btn("🎂 Tuwılǵan kúnler", "menu_birthdays"), btn("⬅️ Artqa", "back_to_main")))

    elif data == "menu_birthdays":
        show(call, birthdays_text(),
             kb(btn("👥 Gruppalaslar", "menu_mates"), btn("⬅️ Artqa", "back_to_main")))

    elif data == "menu_profile":
        register_user(call.from_user)
        t, m = profile_view(uid)
        show(call, t, m)

    elif data == "toggle_remind":
        u = register_user(call.from_user)
        u["remind"] = not u.get("remind", True)
        save()
        t, m = profile_view(uid)
        show(call, t, m)

    elif data == "menu_info":
        show(call, info_text(), kb(btn("⬅️ Artqa", "back_to_main")))


# ---------- Qoraqalpoq & O'zbek tili tahlilchisi va Tarjimon ----------
_CYR_TO_LAT = {
    "а": "a", "ә": "a", "б": "b", "в": "v", "г": "g", "ғ": "g", "д": "d",
    "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k",
    "қ": "q", "л": "l", "м": "m", "н": "n", "ң": "n", "о": "o", "ө": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ў": "u", "ү": "u",
    "ф": "f", "х": "x", "ҳ": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sh",
    "ъ": "", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "á": "a", "ó": "o", "ú": "u", "ǵ": "g", "ń": "n", "ı": "i",
}


def norm_qq(text):
    """Qoraqalpoq (lotin/kirill), O'zbek va Rus matnini yagona lotin qidiruv shakliga keltiradi."""
    s = (text or "").lower()
    out = []
    for ch in s:
        if ch in _CYR_TO_LAT:
            out.append(_CYR_TO_LAT[ch])
        elif ch.isalnum() or ch.isspace():
            out.append(ch)
        else:
            out.append(" ")
    return " ".join("".join(out).split())


_QQ_TO_UZ_WORDS = {
    "assalawma": "assalomu", "aleykum": "alaykum", "qayirli": "xayrli",
    "bugin": "bugun", "búgin": "bugun", "bugingi": "bugungi", "búgingi": "bugungi",
    "erten": "ertaga", "erteń": "ertaga", "erteng": "ertaga", "ertengi": "ertangi",
    "sabaq": "dars", "sabaqlar": "darslar", "sabaqlari": "darslari", "sabaqları": "darslari",
    "keste": "jadval", "kestesi": "jadvali", "saat": "soat", "neshede": "nechada",
    "neshe": "nechta", "nechenshi": "nechanchi", "baslanadi": "boshlanadi",
    "baslanadı": "boshlanadi", "qashan": "qachon", "qaysi": "qaysi", "qaysı": "qaysi",
    "qanday": "qanday", "qalay": "qalay", "jaqsi": "yaxshi", "jaqsı": "yaxshi",
    "barma": "bormi", "joq": "yo'q", "awa": "ha", "xana": "xona", "xanada": "xonada",
    "mugallim": "o'qituvchi", "muǵallim": "o'qituvchi", "oqitiwshi": "o'qituvchi",
    "ameliy": "amaliy", "ámeliy": "amaliy", "lekciya": "ma'ruza", "kitap": "kitob",
    "ushin": "uchun", "ushın": "uchun", "haqqinda": "haqida", "haqqında": "haqida",
    "boyinsha": "bo'yicha", "boyınsha": "bo'yicha", "kerek": "kerak",
    "jiber": "yubor", "tasla": "tashla", "awdar": "tarjima qil",
    "duyshembi": "dushanba", "dúyshembi": "dushanba", "siyshembi": "seshanba",
    "sarshembi": "chorshanba", "sárshembi": "chorshanba", "piyshembi": "payshanba",
    "shembi": "shanba", "ekshembi": "yakshanba", "hapte": "hafta", "hápte": "hafta",
}


def _prepare_source_text(text, sl):
    """Agar matnda qoraqalpoqcha so'zlar bo'lsa va manba uz/auto bo'lsa, tarjima aniqligini oshiradi."""
    if sl not in ("uz", "auto"):
        return text
    words = text.split()
    converted = []
    changed = 0
    for w in words:
        clean = w.strip(".,!?;:()\"'«»").lower()
        norm_w = norm_qq(clean)
        rep = _QQ_TO_UZ_WORDS.get(clean) or _QQ_TO_UZ_WORDS.get(norm_w)
        if rep:
            converted.append(rep)
            changed += 1
        else:
            converted.append(w)
    if changed > 0:
        return " ".join(converted)
    return text


def do_translate(text, src="auto", dest="uz"):
    import requests

    text = (text or "").strip()
    if not text:
        return ""
    sl = src or "auto"
    query_text = _prepare_source_text(text, sl)
    eff_sl = "uz" if (sl == "auto" and query_text != text) else sl
    # 1-usul: Google Translate GTX JSON API (eng tez va barqaror)
    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": eff_sl, "tl": dest, "dt": "t", "q": query_text},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        out = "".join(seg[0] for seg in data[0] if seg and seg[0])
        if out:
            return out
    except Exception:
        pass
    # 2-usul: Google clients5 API
    try:
        r = requests.get(
            "https://clients5.google.com/translate_a/t",
            params={"client": "dict-chrome-ex", "sl": eff_sl, "tl": dest, "q": query_text},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            first = data[0]
            out = first[0] if isinstance(first, list) else str(first)
            if out:
                return out
    except Exception:
        pass
    # 3-usul: MyMemory API
    try:
        pair_src = "uz" if eff_sl == "auto" else eff_sl
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": query_text[:480], "langpair": f"{pair_src}|{dest}"},
            timeout=12,
        )
        r.raise_for_status()
        out = (r.json().get("responseData") or {}).get("translatedText")
        if out and "INVALID" not in out.upper():
            return out
    except Exception:
        pass
    # 4-usul: deep_translator zaxira
    return GoogleTranslator(source=eff_sl, target=dest).translate(query_text)


def detect_and_translate(text):
    import requests

    prep = _prepare_source_text(text, "auto")
    is_qq_or_uz = prep != text
    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "uz" if is_qq_or_uz else "auto",
                "tl": "uz",
                "dt": "t",
                "q": prep,
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        detected = "uz" if is_qq_or_uz else (data[2] if len(data) > 2 else "uz")
        uz_text = "".join(seg[0] for seg in data[0] if seg and seg[0])
        if detected in ("uz", "kk", "ky", "tk", "tr", "kaa"):
            en_text = do_translate(prep, "uz", "en")
            ru_text = do_translate(prep, "uz", "ru")
            return (
                f"🇬🇧 <b>Inglisshe:</b>\n{html.escape(en_text)}\n\n"
                f"🇷🇺 <b>Orıssha:</b>\n{html.escape(ru_text)}"
            )
        return f"🇺🇿 <b>Awdarma:</b>\n{html.escape(uz_text)}"
    except Exception:
        res = do_translate(prep, "auto", "uz")
        return html.escape(res)


@bot.message_handler(commands=["tr", "awdar", "tarjima"])
def tr_cmd(message):
    register_group(message.chat)
    parts = (message.text or "").split(maxsplit=1)
    target_text = parts[1].strip() if len(parts) > 1 else ""
    if not target_text and message.reply_to_message:
        target_text = message.reply_to_message.text or message.reply_to_message.caption or ""
    if not target_text:
        bot.reply_to(
            message,
            "✍️ Awdarma qılıw ushın: <code>/tr tekst</code> jazıń yaki xabarǵa <i>Reply</i> qılıp <code>/tr</code> basıń.",
        )
        return
    try:
        body = detect_and_translate(target_text)
        bot.reply_to(message, body)
    except Exception:
        bot.reply_to(message, "❌ Awdarma qılıwda qátelik.")


_WEEKDAY_ALIASES = {
    0: ["duyshembi", "duyshambi", "dushanba", "dushanbi", "ponedelnik"],
    1: ["siyshembi", "seyshambi", "seshanba", "seshanbi", "vtornik"],
    2: ["sarshembi", "sharshambi", "chorshanba", "sreda"],
    3: ["piyshembi", "payshambi", "payshanba", "chetverg"],
    4: ["juma", "jumaa", "pyatnica", "pyatnitsa"],
    5: ["shembi", "shanba", "shanbi", "subbota"],
    6: ["ekshembi", "yakshanba", "voskresenye"],
}

_SUBJECT_ALIASES = [
    (0, ["fizika"]),
    (1, ["ingliz", "inglisshe", "angliyskiy", "shet tili", "chet tili", "english"]),
    (2, ["geodeziya", "geodez"]),
    (3, ["matematika", "matem", "joqari matematika", "oliy matematika"]),
    (4, ["tariyx", "tarix", "istoriya"]),
    (5, ["qaraqalpaq", "qoraqalpoq", "qq tili"]),
    (6, ["rus tili", "oris tili", "orissha", "russkiy", "russha"]),
]


def _send_subject_card(message, idx, ntext):
    s = DATA["subjects"][idx]
    if s.get("single"):
        items = s.get("lectures") or []
        body = "Materialdı tańlań (ústine bassańız PDF ashıladı):" if items else "Ele qosılmaǵan."
        bot.reply_to(
            message,
            header("📚", html.escape(s["name"])) + body,
            reply_markup=kb(
                *[btn(it["title"], f"it:{idx}:l:{j}") for j, it in enumerate(items)],
                btn("📚 Barlıq pánler", "menu_subjects"),
            ),
        )
        return
    # Agar aniq lekciya yoki ameliy/lab so'ragan bo'lsa:
    wants_lec = any(w in ntext for w in ["lekciya", "leksiya", "maruza"])
    wants_lab = any(w in ntext for w in ["ameliy", "amaliy", "lab", "laboratoriya", "labaratoriya", "seminar"])
    sec_icon, sec_name = second_section(s["name"])
    if wants_lec and not wants_lab:
        bot.reply_to(
            message,
            header("📖", f"{html.escape(s['name'])} — Lekciyalar") + "Temanı tańlań:",
            reply_markup=kb(
                *[btn(it["title"], f"it:{idx}:l:{j}") for j, it in enumerate(s["lectures"])],
                btn("⬅️ Bólimler", f"s:{idx}"),
            ),
        )
    elif wants_lab and not wants_lec:
        bot.reply_to(
            message,
            header(sec_icon, f"{html.escape(s['name'])} — {sec_name}") + "Temanı tańlań:",
            reply_markup=kb(
                *[btn(it["title"], f"it:{idx}:b:{j}") for j, it in enumerate(s["labs"])],
                btn("⬅️ Bólimler", f"s:{idx}"),
            ),
        )
    else:
        bot.reply_to(
            message,
            header("📚", html.escape(s["name"])) + "Bólimdi tańlań:",
            reply_markup=kb(
                btn(f"📖 Lekciyalar ({len(s['lectures'])})", f"sl:{idx}"),
                btn(f"{sec_icon} {sec_name} ({len(s['labs'])})", f"sb:{idx}"),
                btn("📚 Barlıq pánler", "menu_subjects"),
            ),
        )


def try_smart_assistant(message):
    """Qoraqalpoq va o'zbek tillarida berilgan savollarga (jadval, fanlar, kurator, starosta) javob beradi."""
    ntext = norm_qq(message.text or "")
    if not ntext:
        return False
    words = set(ntext.split())
    is_group = message.chat.type in ("group", "supergroup")

    sched_words = {
        "sabaq", "sabaqlar", "sabaqlari", "dars", "darslar", "para", "paralar",
        "keste", "kestesi", "jadval", "jadvali", "raspisaniye", "raspisaniya",
        "xana", "xanada", "kabinet", "auditoriya",
    }
    question_words = {
        "ne", "nima", "qaysi", "qanday", "neshe", "nechta", "nechenshi", "nechanchi",
        "barma", "bormi", "qashan", "qachon", "neshede", "nechada", "saat", "soat",
    }

    # 1. Ertaga / Erteńgi darslar
    if words & {"erten", "erteng", "ertengi", "ertaga", "ertangi", "zavtra"}:
        if (words & sched_words) or (words & question_words) or len(words) <= 3:
            bot.reply_to(
                message,
                tomorrow_text(),
                reply_markup=kb(btn("📅 Háptelik keste", "sch_week"), btn("📚 Pánler", "menu_subjects"), width=2),
            )
            return True

    # 2. Bugungi / Búgingi darslar
    if words & {"bugin", "bugingi", "bugun", "bugungi", "segodnya"}:
        if (words & sched_words) or (words & question_words) or len(words) <= 3:
            bot.reply_to(
                message,
                today_text(),
                reply_markup=kb(btn("📆 Erteńgi keste", "sch_tomorrow"), btn("📅 Háptelik", "sch_week"), width=2),
            )
            return True

    # 3. Hafta kunlari bo'yicha (Dúyshembi, Siyshembi, ...)
    for day_idx, aliases in _WEEKDAY_ALIASES.items():
        if any(a in words for a in aliases):
            if (words & sched_words) or (words & question_words) or not is_group:
                bot.reply_to(
                    message,
                    day_schedule_text(day_idx),
                    reply_markup=kb(btn("📅 Háptelik keste", "sch_week"), width=1),
                )
                return True

    # 4. Haftalik jadval yoki umumiy "sabaq kestesi" / "bugun nechenshi para"
    if (
        ("hapte" in words or "haptelik" in words or "hafta" in words or "haftalik" in words)
        and (words & sched_words)
    ):
        bot.reply_to(message, week_text())
        return True

    if any(
        phrase in ntext
        for phrase in [
            "sabaq keste", "dars jadval", "nechenshi para", "neshe para",
            "saat neshede sabaq", "sabaq saat neshede", "qaysi xana", "qaysi kabinet",
        ]
    ) or ntext in ("keste", "jadval", "sabaq", "sabaqlar", "raspisaniye", "raspisaniya"):
        bot.reply_to(
            message,
            today_text(),
            reply_markup=kb(btn("📆 Erteńgi keste", "sch_tomorrow"), btn("📅 Háptelik", "sch_week"), width=2),
        )
        return True

    # 5. Fanlar va PDF materiallar
    mat_triggers = {
        "pdf", "lekciya", "leksiya", "maruza", "ameliy", "amaliy", "lab",
        "laboratoriya", "labaratoriya", "kitap", "kitob", "fayl", "material",
        "tema", "mavzu", "tasla", "tashla", "jiber", "ber", "barma", "bormi",
        "kerek", "kerak", "bot", "katastr1abot",
    }
    for idx, aliases in _SUBJECT_ALIASES:
        if any(a in ntext for a in aliases):
            if not is_group or (words & mat_triggers) or len(words) <= 3:
                _send_subject_card(message, idx, ntext)
                return True

    if ntext in ("fanlar", "sabaqlar", "panler", "pdf", "lekciyalar", "kitaplar") or (
        ("pdf" in words or "lekciya" in words) and ("barma" in words or "bormi" in words or "jiber" in words or "tasla" in words)
    ):
        subjects_cmd(message)
        return True

    # 6. Kurator, Starosta, Guruh ro'yxati, Imtihonlar
    if "kurator" in ntext or "ziyada" in words or "avezova" in words:
        if not is_group or (words & {"kim", "nomer", "nomeri", "raqami", "tel", "lichka", "barma", "bormi"}) or len(words) <= 3:
            bot.reply_to(message, person("👩‍🏫 <b>Kurator</b>", CURATOR))
            return True

    if "starosta" in ntext or ("abbaz" in words and ("nomer" in ntext or "tel" in ntext)):
        if not is_group or (words & {"kim", "nomer", "nomeri", "raqami", "tel", "lichka", "barma", "bormi"}) or len(words) <= 3:
            bot.reply_to(message, person("⭐ <b>Starosta</b>", STAROSTA))
            return True

    if any(p in ntext for p in ["gruppa dizimi", "studentler dizimi", "guruh royxati", "guruhdoshlar", "kurslaslar", "gruppalaslar"]):
        lines = []
        n = 0
        for m in DATA["mates"]:
            if m.get("role"):
                line = f"⭐ <b>{m['role']}:</b> {html.escape(m['name'])}"
            else:
                n += 1
                line = f"{n}. {html.escape(m['name'])}"
            if m.get("tg"):
                line += f" — @{m['tg']}"
            if m.get("phone"):
                line += f" — {m['phone']}"
            lines.append(line)
        bot.reply_to(message, header("👥", f"Gruppalaslar — {html.escape(DATA['group'])}") + "\n".join(lines))
        return True

    if ("imtixan" in ntext or "imtihon" in ntext or "sessiya" in ntext) and (
        words & {"qashan", "qachon", "barma", "bormi", "keste", "jadval"}
    ):
        today = datetime.now(TZ).date()
        lines = []
        for e in sorted(DATA["exams"], key=lambda x: x["date"]):
            d = datetime.strptime(e["date"], "%Y-%m-%d").date()
            left = (d - today).days
            if left >= 0:
                lines.append(f"📝 <b>{html.escape(e['name'])}</b>\n     🗓 {e['date']} — ⏳ {left} kún qaldı")
        body = "\n\n".join(lines) if lines else "Házirshe rejelestirilgen imtixan joq."
        bot.reply_to(message, header("📝", "Imtixanlar") + body)
        return True

    # 6.5. Tuwılǵan kúnler (umumiy yoki aniq ism bo'yicha)
    bday_triggers = {
        "tuwilgan", "tugilgan", "tuilgan", "rojdeniya", "bday",
        "tuwildi", "tugildi", "jasqa", "yoshga",
    }
    if (words & bday_triggers) or "tuwilgan kun" in ntext or "tugilgan kun" in ntext:
        bdays = DATA.get("birthdays") or BIRTHDAYS
        matched = [b for b in bdays if norm_qq(b["name"]) in ntext]
        if matched:
            today = datetime.now(TZ).date()
            lines = []
            for b in matched:
                left, age = _bday_days_left(b, today)
                mname = MONTHS_QQ[b["month"]].lower()
                status = "🎉 <b>Búgin tuwılǵan kúni!</b>" if left == 0 else (
                    f"⏳ Erteń ({age} jasqa toladı)" if left == 1 else f"⏳ {left} kún qaldı ({age} jasqa toladı)"
                )
                lines.append(
                    f"🎂 <b>{html.escape(b['name'])}</b> — <b>{b['day']}-{mname} {b['year']}</b>\n{status}"
                )
            bot.reply_to(
                message,
                "\n\n".join(lines),
                reply_markup=kb(btn("🎂 Barlıq tuwılǵan kúnler", "menu_birthdays")),
            )
            return True
        bot.reply_to(message, birthdays_text())
        return True

    # 7. Guruhda "bot awdar ..." yoki "bot tarjima ..."
    if is_group and ("awdar" in words or "tarjima" in words) and ("bot" in words or message.reply_to_message):
        target = message.reply_to_message.text if message.reply_to_message else message.text
        if target:
            bot.reply_to(message, detect_and_translate(target))
            return True

    return False


@bot.message_handler(func=lambda m: True, content_types=["text"])
def translate_message(message):
    register_group(message.chat)
    u = register_user(message.from_user)
    is_group = message.chat.type in ("group", "supergroup")

    # Guruhda oddiy suhbatga xalaqit bermaymiz — faqat savollarga javob beramiz
    if is_group:
        try_smart_assistant(message)
        return

    direction = user_direction.get(message.chat.id)
    if not direction:
        saved_tr = u.get("tr")
        if isinstance(saved_tr, list) and len(saved_tr) == 2:
            direction = (saved_tr[0], saved_tr[1])

    # Agar foydalanuvchi aniq tarjima yo'nalishini tanlamagan bo'lsa va jadval/fan so'rasa:
    if not direction and try_smart_assistant(message):
        return

    nav_kb = kb(
        btn("🌐 Baǵdardı tańlaw", "menu_translation"),
        btn("🏠 Bas menyu", "back_to_main"),
        width=2,
    )
    try:
        if direction:
            src, dest = direction
            result = do_translate(message.text, src, dest)
            bot.reply_to(message, html.escape(result), reply_markup=nav_kb)
        else:
            body = detect_and_translate(message.text)
            bot.reply_to(message, body, reply_markup=nav_kb)
        u["translations"] = u.get("translations", 0) + 1
        save()
    except Exception:
        bot.reply_to(
            message,
            "❌ Awdarma qılıwda qátelik. Keyinirek urınıp kóriń.",
            reply_markup=nav_kb,
        )


# ---------- Eslatmalar (07:30 ertalabki keste + 15 daqiqa oldin eslatma) ----------
MORNING_TIME = "07:30"


def reminder_loop():
    sent = set()
    while True:
        try:
            now = datetime.now(TZ)
            today_str = now.strftime("%Y-%m-%d")
            now_hm = now.strftime("%H:%M")
            wday = now.weekday()
            today_lessons = active_schedule().get(str(wday), [])

            # 0) Har kuni ertalab 07:30 da tug'ilgan kun tabrigi (agar bugun kimningdir tug'ilgan kuni bo'lsa)
            bday_key = (today_str, "BDAY_0730")
            if now_hm == MORNING_TIME and bday_key not in sent:
                sent.add(bday_key)
                bdays = DATA.get("birthdays") or BIRTHDAYS
                todays_bdays = [
                    b for b in bdays
                    if int(b["day"]) == now.day and int(b["month"]) == now.month
                ]
                if todays_bdays:
                    names_lines = []
                    for b in todays_bdays:
                        age = now.year - int(b["year"])
                        names_lines.append(f"🥳 <b>{html.escape(b['name'])}</b> ({age} jas!)")
                    bday_msg = (
                        f"🎉🎂 <b>QUTLÍQLAYMÍZ! BÚGIN TUWÍLǴAN KÚN!</b> 🎂🎉\n"
                        f"{LINE}\n"
                        f"Búgin <b>{html.escape(DATA['group'])}</b> gruppalasımız:\n"
                        + "\n".join(names_lines)
                        + "\n\n✨ Sizge uzaq ómir, bekem densawlıq, oqıwlarıńızda úlken tabıslar hám "
                        "barlıq jaqsı niyetlerińizge jetiwińizdi tileymiz! Tuwılǵan kúnińiz qutlı bolsın! 🥳🎁🎈"
                    )
                    for gid, g in list(DATA.get("groups", {}).items()):
                        if g.get("remind", True):
                            try:
                                bot.send_message(int(gid), bday_msg)
                            except Exception:
                                pass
                    for uid, u in list(DATA["users"].items()):
                        if u.get("remind", True):
                            try:
                                bot.send_message(int(uid), bday_msg)
                            except Exception:
                                pass

            # 1) Har kuni ertalab 07:30 da dars bor kunlari guruhlarga va obunachilarga jadval yuborish
            morning_key = (today_str, "MORNING_0730")
            if now_hm == MORNING_TIME and today_lessons and morning_key not in sent:
                sent.add(morning_key)
                morning_msg = (
                    f"☀️ <b>Qayırli tań, {html.escape(DATA['group'])} gruppası!</b>\n"
                    f"📅 <b>Búgingi sabaq kestesi — {DAYS_QQ[wday]} ({DAYS[wday]}):</b>\n"
                    f"{LINE}\n"
                    f"{fmt_day(wday)}\n\n"
                    f"📚 <i>Barlıq PDF hám lekciyalar: @Katastr1a_bot</i>"
                )
                for gid, g in list(DATA.get("groups", {}).items()):
                    if g.get("remind", True):
                        try:
                            bot.send_message(
                                int(gid),
                                morning_msg,
                                reply_markup=kb(btn("📚 Fanlar / PDF", "menu_subjects"), width=1),
                            )
                        except Exception:
                            pass

            # 2) Har bir para boshlanishidan 15 daqiqa oldin eslatma
            target = (now + timedelta(minutes=REMIND_BEFORE_MIN)).strftime("%H:%M")
            for item in today_lessons:
                key = (today_str, item["time"], item["name"])
                if item["time"] == target and key not in sent:
                    sent.add(key)
                    t_range = f"{item['time']} - {item['end']}" if item.get("end") else item["time"]
                    tp = f" ({html.escape(item['type'])})" if item.get("type") else ""
                    extra = []
                    if item.get("teacher"):
                        extra.append(f"👩‍🏫 {html.escape(item['teacher'])}")
                    if item.get("room"):
                        extra.append(f"🚪 {html.escape(item['room'])}")
                    extra_line = ("\n" + " • ".join(extra)) if extra else ""
                    remind_msg = (
                        f"⏰ <b>{REMIND_BEFORE_MIN} minuttan keyin sabaq baslanadı!</b>\n"
                        f"📘 <b>{html.escape(item['name'])}</b>{tp}\n"
                        f"🕒 Waqtı: <b>{html.escape(t_range)}</b>{extra_line}"
                    )
                    for uid, u in list(DATA["users"].items()):
                        if u.get("remind", True):
                            try:
                                bot.send_message(int(uid), remind_msg)
                            except Exception:
                                pass
                    for gid, g in list(DATA.get("groups", {}).items()):
                        if g.get("remind", True):
                            try:
                                bot.send_message(int(gid), remind_msg)
                            except Exception:
                                pass
            if len(sent) > 500:
                sent.clear()
        except Exception:
            pass
        time.sleep(25)


def start_health_server():
    """Hosting (Render) PORT bersa, Mini App va API serverini ishga tushiradi."""
    port = os.getenv("PORT")
    if not port:
        return
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs, urlparse

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="text/plain; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            if path in ("/", "/app", "/index.html"):
                if os.path.exists(WEBAPP_FILE):
                    with open(WEBAPP_FILE, "rb") as f:
                        self._send(200, f.read(), "text/html; charset=utf-8")
                else:
                    self._send(200, b"OK")
            elif path == "/assets/banner.jpg" and os.path.exists(BANNER):
                with open(BANNER, "rb") as f:
                    self._send(200, f.read(), "image/jpeg")
            elif path == "/api/data":
                with LOCK:
                    payload = {
                        "group": DATA.get("group", "Katastr 1-a"),
                        "subjects": DATA.get("subjects", []),
                        "schedule": active_schedule(),
                        "schedule_expired": is_schedule_expired(),
                        "schedule_until": DATA.get("schedule_until", ""),
                        "announcements": DATA.get("announcements", []),
                        "exams": DATA.get("exams", []),
                        "mates": DATA.get("mates", []),
                        "birthdays": DATA.get("birthdays", BIRTHDAYS),
                        "leaders": {
                            "curator": CURATOR,
                            "starosta": STAROSTA,
                            "creator": CREATOR,
                        },
                    }
                self._send(
                    200,
                    json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            elif path == "/api/file":
                import requests

                qs = parse_qs(parsed.query)
                try:
                    si = int((qs.get("s") or ["0"])[0])
                    k = (qs.get("k") or ["l"])[0]
                    ji = int((qs.get("j") or ["0"])[0])
                    kind = "lectures" if k == "l" else "labs"
                    item = DATA["subjects"][si][kind][ji]
                    finfo = bot.get_file(item["content"])
                    furl = f"https://api.telegram.org/file/bot{TOKEN}/{finfo.file_path}"
                    resp = requests.get(furl, timeout=30)
                    resp.raise_for_status()
                    ext = os.path.splitext(finfo.file_path)[1].lower()
                    ctype = "application/pdf" if ext == ".pdf" else (
                        "image/jpeg" if ext in (".jpg", ".jpeg") else "application/octet-stream"
                    )
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    fname = os.path.basename(finfo.file_path)
                    self.send_header("Content-Disposition", f'inline; filename="{fname}"')
                    self.end_headers()
                    self.wfile.write(resp.content)
                except Exception:
                    self._send(404, b"Fayl topilmadi")
            elif path == "/api/translate":
                qs = parse_qs(parsed.query)
                src = (qs.get("src") or ["uz"])[0]
                dest = (qs.get("dest") or ["en"])[0]
                q = (qs.get("q") or [""])[0]
                try:
                    res = do_translate(q, src, dest) if q else ""
                    body = json.dumps({"result": res}, ensure_ascii=False).encode("utf-8")
                except Exception:
                    body = json.dumps({"error": "Tarjima qilishda xatolik"}).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8")
            else:
                self._send(200, b"OK")

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("0.0.0.0", int(port)), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


if __name__ == "__main__":
    start_health_server()
    for fn, arg in [
        (bot.set_my_name, BOT_NAME),
        (bot.set_my_short_description, "🎓 Katastr 1-A guruhi uchun: fanlar, jadval, tarjimon va e'lonlar"),
        (bot.set_my_description,
         "🎓 Katastr 1-A Hub — guruh uchun shaxsiy yordamchi:\n"
         "📚 fanlar va ma'ruzalar\n📅 dars jadvali va eslatmalar\n🌐 tarjimon\n📝 imtihonlar\n📢 e'lonlar"),
        (bot.set_my_commands, [
            types.BotCommand("start", "🏠 Bas menyu"),
            types.BotCommand("bugin", "🕒 Búgingi sabaqlar"),
            types.BotCommand("erten", "📆 Erteńgi sabaqlar"),
            types.BotCommand("keste", "📅 Háptelik sabaq kestesi"),
            types.BotCommand("fanlar", "📚 Pánler hám PDF materiallar"),
            types.BotCommand("tuwilgankun", "🎂 Tuwılǵan kúnler"),
            types.BotCommand("tr", "🌐 Awdarma / Tarjima"),
        ]),
    ]:
        try:
            fn(arg)
        except Exception as e:
            print("Profil sozlanmadi:", e)
    threading.Thread(target=reminder_loop, daemon=True).start()
    if CLOUD:
        threading.Thread(target=cloud_sync_loop, daemon=True).start()
        _dirty.set()  # birinchi marta mahalliy ma'lumotni bulutga yozib qo'yadi
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()


