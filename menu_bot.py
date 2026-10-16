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
        "schedule": {
            "0": [{"time": "09:00", "name": "Fizika"}, {"time": "10:30", "name": "Matematika"}],
            "1": [{"time": "09:00", "name": "Ingliz tili"}],
            "2": [{"time": "09:00", "name": "Fizika (Lab)"}],
        },
        "announcements": [],
        "exams": [],
        "mates": default_mates(),
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


def load_data():
    if CLOUD:
        try:
            data = cloud_load()
            if data:
                print("Ma'lumotlar Supabase'dan yuklandi.")
                return data
        except Exception as e:
            print("Supabase'dan o'qib bo'lmadi:", e)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                return json.load(f)
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
        u = DATA["users"].setdefault(
            str(user.id),
            {"joined": datetime.now(TZ).strftime("%Y-%m-%d"), "translations": 0, "remind": True},
        )
        u["name"] = " ".join(x for x in [user.first_name, user.last_name] if x)
        u["username"] = user.username or ""
        save()
        return u


user_direction = {}  # chat_id -> (src, dest)

DIRECTIONS = {
    "tr_uz_en": ("uz", "en", "🇺🇿 O'zbekcha → 🇬🇧 Inglizcha"),
    "tr_en_uz": ("en", "uz", "🇬🇧 Inglizcha → 🇺🇿 O'zbekcha"),
    "tr_ru_uz": ("ru", "uz", "🇷🇺 Ruscha → 🇺🇿 O'zbekcha"),
    "tr_uz_ru": ("uz", "ru", "🇺🇿 O'zbekcha → 🇷🇺 Ruscha"),
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


def main_menu(uid=None):
    b = [
        btn("📚 Fanlar", "menu_subjects"),
        btn("📅 Jadval", "menu_schedule"),
        btn("🌐 Tarjimon", "menu_translation"),
        btn("📝 Imtihonlar", "menu_exams"),
        btn("📢 E'lonlar", "menu_ann"),
        btn("👥 Guruhdoshlar", "menu_mates"),
        btn("👤 Profilim", "menu_profile"),
        btn("ℹ️ Ma'lumot", "menu_info"),
    ]
    if uid is not None and is_admin(uid):
        b.append(btn("🛠 Admin panel", "adm"))
    return kb(*b, width=2)


def show(call, text, markup=None):
    try:
        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id, reply_markup=markup
        )
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e):
            raise


def creator_footer():
    return "\n\n💻 Yaratuvchi: <b>{}</b> (@{})".format(CREATOR["name"], CREATOR["tg"])


def info_text():
    return (
        header("ℹ️", BOT_NAME)
        + "Kursdoshlar uchun o'quv materiallari, dars jadvali va foydali ma'lumotlar boti.\n\n"
        f"🎓 Guruh: <b>{html.escape(DATA['group'])}</b>\n\n"
        + person("👩‍🏫 <b>Kurator</b>", CURATOR) + "\n\n"
        + person("⭐ <b>Starosta</b>", STAROSTA) + "\n\n"
        + person("💻 <b>Bot yaratuvchisi</b>", CREATOR)
    )


# ---------- /start, /help, /myid ----------
@bot.message_handler(commands=["start"])
def send_welcome(message):
    register_user(message.from_user)
    user_direction.pop(message.chat.id, None)
    if os.path.exists(BANNER):
        try:
            with open(BANNER, "rb") as f:
                bot.send_photo(
                    message.chat.id, f,
                    caption=f"🎓 <b>{BOT_NAME}</b>\n{html.escape(DATA['group'])} guruhi uchun",
                )
        except Exception:
            pass
    bot.send_message(
        message.chat.id,
        f"Assalomu alaykum, <b>{html.escape(message.from_user.first_name or 'do‘st')}</b>! 👋\n"
        f"<b>{BOT_NAME}</b> — <b>{html.escape(DATA['group'])}</b> guruhining shaxsiy yordamchisi."
        + creator_footer()
        + f"\n{LINE}\nKerakli bo'limni tanlang 👇",
        reply_markup=main_menu(message.from_user.id),
    )


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "/start - bosh menyu\n/today - bugungi darslar\n/week - haftalik jadval\n"
        "/profile - profilim\n/myid - Telegram ID\n/admin - admin panel",
    )


@bot.message_handler(commands=["myid"])
def myid(message):
    bot.reply_to(message, f"Sizning ID: <code>{message.from_user.id}</code>")


@bot.message_handler(commands=["today"])
def today_cmd(message):
    bot.send_message(message.chat.id, today_text())


@bot.message_handler(commands=["week"])
def week_cmd(message):
    bot.send_message(message.chat.id, week_text())


@bot.message_handler(commands=["profile"])
def profile_cmd(message):
    register_user(message.from_user)
    t, m = profile_view(message.from_user.id)
    bot.send_message(message.chat.id, t, reply_markup=m)


