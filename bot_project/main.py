import asyncio
from datetime import datetime, timezone
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardRemove
import httpx

CRYPTOBOT_API_TOKEN = "414912:AAOxcFiur4XxoxAigHexDyeHGhq3NLT7ArS"
CRYPTOBOT_BASE_URL = "https://pay.crypt.bot/414912:AAOxcFiur4XxoxAigHexDyeHGhq3NLT7ArS"
BOT_TOKEN = "7964452516:AAE6IQxljgPHcQ34jv_rJI3oIvPgQac4C-s"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()

user_languages = {}
valid_promocodes = {"SUNLIGHTFREE"}
used_promocodes = set()
user_daylight = {}
promocode_input_enabled = set()
user_balance = {}
user_pending_invoice = {}



def get_language(user_id: int) -> str:
    return user_languages.get(user_id, "English")

def set_language(user_id: int, lang: str):
    user_languages[user_id] = lang

def get_title_by_daylight(daylight: float) -> str:
    if daylight > 1.0:
        return "High"
    elif daylight > 0.10:
        return "Middle"
    else:
        return "New"

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await send_welcome(message)

async def create_crypto_invoice(user_id: int, amount: float, description: str) -> tuple[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CRYPTOBOT_API_TOKEN}"
    }
    payload = {
        "asset": "USDT",
        "amount": f"{amount:.2f}",
        "description": description,
        "hidden_message": f"Payment for user {user_id}",
        "paid_btn_name": "callback",
        "paid_btn_url": "https://t.me/DDNetHellBot"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CRYPTOBOT_BASE_URL}/createInvoice", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["result"]["pay_url"], data["result"]["invoice_id"]



@dp.message(F.text == "/myaccount")
async def cmd_myaccount(message: Message):
    await send_account_info(message)

@dp.message(F.text == "/configs")
async def cmd_configs(message: Message):
    await send_configs_menu(message)

async def send_welcome(message: Message):
    now = datetime.now(timezone.utc)
    print(f"[{now.isoformat()}] /start от пользователя {message.from_user.id}")

    lang = get_language(message.from_user.id)
    text = (
        "*DDNetHell — Bot for purchasing DDNet configs*\n\n"
        "👋 Welcome! I'm DDNetHell, your assistant for quick and easy purchase of unique DDNet configs. "
        "Choose and buy custom configs crafted with care to enhance your gaming experience. "
        "Simple, fast, and secure!"
    ) if lang == "English" else (
        "*DDNetHell — Бот для покупки DDNet конфигов*\n\n"
        "👋 Привет! Я DDNetHell, твой помощник для быстрого и удобного приобретения уникальных DDNet конфигов. "
        "Выбирай и покупай кастомные конфиги, созданные с заботой для улучшения твоего игрового опыта. "
        "Просто, быстро и надежно!"
    )

    control_panel_text = "Control Panel" if lang == "English" else "Панель управления"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="👤 Personal account", callback_data="account")
    keyboard.button(text="👥 Links and more", callback_data="links")
    keyboard.button(text=f"⚙ {control_panel_text}", callback_data="control_panel")
    keyboard.adjust(1)

    photo = FSInputFile("Welcome.jpg")
    await message.answer_photo(photo=photo, caption=text, reply_markup=keyboard.as_markup())

