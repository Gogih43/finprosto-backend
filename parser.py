import asyncio
import re
from playwright.async_api import async_playwright
from db import init_db, save_rate

async def run_heavy_artillery():
    print("🚀 [СНАЙПЕР] Запускаю парсинг с оптимизацией памяти...")
    init_db()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-gpu', '--single-process']
        )
        
        # Индивидуальные снайперские регулярки для каждого банка
        banks_config = [
            {
                "name": "Альфа-Банк", 
                "url": "https://alfabank.ru/get-money/credit/", 
                "fallback": 17.4, "badge": "Лучшее решение",
                "regex": r'(\d{1,2}[,.]\d{1,2})\s*%'
            },
            {
                "name": "СберБанк", 
                "url": "https://www.sberbank.com/ru/person/credits/money/credit_unsecured", 
                "fallback": 17.9, "badge": "+ 21 000 ₽ переплаты",
                "regex": r'[Оо]т(?:&nbsp;|\s)*(\d{1,2}[,.]\d{1,2})\s*%'
            },
            {
                "name": "ВТБ", 
                "url": "https://www.vtb.ru/personal/kredity/nalichnymi/", 
                "fallback": 15.9, "badge": "Обязательная страховка",
                "regex": r'(\d{1,2}[,.]\d{1,3})\s*%(?:&nbsp;|\s|<[^>]*>)*(?:–|-|—|&ndash;|&mdash;)'
            },
            {
                "name": "Т-Банк", 
                "url": "https://www.tbank.ru/loans/cash-loan/", 
                "fallback": 14.9, "badge": "Скрытые комиссии",
                "regex": r'(\d{1,2}[,.]\d{1,2})\s*%(?:&nbsp;|\s|<[^>]*>)*(?:–|-|—|&ndash;|&mdash;)'
            }
        ]

        for bank in banks_config:
            print(f"\n📍 Иду на {bank['name']}...")
            try:
                context = await browser.new_context(viewport={'width': 1280, 'height': 720})
                page = await context.new_page()

                async def route_intercept(route):
                    if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                        await route.abort()
                    else:
                        await route.continue_()
                
                await page.route("**/*", route_intercept)

                await page.goto(bank['url'], wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Бьем снайперской регуляркой по СЫРОМУ HTML (чтобы обойти скрытые блоки React)
                html = await page.content()
                matches = re.findall(bank['regex'], html)
                
                if matches:
                    valid_rates = []
                    for m in matches:
                        rate = float(m.replace(",", "."))
                        if 10.0 <= rate <= 60.0: # Ставки сейчас высокие, берем от 10%
                            valid_rates.append(rate)
                    
                    if valid_rates:
                        final_rate = min(valid_rates)
                        print(f"✅ [{bank['name']}] Нашел точную ставку: {final_rate}%")
                        save_rate(bank['name'], final_rate, bank['badge'])
                    else:
                        print(f"⚠️ [{bank['name']}] Мусорные цифры. Ставлю резерв.")
                        save_rate(bank['name'], bank['fallback'], bank['badge'])
                else:
                    print(f"⚠️ [{bank['name']}] Ничего не нашел. Ставлю резерв.")
                    save_rate(bank['name'], bank['fallback'], bank['badge'])
                    
            except Exception as e:
                print(f"❌ [{bank['name']}] Ошибка загрузки. Ставлю резерв.")
                save_rate(bank['name'], bank['fallback'], bank['badge'])
            finally:
                await context.close()

        print("\n🏁 [СНАЙПЕР] Обход завершен!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_heavy_artillery())