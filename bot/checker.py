import aiohttp
import asyncio
from datetime import datetime

class WebsiteChecker:
    @staticmethod
    async def check_website(url):
        """Проверяет доступность сайта и возвращает результат"""
        start_time = datetime.now()
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, ssl=False) as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    return {
                        'status': 'up' if response.status < 400 else 'down',
                        'status_code': response.status,
                        'response_time': response_time,
                        'timestamp': datetime.now()
                    }
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            return {
                'status': 'down',
                'status_code': 0,
                'response_time': 0,
                'timestamp': datetime.now(),
                'error': str(e)
            }