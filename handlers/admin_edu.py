from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.deep_linking import create_start_link

from database.requests import create_client_with_package, get_active_users_by_type, deduct_sessions

router = Router()

class AddStudentForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_program = State()

# Главное меню обучения
@router.callback_query(F.data == "admin_edu")
async def process_edu_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ученика", callback_data="edu_add_student")],
        [InlineKeyboardButton(text="📉 Списать занятие", callback_data="edu_deduct")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ])
    await callback.message.edit_text("🎓 <b>Управление обучением</b>", reply_markup=kb, parse_mode="HTML")

# --- ДОБАВЛЕНИЕ ---
@router.callback_query(F.data == "edu_add_student")
async def start_adding_student(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Введите Имя и Фамилию ученика:")
    await state.set_state(AddStudentForm.waiting_for_name)

@router.message(AddStudentForm.waiting_for_name)
async def process_student_name(message: Message, state: FSMContext):
    await state.update_data(student_name=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 месяц (12)", callback_data="prog_12")],
        [InlineKeyboardButton(text="3 месяца (37)", callback_data="prog_37")],
        [InlineKeyboardButton(text="6 месяцев (75)", callback_data="prog_75")]
    ])
    await message.answer(f"Выберите программу для <b>{message.text}</b>:", reply_markup=kb, parse_mode="HTML")
    await state.set_state(AddStudentForm.waiting_for_program)

@router.callback_query(AddStudentForm.waiting_for_program, F.data.startswith("prog_"))
async def save_student(callback: CallbackQuery, state: FSMContext, bot: Bot):
    count = int(callback.data.split("_")[1])
    data = await state.get_data()
    db_id = await create_client_with_package(data['student_name'], "education", count)
    link = await create_start_link(bot, str(db_id), encode=True)
    
    await callback.message.edit_text(
        f"✅ Ученик добавлен!\n👤 <b>{data['student_name']}</b>\n📚 Занятий: {count}\n🔗 Ссылка:\n{link}",
        parse_mode="HTML"
    )
    await state.clear()

# --- СПИСАНИЕ ЗАНЯТИЙ УЧЕНИКАМ ---
@router.callback_query(F.data == "edu_deduct")
async def show_students_list(callback: CallbackQuery):
    students = await get_active_users_by_type("education")
    if not students:
        await callback.answer("Учеников пока нет", show_alert=True)
        return

    buttons = []
    for s in students:
        pkg = next((p for p in s.packages if p.package_type == "education" and p.status == "active"), None)
        if pkg:
            rem = pkg.total_sessions - pkg.used_sessions
            buttons.append([InlineKeyboardButton(text=f"🎓 {s.full_name} ({rem})", callback_data=f"edu_dec_{s.id}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edu")])
    await callback.message.edit_text("👇 Выберите ученика:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("edu_dec_"))
async def process_edu_deduction(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    res = await deduct_sessions(user_id, "education", 1) # Списываем по 1 уроку
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 К списку", callback_data="edu_deduct")]])
    if res["status"] == "success":
        await callback.message.edit_text(f"✅ Занятие списано! Остаток: <b>{res['remaining']}</b>", parse_mode="HTML", reply_markup=kb)
    await callback.answer()