async def send_account_info(target: Message | CallbackQuery):
    user = target.from_user
    username = user.username or user.full_name or "Unknown"
    user_id = user.id

    lang = get_language(user_id)
    daylight = user_daylight.get(user_id, 0.0)
    title = get_title_by_daylight(daylight)
    lang_display = "English" if lang == "English" else "Русский"

    text = (
        f"🗣 Hello, {username}! [ID: {user_id}]\n\n"
        f"👤 *Name:* **{username}**\n"
        f"👁 *Title:* **{title}**\n"
        f"☀️ *Daylight:* _{daylight:.2f}$_\n"
        f"🇺🇸/🇷🇺 *Language:* _{lang_display}_\n\n"
        f"_Subscription:_ ❌\n\n"
    ) if lang == "English" else (
        f"🗣 Привет, {username}! [ID: {user_id}]\n\n"
        f"👤 *Имя:* **{username}**\n"
        f"👁 *Звание:* **{title}**\n"
        f"☀️ *Daylight:* _{daylight:.2f}$_\n"
        f"🇺🇸/🇷🇺 *Язык:* _{lang_display}_\n\n"
        f"_Подписка:_ ❌\n\n"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💰 Shop" if lang == "English" else "💰 Магазин", callback_data="shop")
    keyboard.button(text="⚙ Configs" if lang == "English" else "⚙ Конфиги", callback_data="configs")
    keyboard.button(text="🏷 Promocode" if lang == "English" else "🏷 Промокод", callback_data="promocode")
    keyboard.button(text="🛠 Support" if lang == "English" else "🛠 Поддержка", callback_data="support")
    keyboard.adjust(2, 1, 1)

    photo = FSInputFile("Account.jpg")
    if isinstance(target, Message):
        await target.answer_photo(photo=photo, caption=text, reply_markup=keyboard.as_markup())
    else:
        await target.message.answer_photo(photo=photo, caption=text, reply_markup=keyboard.as_markup())


@dp.callback_query(F.data == "promocode")
async def cb_promocode(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_language(user_id)

    if user_id in used_promocodes:
        text = "🚫 You have already used a promocode!" if lang == "English" else "🚫 Вы уже использовали промокод!"
        await callback.answer(text, show_alert=True)
        return

    promocode_input_enabled.add(user_id)

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="← Back", callback_data="promocode_back")
    keyboard.adjust(1)

    text = (
        "*🏷 Enter promocode:*\n\n"
        "Send a valid code to get bonuses."
        if lang == "English" else
        "*🏷 Введите промокод:*\n\n"
        "Отправь корректный код, чтобы получить бонусы."
    )
    await callback.message.answer(text, reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "account")
async def cb_account(callback: CallbackQuery):
    await send_account_info(callback)
    await callback.answer()

@dp.callback_query(F.data == "links")
async def cb_links(callback: CallbackQuery):
    lang = get_language(callback.from_user.id)
    await callback.answer("👥 Links and more (coming soon)" if lang == "English" else "👥 Ссылки и другое (скоро будет)", show_alert=True)

@dp.callback_query(F.data == "shop")
async def cb_shop(callback: CallbackQuery):
    lang = get_language(callback.from_user.id)

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💵 $1.00", callback_data="topup_1")
    keyboard.button(text="💵 $3.00", callback_data="topup_3")
    keyboard.button(text="💵 $5.00", callback_data="topup_5")
    keyboard.button(text="💵 $10.00", callback_data="topup_10")
    keyboard.adjust(2)

    text = (
        "💳 *Выберите сумму пополнения:*\nВыберите, на сколько пополнить баланс."
    )

    await callback.message.answer(text, reply_markup=keyboard.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("topup_"))
async def cb_topup(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_language(user_id)
    amount = int(callback.data.split("_")[1])

    pay_url, invoice_id = await create_crypto_invoice(user_id, amount, "Пополнение баланса")
    user_pending_invoice[user_id] = invoice_id  # ✅ сохраняем invoice_id

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🟢 Оплатить через CryptoBot", url=pay_url)
    keyboard.button(text="✅ Я оплатил", callback_data="confirm_payment")
    keyboard.adjust(1, 1)

    text = (
        f"💰 *Пополнение на ${amount:.2f}*\n\n"
        f"1. Перейди по ссылке\n"
        f"2. Оплати в CryptoBot\n"
        f"3. Потом нажми 'Я оплатил'"
    )

    await callback.message.answer(text, reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "confirm_payment")
async def cb_confirm_payment(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_language(user_id)

    invoice_id = user_pending_invoice.get(user_id)
    if not invoice_id:
        await callback.message.answer("❌ Счёт не найден. Попробуйте заново.")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CRYPTOBOT_API_TOKEN}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CRYPTOBOT_BASE_URL}/getInvoices?invoice_ids={invoice_id}", headers=headers)
        response.raise_for_status()
        data = response.json()

        invoice = data["result"][0]
        status = invoice["status"]
        amount = float(invoice["amount"])

        if status == "paid":
            user_daylight[user_id] = user_daylight.get(user_id, 0.0) + amount
            await callback.message.answer(
                f"✅ Оплата подтверждена!\nТеперь у тебя {user_daylight[user_id]:.2f} daylight."
            )
        else:
            await callback.message.answer("❌ Оплата не найдена. Убедитесь, что вы оплатили и попробуйте позже.")


@dp.callback_query(F.data == "support")
async def cb_support(callback: CallbackQuery):
    lang = get_language(callback.from_user.id)
    await callback.answer("🛠 Support (coming soon)" if lang == "English" else "🛠 Поддержка (скоро будет)", show_alert=True)

@dp.callback_query(F.data == "configs")
async def send_configs_menu(target: Message | CallbackQuery):
    lang = get_language(target.from_user.id)

    text = (
        "⚙ *Configs:*\nChoose one of the configs below. All are optimized for DDNet and ready to use."
        if lang == "English" else
        "⚙ *Configs:*\nВыбери один из конфигов ниже. Все они оптимизированы для DDNet и готовы к использованию."
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="1 Config", callback_data="config_1")
    keyboard.button(text="2 Config", callback_data="config_2")
    keyboard.button(text="3 Config", callback_data="config_3")
    keyboard.button(text="4 Config", callback_data="config_4")
    keyboard.button(text="<-", callback_data="configs_prev")
    keyboard.button(text="->", callback_data="configs_next")
    keyboard.adjust(2, 2, 2)

    photo = FSInputFile("Configs.jpg")

    if isinstance(target, Message):
        await target.answer_photo(photo=photo, caption=text, reply_markup=keyboard.as_markup())
    else:
        await target.message.answer_photo(photo=photo, caption=text, reply_markup=keyboard.as_markup())
        await target.answer()


# 👇 Универсальная функция показа первого конфига
async def send_config_1(callback: CallbackQuery):
    text = (
        "☀️ <b>Kimi no Asa</b> – <i>Your morning</i>\n"
        "💰 <b>Price</b> – <i>0.1$</i> (Pay once, keep forever)\n\n"
        "✔ <b>Optimized for every DDNet versions</b>\n"
        "✔ <b>Clean interface & fast binds</b>\n"
        "✔ <b>No ads, no subscriptions</b>\n\n"
        "<blockquote>Paid version 1.6</blockquote>\n\n"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="→ Get now", callback_data="buy_config_1")
    keyboard.button(text="→ About & previews", callback_data="preview_config_1")
    keyboard.button(text="→ How to install", callback_data="install_config_1")
    keyboard.button(text="← Back", callback_data="back_to_configs")
    keyboard.adjust(1)

    photo = FSInputFile("Config1.jpg")
    await callback.message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

# 👇 При открытии первого конфига из меню конфигов
@dp.callback_query(F.data == "config_1")
async def cb_config_1(callback: CallbackQuery):
    await callback.message.delete()
    await send_config_1(callback)
    await callback.answer()

# 👇 Показываем описание конфига
@dp.callback_query(F.data == "preview_config_1")
async def preview_config_1(callback: CallbackQuery):
    await callback.message.delete()

    text = (
        "<b>🌅 Kimi no Asa — Your morning.</b>\n\n"
        "Kimi no Asa is a handcrafted DDNet config made entirely from scratch.\n"
        "Created by @DDNetHell in just 2 hours — no templates, no copy-paste, just pure logic, flow, and soul.\n\n"
        "<b>🔧 What’s inside:</b>\n\n"
        "→ Fully optimized for all DDNet versions\n"
        "→ Clean HUD with no distractions\n"
        "→ Minimal visuals — full control\n"
        "→ Works flawlessly with keyboard\n"
        "→ No useless scripts — only what you really need\n"
        "→ Lightweight for smooth FPS even on low-end setups\n\n"
        "🌅 Inspired by Kyoto mornings, anime vibes, and old-school.\n"
        "Every detail was tested and fine-tuned for pure movement and focus.\n\n"
        "<i>“This isn’t just a config — it’s your new starting point.”</i>\n\n"
        "<blockquote>"
        "📄 Made by: DDNetHell\n"
        "📦 Version: 1.6\n"
        "🔨 Used programmes: Visual Studio Code; Photoshop; Notebook.\n"
        "📌 Release type: One-time / No updates / No ads / No bullshit"
        "</blockquote>"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="← Back", callback_data="back_to_config_1")
    keyboard.adjust(1)

    photo = FSInputFile("Config1.jpg")
    await callback.message.answer_photo(photo=photo, caption=text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "buy_config_1")
async def buy_config_1(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_language(user_id)
    balance = user_daylight.get(user_id, 0.0)  # ЗАМЕНА!
    price = 0.10

    if balance >= price:
        user_daylight[user_id] = balance - price  # ЗАМЕНА!

        text = (
            f"✅ *Покупка успешна!*\n\n"
            f"_Вы приобрели:_ `Kimi no Asa`\n"
            f"_Цена:_ **${price:.2f}**\n"
            f"_Ваш daylight:_ **{user_daylight[user_id]:.2f}**\n\n"
            f"_Конфиг будет отправлен в ближайшее время._"
        )

        await callback.message.answer(text)

        # Отправка архива
        await callback.message.answer_document(FSInputFile("KimiNoAsa.zip"))  # ✅ Не забудь положить этот файл в ту же папку

    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💳 Refill balance", callback_data="shop")
        keyboard.button(text="🔗 Pay via CryptoBot", url="https://t.me/CryptoBot?start=PAY_KIMINOASA")
        keyboard.adjust(1, 1)

        text = (
            f"❌ *Недостаточно средств!*\n\n"
            f"_Цена:_ **${price:.2f}**\n"
            f"_Ваш daylight:_ **{balance:.2f}**\n\n"
            f"_Пополните баланс или оплатите через CryptoBot._"
        )
        await callback.message.answer(text, reply_markup=keyboard.as_markup())

    await callback.answer()


# 👇 Кнопка назад из описания в сам конфиг
@dp.callback_query(F.data == "back_to_config_1")
async def back_to_config_1(callback: CallbackQuery):
    await callback.message.delete()
    await send_config_1(callback)
    await callback.answer()

# 👇 Кнопка назад из конфига в меню конфигов
@dp.callback_query(F.data == "back_to_configs")
async def back_to_configs(callback: CallbackQuery):
    await callback.message.delete()
    await send_configs_menu(callback)
    await callback.answer()


# 📦 Улучшенная инструкция установки Kimi no Asa
@dp.callback_query(F.data == "install_config_1")
async def install_config_1(callback: CallbackQuery):
    await callback.message.delete()
    lang = get_language(callback.from_user.id)

    if lang == "English":
        text = (
            "*🧩 Installation Guide for Kimi no Asa*\n"
            "────────────────────\n\n"
            "Welcome to the setup tutorial for the **Kimi no Asa** config.\n"
            "Follow these steps to install it correctly and enjoy the perfect DDNet experience:\n\n"
            "📥 *1.* Download the archive: `KimiNoAsa.rar`\n"
            "🖥 *2.* Press `Win + R` on your keyboard\n"
            "💬 *3.* Type `%AppData%` and press Enter\n"
            "📂 *4.* Find the folder named `DDNet`\n"
            "📦 *5.* Extract and move all files from the archive into that folder\n"
            "🎮 *6.* Start the game\n"
            "🌐 *7.* Join any DDNet server\n"
            "⌨️ *8.* Press `F1` to open console\n"
            "⚙️ *9.* Type: `exec KimiNoAsa.cfg`\n\n"
            "💡 *Tip:* If you renamed the `.cfg` file, use the name you gave it.\n\n"
            "_Enjoy clean visuals, fast binds, and focused gameplay!_\n"
            "Made with ❤️ by @DDNetHell"
        )
    else:
        text = (
            "*🧩 Инструкция по установке Kimi no Asa*\n"
            "────────────────────\n\n"
            "Добро пожаловать в гайд по установке конфига **Kimi no Asa**.\n"
            "Следуй этим шагам, чтобы правильно установить и наслаждаться идеальной игрой в DDNet:\n\n"
            "📥 *1.* Скачай архив: `KimiNoAsa.rar`\n"
            "🖥 *2.* Нажми `Win + R`\n"
            "💬 *3.* Введи `%AppData%` и нажми Enter\n"
            "📂 *4.* Найди папку `DDNet`\n"
            "📦 *5.* Распакуй и перемести все файлы из архива в эту папку\n"
            "🎮 *6.* Запусти игру\n"
            "🌐 *7.* Зайди на любой сервер DDNet\n"
            "⌨️ *8.* Нажми `F1`, чтобы открыть консоль\n"
            "⚙️ *9.* Напиши: `exec KimiNoAsa.cfg`\n\n"
            "💡 *Совет:* Если ты переименовал `.cfg` файл — используй своё имя.\n\n"
            "_Наслаждайся чистым интерфейсом, быстрыми биндами и фокусом на движении!_\n"
            "Сделано с ❤️ от @DDNetHell"
        )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="← Back", callback_data="back_to_config_1_from_install")
    keyboard.adjust(1)

    await callback.message.answer(text, reply_markup=keyboard.as_markup())

# ⬅ Назад из туториала в сам конфиг
@dp.callback_query(F.data == "back_to_config_1_from_install")
async def back_to_config_1_from_install(callback: CallbackQuery):
    await callback.message.delete()
    await send_config_1(callback)
    await callback.answer()



# 📖 /guides — улучшенный общий гайд по установке конфигов
@dp.message(F.text == "/guide")
async def cmd_guides(message: Message):
    lang = get_language(message.from_user.id)

    if lang == "English":
        text = (
            "*📖 How to install any DDNet Config:*\n"
            "────────────────────\n\n"
            "Use this step-by-step guide to install any config (including paid ones).\n\n"
            "📥 *1.* Download the config archive (.rar or .zip)\n"
            "🖥 *2.* Press `Win + R` on your keyboard\n"
            "💬 *3.* Type `%AppData%` and press Enter\n"
            "📂 *4.* Open the `DDNet` folder (create it if it doesn't exist)\n"
            "📦 *5.* Unpack the archive and move all files into the `DDNet` folder\n"
            "🎮 *6.* Launch DDNet\n"
            "🌐 *7.* Join any server\n"
            "⌨️ *8.* Press `F1` to open the console\n"
            "⚙️ *9.* Type: `exec your_config_name.cfg`\n\n"
            "💡 Replace `your_config_name` with the actual filename.\n\n"
            "_Enjoy clean gameplay, optimized binds, and smooth movement!_\n"
            "Made with ❤️ by @DDNetHell"
        )
    else:
        text = (
            "*📖 Как установить любой DDNet конфиг:*\n"
            "────────────────────\n\n"
            "Следуй этому пошаговому гайду, чтобы установить любой конфиг (включая платные).\n\n"
            "📥 *1.* Скачай архив конфига (.rar или .zip)\n"
            "🖥 *2.* Нажми `Win + R` на клавиатуре\n"
            "💬 *3.* Введи `%AppData%` и нажми Enter\n"
            "📂 *4.* Открой папку `DDNet` (создай её, если нет)\n"
            "📦 *5.* Распакуй архив и перемести все файлы в папку `DDNet`\n"
            "🎮 *6.* Запусти DDNet\n"
            "🌐 *7.* Зайди на любой сервер\n"
            "⌨️ *8.* Нажми `F1`, чтобы открыть консоль\n"
            "⚙️ *9.* Напиши: `exec имя_конфига.cfg`\n\n"
            "💡 Замени `имя_конфига` на настоящее имя файла.\n\n"
            "_Наслаждайся чистым интерфейсом, удобными биндами и плавным движением!_\n"
            "Сделано с ❤️ от @DDNetHell"
        )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="← Back", callback_data="back_to_account_from_guides")
    keyboard.adjust(1)

    await message.answer(text, reply_markup=keyboard.as_markup())