@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Siz admin emassiz.")
        return
    bot.send_message(message.chat.id, "🛠 Admin panel:", reply_markup=admin_menu())


# ---------- Jadval ----------
def fmt_day(i):
    items = sorted(DATA["schedule"].get(str(i), []), key=lambda x: x["time"])
    if not items:
        return "— dars yo'q"
    return "\n".join(f"🕒 {x['time']} — {html.escape(x['name'])}" for x in items)


def week_text():
    days = [f"<b>{DAYS[i]}</b>\n{fmt_day(i)}" for i in range(7) if DATA["schedule"].get(str(i))]
    if not days:
        return header("📅", "Haftalik dars jadvali") + "Jadval hali kiritilmagan."
    return header("📅", "Haftalik dars jadvali") + "\n\n".join(days)


def today_text():
    i = datetime.now(TZ).weekday()
    return header("🕒", f"Bugungi darslar — {DAYS[i]}") + fmt_day(i)


# ---------- Profil ----------
def profile_view(uid):
    u = DATA["users"].get(str(uid), {})
    text = (
        header("👤", "Profilim")
        + f"🙍 Ism: {html.escape(u.get('name', '-'))}\n"
        f"🔗 Username: @{u.get('username') or '-'}\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"📆 Qo'shilgan sana: {u.get('joined', '-')}\n"
        f"🌐 Tarjimalar soni: {u.get('translations', 0)}\n"
        f"⏰ Dars eslatmasi: {'🔔 yoqilgan' if u.get('remind', True) else '🔕 o‘chirilgan'}"
    )
    m = kb(
        btn("🔕 Eslatmani o'chirish" if u.get("remind", True) else "🔔 Eslatmani yoqish", "toggle_remind"),
        btn("⬅️ Orqaga", "back_to_main"),
    )
    return text, m


