# Lyorna — mağaza botu

Rusiyada işləyən vitrin botu. Müştəri dili rusca. Mağaza adı: **Lyorna**.

İçində:
- 3 addımlı intro
- 7 zal: geyim, ayaqqabı, aksesuar, ev, gözəllik, texnika, hədiyyə
- 17 nümunə mal, şəkil, qiymət (₽), qalıq
- səbət, miqdar, sifariş (telefon, şəhər, ünvan, ödəniş)
- admin zalı: ad, qiymət, şəkil, təsvir, qalıq, zal, gizlət/göstər, yeni mal, sifariş statusu

Ödəniş avtomatik kart deyil: köçürmə və ya alarkən. Admin statusu dəyişəndə müştəriyə mesaj gedir.

## Quraşdırma

1. Telegramda @BotFather → `/newbot` → tokeni götür.
2. Öz id-ni öyrən: @userinfobot.
3. Bu qovluqda:

```bash
cd lyorna-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

4. `.env`:

```
BOT_TOKEN=123456:ABC...
ADMIN_IDS=senin_id
```

Bir neçə admin: `111,222`

5. İşə sal:

```bash
python bot.py
```

`/start` — intro və zal. `/admin` — yalnız admin.

Şəkil dəyişmək: admin → mal → Фото → şəkil göndər və ya link.
Yeni mal: admin → Новый товар.

Kompüter bağlı olanda bot dayanır. Daimi iş üçün VPS və ya Railway-də eyni əmri `python bot.py` kimi saxla. Tokeni çata yapışdırma, yalnız `.env`-ə yaz.