# ⬅ Назад из /guides в личный аккаунт
@dp.callback_query(F.data == "back_to_account_from_guides")
async def back_to_account_from_guides(callback: CallbackQuery):
    await callback.message.delete()
    await send_account_info(callback)
    await callback.answer()

@dp.callback_query(F.data.in_({"config_2", "config_3", "config_4"}))
async def cb_config_placeholder(callback: CallbackQuery):
    await callback.answer("⏳ Coming soon...", show_alert=True)

@dp.callback_query(F.data == "promocode")
async def cb_promocode(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_language(user_id)

    if user_id in used_promocodes:
        text = "🚫 You have already used a promocode!" if lang == "English" else "🚫 Вы уже использовали промокод!"
        await callback.answer(text, show_alert=True)
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="← Back", callback_data="promocode_back")
    keyboard.adjust(1)

    text = (
        "*🏷 Enter promocode:*\n\n"
        "Send a valid code to get bonuses."
        if lang == "English" else
        "*🏷 Введите промокод:*\n\n"
        "Отправь корректный код, чтобы получить бонусы."
    )
    await callback.message.answer(text, reply_markup=keyboard.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "promocode_back")
async def cb_promocode_back(callback: CallbackQuery):
    user_id = callback.from_user.id
    promocode_input_enabled.discard(user_id)
    await callback.message.delete()
    await callback.answer()

