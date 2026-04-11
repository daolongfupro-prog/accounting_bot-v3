# handlers/admin_edu.py (Частичное обновление логики сохранения)

@router.callback_query(AddStudentForm.waiting_for_program, F.data.startswith("prog_"))
async def process_student_program(callback: CallbackQuery, state: FSMContext, bot: Bot):
    lessons_count = int(callback.data.split("_")[1])
    data = await state.get_data()
    student_name = data['student_name']
    
    # 🔥 РЕАЛЬНОЕ СОХРАНЕНИЕ В БАЗУ
    db_student_id = await create_client_with_package(
        full_name=student_name,
        package_type="education",
        total_sessions=lessons_count
    )
    
    # Генерация реальной ссылки
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
