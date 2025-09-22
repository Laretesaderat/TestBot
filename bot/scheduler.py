from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

class MonitoringScheduler:
    def __init__(self, bot, db, checker):
        self.bot = bot
        self.db = db
        self.checker = checker
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}

    async def start(self):
        """Запускает планировщик и загружает существующие задачи"""
        self.scheduler.start()

        # Загружаем существующие сайты для мониторинга
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM websites WHERE is_active = TRUE")
            websites = cursor.fetchall()

            for website in websites:
                self.add_website_to_monitor(website)

    def add_website_to_monitor(self, website):
        """Добавляет сайт в мониторинг"""
        job_id = f"website_{website['id']}"

        # Создаем задачу для периодической проверки
        job = self.scheduler.add_job(
            self.check_and_notify,
            trigger=IntervalTrigger(seconds=website['check_interval']),
            args=[website],
            id=job_id
        )

        self.jobs[website['id']] = job

    async def check_and_notify(self, website):
        """Проверяет сайт и отправляет уведомления при изменении статуса"""
        result = await self.checker.check_website(website['url'])

        # Сохраняем результат проверки
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Получаем текущий статус сайта из базы
            cursor.execute(
                "SELECT last_status FROM websites WHERE id = ?",
                (website['id'],)
            )
            current_status_row = cursor.fetchone()
            current_status = current_status_row['last_status'] if current_status_row else 'unknown'

            # Сохраняем результат проверки
            cursor.execute(
                "INSERT INTO check_results (website_id, status, status_code, response_time) VALUES (?, ?, ?, ?)",
                (website['id'], result['status'], result['status_code'], result['response_time'])
            )

            # Обновляем статус сайта
            cursor.execute(
                "UPDATE websites SET last_status = ?, last_response_time = ? WHERE id = ?",
                (result['status'], result['response_time'], website['id'])
            )

            # Проверяем, изменился ли статус
            if current_status != result['status']:
                # Отправляем уведомление
                message = self.format_notification(website, result, current_status)
                try:
                    await self.bot.send_message(website['user_id'], message)
                except Exception as e:
                    print(f"Ошибка при отправке уведомления: {e}")

            conn.commit()

    def format_notification(self, website, result, previous_status):
        """Форматирует сообщение уведомления"""
        if result['status'] == 'down':
            return (f"🔴 Сайт {website['url']} стал недоступен!\n"
                    f"📊 Предыдущий статус: {previous_status}\n"
                    f"⏰ Время: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        else:
            return (f"🟢 Сайт {website['url']} снова доступен!\n"
                    f"📊 Предыдущий статус: {previous_status}\n"
                    f"⚡ Время ответа: {result['response_time']:.2f}мс\n"
                    f"✅ Код ответа: {result['status_code']}\n"
                    f"⏰ Время: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")