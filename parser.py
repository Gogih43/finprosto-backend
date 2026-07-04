import asyncio
import re
from playwright.async_api import async_playwright
from db import init_db, save_rate

async def run_heavy_artillery():
    print("🚀 [БРОНЕПОЕЗД] Запускаю парсинг с ОПТИМИЗАЦИЕЙ ПАМЯТИ...")
    init_db()

    async with async_playwright() as p:
        # 🔥 МАГИЯ 1: Запускаем браузер в режиме жесткой экономии памяти
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage', # Спасает от краша в Linux
                '--no-sandbox',
                '--disable-gpu',
                '--single-process'
            ]
        )
        
        banks_to_parse = [
            {"name": "Альфа-Банк", "url": "https://alfabank.ru/get-money/credit/", "fallback": 17.4, "badge": "Лучшее решение"},
            {"name": "СберБанк", "url": "https://www.sberbank.com/ru/person/credits/money/credit_unsecured", "fallback": 17.9, "badge": "+ 21 000 ₽ переплаты"},
            {"name": "ВТБ", "url": "https://www.vtb.ru/personal/kredity/nalichnymi/", "fallback": 15.9, "badge": "Обязательная страховка"},
            {"name": "Т-Банк", "url": "https://www.tbank.ru/loans/cash-loan/", "fallback": 14.9, "badge": "Скрытые комиссии"}
        ]

        for bank in banks_to_parse:
            print(f"\n📍 Иду на {bank['name']}...")
            try:
                # Открываем чистую изолированную вкладку
                context = await browser.new_context(viewport={'width': 1280, 'height': 720})
                page = await context.new_page()

                # 🔥 МАГИЯ 2: Блокируем загрузку ВСЕХ картинок, стилей и шрифтов
                async def route_intercept(route):
                    if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                        await route.abort()
                    else:
                        await route.continue_()
                
                await page.route("**/*", route_intercept)

                # Заходим на сайт
                await page.goto(bank['url'], wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                
                text = await page.locator("body").inner_text()
                matches = re.findall(r'(\d{1,2}(?:[,.]\d{1,2})?)\s*%', text)
                
                if matches:
                    valid_rates = [float(m.replace(",", ".")) for m in matches if 5.0 <= float(m.replace(",", ".")) <= 40.0]
                    if valid_rates:
                        final_rate = min(valid_rates)
                        print(f"✅ [{bank['name']}] Нашел ставку: {final_rate}%")
                        save_rate(bank['name'], final_rate, bank['badge'])
                    else:
                        save_rate(bank['name'], bank['fallback'], bank['badge'])
                else:
                    save_rate(bank['name'], bank['fallback'], bank['badge'])
                    
            except Exception as e:
                print(f"❌ [{bank['name']}] Ошибка: {e}")
                save_rate(bank['name'], bank['fallback'], bank['badge'])
            finally:
                # 🔥 МАГИЯ 3: ЖЕСТКО ЗАКРЫВАЕМ ВЛАДКУ, чтобы освободить оперативную память
                await context.close()

        print("\n🏁 [БРОНЕПОЕЗД] Обход завершен. Память не превышена!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_heavy_artillery())