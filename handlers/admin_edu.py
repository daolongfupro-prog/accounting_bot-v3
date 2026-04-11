from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.deep_linking import create_start_link

# Импортируем клавиатуру и функцию сохранения в базу
from keyboards.admin_kb import get_edu_admin_kb
from database.requests import create_client_with_package

# Создаем тот самый роутер, на который ругался бот
router = Router()

class AddStudentForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_program = State()

# Вход в меню обучения
@router.callback_query(F.data == "admin_edu")
async def process_edu_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎓 <b>Раздел: Обучение массажу</b>\n\n"
        "Выберите действие для управления учениками и расписанием:",
        reply_markup=get_edu_admin_kb(),
        parse_mode="HTML"
    )
    await callback.answer()

# --- ДОБАВЛЕНИЕ УЧЕНИКА ---

@router.callback_query(F.data == "edu_add_student")
async def start_adding_student(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 <b>Новый ученик</b>\n\nВведите Имя и Фамилию ученика:",
        parse_mode="HTML"
    )
    await state.set_state(AddStudentForm.waiting_for_name)
    await callback.answer()

@router.message(AddStudentForm.waiting_for_name)
async def process_student_name(message: Message, state: FSMContext):
    await state.update_data(student_name=message.text)
    
    # Программы: 1 мес (12), 3 мес (37), 6 мес (75)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 месяц (12 зан.)", callback_data="prog_12")],
        [InlineKeyboardButton(text="3 месяца (37 зан.)", callback_data="prog_37")],
        [InlineKeyboardButton(text="6 месяцев (75 зан.)", callback_data="prog_75")]
    ])
    
    await message.answer(
        f"Ученик <b>{message.text}</b>.\nВыберите программу обучения:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.set_state(AddStudentForm.waiting_for_program)

@router.callback_query(AddStudentForm.waiting_for_program, F.data.startswith("prog_"))
async def process_student_program(callback: CallbackQuery, state: FSMContext, bot: Bot):
    lessons_count = int(callback.data.split("_")[1])
    data = await state.get_data()
    student_name = data['student_name']
    
    # 🔥 РЕАЛЬНОЕ СОХРАНЕНИЕ В БАЗУ ДАННЫХ
    db_student_id = await create_client_with_package(
        full_name=student_name,
        package_type="education",
        total_sessions=lessons_count
    )
    
    # Генерация реальной ссылки для ученика
    link = await create_start_link(bot, str(db_student_id), encode=True)
    
    await callback.message.edit_text(
        f"✅ <b>Ученик успешно добавлен!</b>\n\n"
        f"👤 Имя: <b>{student_name}</b>\n"
        f"📚 Программа: <b>{lessons_count} занятий</b>\n\n"
        f"🔗 <b>Ссылка для ученика:</b>\n{link}",
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()

# --- СТАТИСТИКА (Каркас) ---

@router.callback_query(F.data == "edu_stats")
async def show_edu_stats(callback: CallbackQuery):
    await callback.message.edit_text(
        "📈 <b>Статистика обучения:</b>\n\n"
        "<i>Скоро здесь появится список учеников из базы данных.</i>",
        reply_markup=get_edu_admin_kb(),
        parse_mode="HTML"
    )
    await callback.answer()
