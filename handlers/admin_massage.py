from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.deep_linking import create_start_link

# 🔥 Импортируем все необходимые функции из базы данных
from database.requests import create_client_with_package, get_active_users_by_type, deduct_sessions

router = Router()

# --- FSM (Машина состояний) для добавления клиента ---
class AddClientForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_package = State()

# ==========================================
# 1. ДОБАВЛЕНИЕ КЛИЕНТА (Уже работает с БД)
# ==========================================

@router.callback_query(F.data == "msg_add_client")
async def start_adding_client(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 <b>Добавление нового VIP-клиента</b>\n\n"
        "Введите Имя и Фамилию клиента:",
        parse_mode="HTML"
    )
    await state.set_state(AddClientForm.waiting_for_name)
    await callback.answer()

@router.message(AddClientForm.waiting_for_name)
async def process_client_name(message: Message, state: FSMContext):
    await state.update_data(client_name=message.text)
    
    packages_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5 сеансов", callback_data="pkg_5")],
        [InlineKeyboardButton(text="10 сеансов", callback_data="pkg_10")],
        [InlineKeyboardButton(text="15 сеансов (VIP)", callback_data="pkg_15")]
    ])
    
    await message.answer(
        f"Имя <b>{message.text}</b> сохранено.\n"
        f"Выберите пакет сеансов массажа:",
        reply_markup=packages_kb,
        parse_mode="HTML"
    )
    await state.set_state(AddClientForm.waiting_for_package)

@router.callback_query(AddClientForm.waiting_for_package, F.data.startswith("pkg_"))
async def process_client_package(callback: CallbackQuery, state: FSMContext, bot: Bot):
    sessions_count = int(callback.data.split("_")[1])
    data = await state.get_data()
    client_name = data['client_name']
    
    # Сохраняем клиента в БД
    db_user_id = await create_client_with_package(
        full_name=client_name, 
        package_type="massage", 
        total_sessions=sessions_count
    )
    
    # Генерация зашифрованной ссылки
    link = await create_start_link(bot, str(db_user_id), encode=True)
    
    await callback.message.edit_text(
        f"✅ <b>Карточка клиента успешно создана!</b>\n\n"
        f"👤 Клиент: <b>{client_name}</b>\n"
        f"🎟 Пакет: <b>{sessions_count} сеансов</b>\n\n"
        f"🔗 <b>Ссылка для клиента:</b>\n{link}\n\n"
        f"<i>Отправьте эту ссылку клиенту. Когда он перейдет по ней, бот автоматически его узнает.</i>",
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()

# ==========================================
# 2. СПИСАНИЕ СЕАНСОВ (Теперь работает с БД!)
# ==========================================

@router.callback_query(F.data == "msg_deduct")
async def show_clients_for_deduction(callback: CallbackQuery):
    # Достаем из БД всех, у кого есть активный пакет массажа
    users = await get_active_users_by_type("massage")
    
    if not users:
        # Если база пустая или все пакеты потрачены
        await callback.message.edit_text(
            "🤷‍♀️ Активных клиентов массажа пока нет.\nДобавьте новых через меню.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_massage")]
            ])
        )
        return

    # Динамически создаем кнопки для каждого клиента
    kb_buttons = []
    for user in users:
        # Ищем именно активный пакет массажа у этого юзера
        active_pkg = next((p for p in user.packages if p.package_type == "massage" and p.status == "active"), None)
        if active_pkg:
            remaining = active_pkg.total_sessions - active_pkg.used_sessions
            # Создаем кнопку с именем и остатком (например: "👤 Иван Иванов (остаток: 5)")
            kb_buttons.append([InlineKeyboardButton(
                text=f"👤 {user.full_name} (остаток: {remaining})", 
                callback_data=f"deduct_user_{user.id}"
            )])
            
    # Добавляем кнопку "Назад" в самый низ
    kb_buttons.append([InlineKeyboardButton(text="🔙 Назад в меню массажа", callback_data="admin_massage")])
    
    await callback.message.edit_text(
        "👇 Выберите клиента для списания сеанса:", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    )

@router.callback_query(F.data.startswith("deduct_user_"))
async def confirm_deduction(callback: CallbackQuery):
    user_id = callback.data.split("_")[2]
    
    # Кнопки для выбора количества списываемых сеансов (ведут на process_dec)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 сеанс", callback_data=f"process_dec_{user_id}_1"),
            InlineKeyboardButton(text="2 сеанса", callback_data=f"process_dec_{user_id}_2")
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="msg_deduct")]
    ])
    
    await callback.message.edit_text(f"Сколько сеансов списать?", reply_markup=kb)

@router.callback_query(F.data.startswith("process_dec_"))
async def process_deduction(callback: CallbackQuery):
    # Достаем ID пользователя и количество сеансов из скрытых данных кнопки
    data_parts = callback.data.split("_")
    user_id = int(data_parts[2])
    amount = int(data_parts[3])
    
    # Списываем сеансы в базе данных
    result = await deduct_sessions(user_id=user_id, package_type="massage", amount_to_deduct=amount)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку клиентов", callback_data="msg_deduct")]
    ])
    
    if result["status"] == "success":
        text = f"✅ <b>Успешно списано: {amount} сеанс(а).</b>\n\nОстаток: <b>{result['remaining']}</b>"
        if result["completed"]:
            text += "\n🎉 <i>Пакет полностью использован (статус изменен на 'Завершен').</i>"
    else:
        text = f"❌ Ошибка: {result['message']}"
        
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