@dp.message()
async def handle_promocode_input(message: Message):
    user_id = message.from_user.id
    lang = get_language(user_id)
    code = message.text.strip()

    if user_id not in promocode_input_enabled:
        return

    if code in valid_promocodes:
        if user_id in used_promocodes:
            text = (
                "🚫 *Oops! You've already used a promocode.*\n\n"
                "_Only one gift per user — make it count!_ 🎁"
                if lang == "English" else
                "🚫 *Упс! Вы уже использовали промокод.*\n\n"
                "_Один подарок на пользователя — используйте с умом!_ 🎁"
            )
        else:
            used_promocodes.add(user_id)
            user_daylight[user_id] = user_daylight.get(user_id, 0.0) + 1.0
            text = (
                "✅ *Promocode successfully activated!* 🎉\n\n"
                "_You just gained_ **+1.0** _daylight ☀️_"
                if lang == "English" else
                "✅ *Промокод успешно активирован!* 🎉\n\n"
                "_Вы получили_ **+1.0** _daylight ☀️_"
            )
        promocode_input_enabled.discard(user_id)
    else:
        text = (
            "❌ *Invalid promocode entered.*\n\n"
            "_Double-check the code and try again, or press_ `← Back` _to return._"
            if lang == "English" else
            "❌ *Введён неверный промокод.*\n\n"
            "_Проверь правильность кода и попробуй снова, либо нажми_ `← Назад` _для возврата._"
        )

    await message.answer(text, reply_markup=ReplyKeyboardRemove())


@dp.callback_query(F.data == "control_panel")
async def cb_control_panel(callback: CallbackQuery):
    lang = get_language(callback.from_user.id)
    caption = "*Control Panel*\n\nChoose your language / Выбери язык:" if lang == "English" else "*Панель управления*\n\nChoose your language / Выбери язык:"
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🇺🇸 English" if lang == "English" else "🇺🇸 Английский", callback_data="lang_English")
    keyboard.button(text="🇷🇺 Russian" if lang == "English" else "🇷🇺 Русский", callback_data="lang_Russian")
    keyboard.adjust(1)
    photo = FSInputFile("ControlPanel.jpg")
    await callback.message.answer_photo(photo=photo, caption=caption, reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("lang_"))
async def cb_lang_change(callback: CallbackQuery):
    chosen_lang = callback.data.split("_")[1]
    set_language(callback.from_user.id, "Russian" if chosen_lang == "Russian" else "English")
    await callback.message.delete()
    lang = get_language(callback.from_user.id)
    await callback.message.answer("Language changed to English ✅" if lang == "English" else "Язык изменен на русский ✅")
    await callback.answer()

async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
