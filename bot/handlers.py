from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot

router = Router()


class AddWebsite(StatesGroup):
    waiting_for_url = State()
    waiting_for_interval = State()


@router.message(Command("start"))
async def cmd_start(message: types.Message, db):
    """Обработчик команды /start"""
    # Добавляем пользователя в базу
    db.add_user(message.from_user.id, message.chat.id)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить сайт"), KeyboardButton(text="Мои сайты")],
            [KeyboardButton(text="Удалить сайт"), KeyboardButton(text="Статистика")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "👋 Добро пожаловать в мониторинг сайтов!\n\n"
        "Я могу отслеживать доступность ваших веб-сайтов и отправлять уведомления при проблемах.\n\n"
        "Используйте кнопки ниже для управления:",
        reply_markup=keyboard
    )


@router.message(F.text == "Добавить сайт")
async def button_add_website(message: types.Message, state: FSMContext):
    """Обработчик нажатия кнопки 'Добавить сайт'"""
    await message.answer("Введите URL сайта для мониторинга:")
    await state.set_state(AddWebsite.waiting_for_url)


@router.message(AddWebsite.waiting_for_url)
async def process_website_url(message: types.Message, state: FSMContext):
    """Обработка введенного URL"""
    url = message.text.strip()

    # Простая валидация URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    await state.update_data(url=url)
    await message.answer("Введите интервал проверки в секундах (по умолчанию 300):")
    await state.set_state(AddWebsite.waiting_for_interval)


@router.message(AddWebsite.waiting_for_interval)
async def process_website_interval(
        message: types.Message,
        state: FSMContext,
        db,  # Зависимость будет автоматически внедрена
        scheduler  # Зависимость будет автоматически внедрена
):
    """Обработка введенного интервала проверки"""
    data = await state.get_data()
    url = data['url']

    try:
        interval = int(message.text) if message.text.strip() else 300
    except ValueError:
        interval = 300

    # Добавляем сайт в базу данных
    website_id = db.add_website(message.from_user.id, url, interval)

    if website_id:
        # Добавляем сайт в мониторинг
        website = {
            'id': website_id,
            'url': url,
            'user_id': message.from_user.id,
            'check_interval': interval
        }
        scheduler.add_website_to_monitor(website)

        await message.answer(f"✅ Сайт {url} добавлен в мониторинг с интервалом {interval} секунд")
    else:
        await message.answer("❌ Ошибка при добавлении сайта")

    await state.clear()


@router.message(F.text == "Мои сайты")
async def button_list_websites(message: types.Message, db):
    """Обработчик нажатия кнопки 'Мои сайты'"""
    websites = db.get_user_websites(message.from_user.id)

    if not websites:
        await message.answer("У вас нет сайтов для мониторинга.")
        return

    text = "📋 Ваши сайты:\n\n"
    for site in websites:
        status_emoji = "🟢" if site['last_status'] == 'up' else "🔴"
        text += f"{status_emoji} {site['url']} (каждые {site['check_interval']} сек.)\n"

    await message.answer(text)


@router.message(F.text == "Статистика")
async def button_stats(message: types.Message, db):
    """Обработчик нажатия кнопки 'Статистика'"""
    websites = db.get_user_websites(message.from_user.id)

    if not websites:
        await message.answer("У вас нет сайтов для мониторинга.")
        return

    text = "📊 Статистика:\n\n"
    for site in websites:
        stats = db.get_website_stats(site['id'])
        if stats:
            uptime_percent = (stats['up_checks'] / stats['total_checks'] * 100) if stats['total_checks'] > 0 else 0
            text += f"🌐 {site['url']}\n"
            text += f"   Доступность: {uptime_percent:.1f}%\n"
            text += f"   Время ответа: {stats['avg_response_time']:.2f}мс\n"
            text += f"   Проверок: {stats['total_checks']}\n\n"

    await message.answer(text)


@router.message(F.text == "Удалить сайт")
async def button_delete_website(message: types.Message, db):
    """Обработчик нажатия кнопки 'Удалить сайт'"""
    websites = db.get_user_websites(message.from_user.id)

    if not websites:
        await message.answer("У вас нет сайтов для удаления.")
        return

    # Создаем инлайн-клавиатуру с сайтами для удаления
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for site in websites:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {site['url']}",
                callback_data=f"delete_{site['id']}"
            )
        ])

    await message.answer("Выберите сайт для удаления:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("delete_"))
async def process_delete_website(callback: types.CallbackQuery, db):
    """Обработка удаления сайта"""
    website_id = int(callback.data.split("_")[1])

    if db.delete_website(callback.from_user.id, website_id):
        await callback.message.answer("✅ Сайт удален из мониторинга")
    else:
        await callback.message.answer("❌ Ошибка при удалении сайта")

    await callback.answer()


@router.message()
async def handle_all_messages(message: types.Message):
    """Обработчик всех сообщений (для отладки)"""
    print(f"Получено сообщение: {message.text}")