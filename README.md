# Supermarket Telegram Bot 🛒🇺🇿

Production-ready Telegram bot for a supermarket/grocery store built with **Python 3.12**, **Aiogram 3**, **PostgreSQL** (async SQLAlchemy), **Alembic**, **FSM**, and **Docker**.

---

## 🚀 Xususiyatlari / Features

### 👤 Foydalanuvchi qismi (User Side)
- **Katalog & Mahsulotlar:** Dinamik kategoriyalar va mahsulotlar ro'yxati (paginatsiya bilan).
- **Mahsulot Kartasi:** Rasm, narx, tavsif va sonini sozlash (inline minus/plus tugmalari).
- **Savatcha Tizimi (Cart):** Savatchaga qo'shish, sonini yangilash, o'chirish va umumiy hisob-kitob.
- **Buyurtma berish (Checkout Flow):** FSM orqali manzil, telefon raqami (kontakt yuborish), to'lov turi va tasdiqlash.
- **To'lov Turlari:** Naqd, Click, Payme (sozlamalardan yoqish/o'chirish imkoniyati).
- **Admin Guruhga Xabar:** Har bir yangi buyurtma avtomatik tarzda maxsus admin guruhiga yuboriladi va u yerdan turib statusni o'zgartirish mumkin.

### 🔐 Admin Panel (Admin Panel)
- **Xavfsiz Kirish:** Admin profilga kirish uchun username va hashed password talab qilinadi (bcrypt orqali).
- **Kategoriyalar Boshqaruvi:** Kategoriya qo'shish, tahrirlash (nom, emoji), o'chirish.
- **Tovarlar Boshqaruvi:** Yangi tovar qo'shish (kategoriya tanlash, nomi, tavsifi, narxi, soni va rasm), tahrirlash, o'chirish, qidiruv tizimi va paginatsiya.
- **Buyurtmalar Boshqaruvi:** Barcha buyurtmalarni ro'yxati, batafsil ma'lumot va statuslar (NEW, ACCEPTED, DELIVERING, COMPLETED, CANCELED) o'zgartirish.
- **Statistika:** Bugungi buyurtmalar va savdo, oylik savdo, umumiy foydalanuvchilar va eng ko'p sotilgan mahsulotlar.
- **Sozlamalar:** Yetkazib berish narxini sozlash, to'lov turlarini yoqish/o'chirish, adminlar ro'yxati va yangi admin qo'shish.
- **Xabar yuborish (Broadcast System):** Barcha bot foydalanuvchilariga rasm, video yoki matnli xabar yuborish.

---

## 📁 Loyiha Tuzilishi / Project Structure

```
supermarket-bot/
├── config/                  # Configuration settings
│   └── settings.py
├── database/                # Database engine & base
│   ├── engine.py
│   └── base.py
├── models/                  # SQLAlchemy models
│   ├── user.py
│   ├── admin.py
│   ├── category.py
│   ├── product.py
│   ├── cart.py
│   ├── order.py
│   └── settings.py
├── services/                # Business logic layer
│   ├── user.py
│   ├── admin.py
│   ├── category.py
│   └── ...
├── handlers/                # Telegram message handlers
│   ├── user/
│   └── admin/
├── keyboards/               # Inline & Reply keyboards
│   ├── user_kb.py
│   └── admin_kb.py
├── middlewares/             # Database session & rate limit
├── states/                  # FSM states
├── utils/                   # Logging & formatting helper helpers
├── alembic/                 # Alembic migrations
├── docker-compose.yml       # Production deployment
├── Dockerfile               # Container builder
├── bot.py                   # App entrypoint
└── README.md
```

---

## 🛠 O'rnatish va Ishga tushirish (Installation & Run)

### 1. Loyihani yuklab olish va Venv yaratish

```bash
git clone <repository_url> supermarket-bot
cd supermarket-bot

python -m venv venv
source venv/bin/activate  # Windows uchun: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. .env Sozlamalari (.env Configuration)

`.env.example` faylini nusxalab `.env` ga o'zgartiring va sozlang:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/supermarket_bot
ADMIN_IDS=[123456789]
ADMIN_GROUP_ID=-1001234567890
```

### 3. Migratsiyalarni amalga oshirish (Database Migrations)

Alembic orqali ma'lumotlar bazasini yangilang:

```bash
alembic upgrade head
```

### 4. Mahalliy ishga tushirish (Run Locally)

```bash
python bot.py
```

---

## 🐳 Docker orqali ishga tushirish (Docker Deployment)

Docker va Docker Compose o'rnatilgan bo'lsa, loyihani birgina buyruq orqali to'liq ishga tushirish mumkin (PostgreSQL bazasi bilan birga):

```bash
# Docker Compose orqali ishga tushirish
docker-compose up --build -d
```

Ushbu buyruq PostgreSQL bazasini yuklaydi, sog'lomligini tekshiradi va bot konteynerini ishga tushiradi.

---

## 🛡 Xavfsizlik va Kengayuvchanlik (Security & Scalability)

- **SQL Injection:** SQLAlchemy ORM parametrlashtirilgan so'rovlari tufayli SQL injection xavfi yo'q.
- **Admin Authentication:** Admin panel maxsus parol xeshlash tizimi (`bcrypt`) orqali himoyalangan.
- **Rate Limiting:** `ThrottleMiddleware` orqali botni ortiqcha so'rovlar bilan yuklashdan (flood) saqlaydi.
- **Async:** Barcha ma'lumotlar bazasi va tarmoq so'rovlari 100% asinxron tarzda bajariladi, bu botning tezkor ishlashini ta'minlaydi.
