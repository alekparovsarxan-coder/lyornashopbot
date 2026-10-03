# Lyorna botunu işə salmaq

Tokeni bu söhbətə yapışdırma. Yalnız Railway-in Variables yerinə yaz.

## 1. Telegramda bot yarat

1. Telegramı aç.
2. Axtarışa yaz: `@BotFather`
3. `/newbot` göndər.
4. Ad: `Lyorna`
5. Username: `lyorna_shop_bot` kimi, sonunda mütləq `bot` olsun. Tutulubsa başqa ad yaz.
6. BotFather sənə uzun sətir verəcək. Bu **token**dir. Nümunə: `7123456789:AAH...`
7. Onu qeyd dəftərinə kopyala. Heç kimə göndərmə.

## 2. Öz admin nömrəni götür

1. Axtarışa yaz: `@userinfobot`
2. `/start` bas.
3. `Id:` yazılan rəqəmi kopyala. Məsələn `584920174`
4. Bu sənin admin id-indir. Panel yalnız bu id-ə açılacaq.

## 3. Kodu GitHub-a qoy

1. https://github.com aç, hesab yarat.
2. Sağ yuxarı `+` → `New repository`
3. Ad: `lyorna-bot` → Public → `Create repository`
4. `uploading an existing file` yazısına bas.
5. Bu arxivin içindəki faylları çıxart və hamısını ora at: `bot.py`, `db.py`, `config.py`, `keyboards.py`, `texts.py`, `requirements.txt`, `railway.toml`, `Procfile`, `.env.example`
6. `.env` faylını GitHub-a atma. Token orada qalmamalıdır.
7. `Commit changes`

## 4. Railway-ə qoş

1. https://railway.com aç.
2. `Login` → GitHub ilə gir.
3. `New Project` → `Deploy from GitHub repo` → `lyorna-bot` seç.
4. Layihə açılınca servisə gir.
5. `Variables` düyməsi.
6. İki sətir əlavə et, adları eyni belə yaz:

```
BOT_TOKEN
```
dəyər: BotFather-dən aldığın uzun sətir

```
ADMIN_IDS
```
dəyər: userinfobot-dan aldığın rəqəm

7. `Deploy` və ya `Redeploy` bas.
8. `Deployments` yaşıl olanda bot işləyir.

Start əmri artıq `python bot.py`dir. Ünvan (domain) lazım deyil. Bu bot sayt deyil, Telegrama özü yazır.

## 5. Yoxla

1. Telegramda öz botunun adını axtar.
2. `/start` bas. 5 intro gəlməlidir, sonra düymələr.
3. `/admin` bas. Azərbaycan dilində panel açılmalıdır.
4. Panel açılmırsa `ADMIN_IDS` səhvdir. Yenidən yaz, redeploy et.

## Paneldə nə edirsən

- Mallar: mala bas → Ad, Qiymət, Şəkil, Qalıq, Təsvir, Zal, Gizlət, Sil
- Qiymətə yalnız rəqəm yaz: `12900`
- Şəkil: bota şəkil göndər, ya da link
- Yeni mal: zal → ad → təsvir → qiymət → şəkil → qalıq
- Sifarişlər: İşdə / Göndərildi / Bağlandı / Ləğv. Müştəriyə özü yazır.

Kompüteri bağlamaq botu söndürmür. Bot Railway-də qalır.
