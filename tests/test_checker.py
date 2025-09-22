import pytest
from bot.checker import WebsiteChecker


@pytest.mark.asyncio
async def test_check_website_success():
    """Тестирование успешной проверки сайта"""
    checker = WebsiteChecker()
    result = await checker.check_website("https://httpbin.org/status/200")

    assert result['status'] == 'up'
    assert result['status_code'] == 200
    assert result['response_time'] > 0


@pytest.mark.asyncio
async def test_check_website_failure():
    """Тестирование проверки недоступного сайта"""
    checker = WebsiteChecker()
    result = await checker.check_website("https://httpbin.org/status/404")

    assert result['status'] == 'down'
    assert result['status_code'] == 404


@pytest.mark.asyncio
async def test_check_website_timeout():
    """Тестирование обработки таймаута"""
    checker = WebsiteChecker()
    # Сайт, который не ответит за 10 секунд
    result = await checker.check_website("https://httpstat.us/200?sleep=11000")

    assert result['status'] == 'down'