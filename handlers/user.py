from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.deep_linking import decode_payload

# Импортируем наши функции для работы с базой
from database.requests import link_telegram_id, get_user_by_tg_id

router = Router()

def get_language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])

# --- ЛОГИКА ВХОДА ПО УМНОЙ ССЫЛКЕ ---

@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject):
    args = command.args
    try:
        # 1. Расшифровываем ID из ссылки
        db_user_id = int(decode_payload(args))
        
        # 2. Пытаемся привязать Telegram ID к этой карточке в базе
        user = await link_telegram_id(db_user_id, message.from_user.id)
        
        if user:
            # Если все успешно, предлагаем выбрать язык
            await message.answer(
                f"👋 Здравствуйте, <b>{user.full_name}</b>!\n\n"
                "Рады видеть вас в нашем боте.\n"
                "Пожалуйста, выберите язык интерфейса:\n\n"
                "Iltimos, tilni tanlang:\n"
                "Please choose a language:",
                reply_markup=get_language_kb(),
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Извините, эта ссылка больше не действительна или была использована.")
            
    except Exception as e:
        await message.answer("❌ Произошла ошибка при активации ссылки. Обратитесь к администратору.")

# --- ОБЫЧНЫЙ СТАРТ (Если юзер просто зашел в бот) ---

@router.message(CommandStart())
async def cmd_start_normal(message: Message):
    # Проверяем, есть ли этот человек уже в нашей базе
    user = await get_user_by_tg_id(message.from_user.id)
    
    if user:
        # Если он уже наш клиент, просто здороваемся
        await message.answer(f"Приветствуем снова, <b>{user.full_name}</b>!\nВоспользуйтесь меню или командой /profile.")
    else:
        # Если посторонний — вежливо отказываем
        await message.answer(
            "🔒 <b>Доступ ограничен</b>\n\n"
            "Этот бот предназначен только для клиентов студии и учеников.\n"
            "Для получения доступа обратитесь к вашему мастеру."
        )

# --- ВЫБОР ЯЗЫКА ---

@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery):
    lang_code = callback.data.split("_")[1] 
    
    # TODO: Здесь мы добавим функцию update_user_language в requests.py
    
    responses = {
        "ru": "✅ Язык установлен! Теперь вы будете получать уведомления на русском.\nИспользуйте /profile для проверки остатка.",
        "uz": "✅ Til o'rnatildi! Endi siz xabarlarni o'zbek tilida olasiz.\nQoldiqni tekshirish uchun /profile dan foydalaning.",
        "en": "✅ Language set! You will now receive notifications in English.\nUse /profile to check your balance."
    }
    
    await callback.message.edit_text(responses.get(lang_code, "✅ Done!"), parse_mode="HTML")
    await callback.answer()
