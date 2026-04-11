# Добавь этот хендлер в конец файла user.py

@router.message(F.text == "/profile")
@router.message(F.text == "👤 Профиль") # Если потом сделаем кнопку в меню
async def show_user_profile(message: Message):
    user = await get_user_by_tg_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы в системе.")
        return

    text = f"👤 <b>Ваш профиль</b>\n\nИмя: {user.full_name}\n\n"
    
    if not user.packages:
        text += "У вас пока нет активных абонементов."
    else:
        text += "<b>Ваши услуги:</b>\n"
        for pkg in user.packages:
            icon = "💆‍♂️" if pkg.package_type == "massage" else "🎓"
            name = "Массаж" if pkg.package_type == "massage" else "Обучение"
            rem = pkg.total_sessions - pkg.used_sessions
            status = "✅ Активен" if pkg.status == "active" else "🏁 Завершен"
            text += f"{icon} {name}: <b>{rem}</b> из {pkg.total_sessions} ({status})\n"

    await message.answer(text, parse_mode="HTML")