# ---------- Admin ----------
def admin_menu():
    return kb(
        btn("➕ Ma'ruza qo'shish", "adm_add:lectures"),
        btn("➕ Laboratoriya qo'shish", "adm_add:labs"),
        btn("📚 Yangi fan qo'shish", "adm_subject"),
        btn("📅 Kun jadvalini o'zgartirish", "adm_sched"),
        btn("📢 E'lon yuborish", "adm_ann"),
        btn("📝 Imtihon qo'shish", "adm_exam"),
        btn("🗑 Imtihonlarni tozalash", "adm_clear:exams"),
        btn("🗑 E'lonlarni tozalash", "adm_clear:ann"),
        btn("👥 Guruhdosh qo'shish", "adm_mate"),
        btn("🎓 Guruh nomini o'zgartirish", "adm_group"),
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
    DATA["schedule"][str(day)] = items
    save()
    bot.send_message(message.chat.id, f"✅ {DAYS[day]} jadvali yangilandi.", reply_markup=admin_menu())


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
            bot.send_message(int(uid), f"📢 <b>E'lon</b>\n\n{text}")
            sent += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ {sent} ta foydalanuvchiga yuborildi.", reply_markup=admin_menu())


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
    elif data == "adm_stats":
        users = DATA["users"].values()
        tr = sum(u.get("translations", 0) for u in users)
        bot.send_message(chat_id, f"📊 Foydalanuvchilar: {len(users)}\nTarjimalar: {tr}")


# ---------- Tugmalar ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    uid = call.from_user.id
    data = call.data

    if data.startswith("adm"):
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "⛔ Faqat admin uchun", show_alert=True)
            return
        handle_admin(call)

    elif data == "back_to_main":
        user_direction.pop(chat_id, None)
        show(call, header("🏠", "Asosiy menyu") + f"🎓 {html.escape(DATA['group'])}\nBo'limni tanlang 👇",
             main_menu(uid))

    elif data == "menu_translation":
        user_direction.pop(chat_id, None)
        show(call, header("🌐", "Tarjimon") + "Tarjima yo'nalishini tanlang:", kb(
            *[btn(v[2], k) for k, v in DIRECTIONS.items()], btn("⬅️ Orqaga", "back_to_main")))

    elif data in DIRECTIONS:
        src, dest, label = DIRECTIONS[data]
        user_direction[chat_id] = (src, dest)
        show(call, header("🌐", "Tarjimon") + f"✅ Yo'nalish: <b>{label}</b>\n\n"
             "✍️ Endi tarjima qilinadigan matnni yuboring.",
             kb(btn("⬅️ Orqaga", "menu_translation")))

    elif data == "menu_subjects":
        show(call, header("📚", "Fanlar") + "Fanni tanlang:", kb(
            *[btn(s["name"], f"s:{i}") for i, s in enumerate(DATA["subjects"])],
            btn("⬅️ Orqaga", "back_to_main")))

    elif data.startswith("s:"):
        i = int(data[2:])
        s = DATA["subjects"][i]
        show(call, header("📚", html.escape(s["name"])) + "Bo'limni tanlang:", kb(
            btn(f"📖 Ma'ruzalar ({len(s['lectures'])})", f"sl:{i}"),
            btn(f"🧪 Laboratoriya ({len(s['labs'])})", f"sb:{i}"),
            btn("⬅️ Fanlarga qaytish", "menu_subjects")))

    elif data.startswith(("sl:", "sb:")):
        i = int(data[3:])
        kind = "lectures" if data.startswith("sl:") else "labs"
        s = DATA["subjects"][i]
        icon, name = ("📖", "Ma'ruzalar") if kind == "lectures" else ("🧪", "Laboratoriya ishlari")
        body = "Mavzuni tanlang:" if s[kind] else "Hali qo'shilmagan."
        show(call, header(icon, f"{html.escape(s['name'])} — {name}") + body, kb(
            *[btn(it["title"], f"it:{i}:{kind[0]}:{j}") for j, it in enumerate(s[kind])],
            btn("⬅️ Orqaga", f"s:{i}")))

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
        show(call, header("📅", "Dars jadvali") + "Tanlang:", kb(
            btn("📅 Haftalik", "sch_week"), btn("🕒 Bugun", "sch_today"),
            btn("⬅️ Orqaga", "back_to_main"), width=2))

    elif data == "sch_week":
        show(call, week_text(), kb(btn("⬅️ Orqaga", "menu_schedule")))

    elif data == "sch_today":
        show(call, today_text(), kb(btn("⬅️ Orqaga", "menu_schedule")))

    elif data == "menu_ann":
        anns = DATA["announcements"][-5:][::-1]
        body = "\n\n".join(f"🗓 <i>{a['date']}</i>\n{a['text']}" for a in anns) if anns else "E'lonlar yo'q."
        show(call, header("📢", "So'nggi e'lonlar") + body, kb(btn("⬅️ Orqaga", "back_to_main")))

    elif data == "menu_exams":
        today = datetime.now(TZ).date()
        lines = []
        for e in sorted(DATA["exams"], key=lambda x: x["date"]):
            d = datetime.strptime(e["date"], "%Y-%m-%d").date()
            left = (d - today).days
            if left >= 0:
                lines.append(f"📝 <b>{html.escape(e['name'])}</b>\n     🗓 {e['date']} — ⏳ {left} kun qoldi")
        body = "\n\n".join(lines) if lines else "Rejalashtirilgan imtihon yo'q."
        show(call, header("📝", "Imtihonlar") + body, kb(btn("⬅️ Orqaga", "back_to_main")))

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
        show(call, header("👥", f"Guruhdoshlar — {html.escape(DATA['group'])}") + "\n".join(lines),
             kb(btn("⬅️ Orqaga", "back_to_main")))

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
        show(call, info_text(), kb(btn("⬅️ Orqaga", "back_to_main")))


# ---------- Tarjima ----------
@bot.message_handler(func=lambda m: True, content_types=["text"])
def translate_message(message):
    direction = user_direction.get(message.chat.id)
    if not direction:
        bot.reply_to(message, "Menyu uchun /start bosing.")
        return
    src, dest = direction
    try:
        result = GoogleTranslator(source=src, target=dest).translate(message.text)
        bot.reply_to(message, html.escape(result))
        u = register_user(message.from_user)
        u["translations"] = u.get("translations", 0) + 1
        save()
    except Exception:
        bot.reply_to(message, "❌ Tarjima qilishda xatolik. Keyinroq urinib ko'ring.")


# ---------- Eslatmalar ----------
def reminder_loop():
    sent = set()
    while True:
        try:
            now = datetime.now(TZ)
            target = (now + timedelta(minutes=REMIND_BEFORE_MIN)).strftime("%H:%M")
            for item in DATA["schedule"].get(str(now.weekday()), []):
                key = (now.strftime("%Y-%m-%d"), item["time"], item["name"])
                if item["time"] == target and key not in sent:
                    sent.add(key)
                    for uid, u in list(DATA["users"].items()):
                        if u.get("remind", True):
                            try:
                                bot.send_message(
                                    int(uid),
                                    f"⏰ {REMIND_BEFORE_MIN} daqiqadan keyin dars: "
                                    f"<b>{html.escape(item['name'])}</b> ({item['time']})",
                                )
                            except Exception:
                                pass
            if len(sent) > 500:
                sent.clear()
        except Exception:
            pass
        time.sleep(30)


def start_health_server():
    """Hosting (Render) PORT bersa, oddiy HTTP server ishga tushiradi."""
    port = os.getenv("PORT")
    if not port:
        return
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

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


