import asyncio
import re
import requests
from playwright.async_api import async_playwright

RENDER_URL = "https://finprosto-backend.onrender.com/api/update_rates"
SECRET_KEY = "GOGIH_SUPER_SECRET_2026"

async def run_spy():
    print("🕵️‍♂️ [ШПИОН] Запускаюсь в скрытом режиме с ТОЧНЫМИ РЕГУЛЯРКАМИ...")
    
    collected_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 1. ЦБ РФ
        try:
            print("\n📍 Иду на ЦБ РФ...")
            page = await context.new_page()
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            await page.goto("https://www.cbr.ru/", timeout=30000)
            text = await page.locator("body").inner_text()
            match = re.search(r'Ключевая ставка.*?(\d+[,.]\d+)\s*%', text, re.IGNORECASE | re.DOTALL)
            if match:
                rate = float(match.group(1).replace(",", "."))
                print(f"✅ [ЦБ РФ] Нашел: {rate}%")
                collected_data.append({"name": "ЦБ РФ", "rate": rate, "badge": "Ключевая ставка"})
            else:
                print("⚠️ [ЦБ РФ] Не нашел ставку!")
            await page.close()
        except Exception as e:
            print(f"❌ [ЦБ РФ] Ошибка: {e}")

        # 2. СПИСОК БАНКОВ (Без резервных ставок, только хардкор)
        banks_config = [
            {"name": "Альфа-Банк", "url": "https://alfabank.ru/get-money/credit/", "badge": "Лучшее решение", "regex": r'(\d{1,2}[,.]\d{1,2})\s*%'},
            {"name": "СберБанк", "url": "https://www.sberbank.ru/ru/person/credits/money/na_50000_rublej", "badge": "+ 21 000 ₽ переплаты", "regex": r'[Оо]т(?:&nbsp;|\s)*(\d{1,2}[,.]\d{1,2})\s*%'},
            {"name": "ВТБ", "url": "https://www.vtb.ru/personal/kredit/nalichnymi/", "badge": "Обязательная страховка", "regex": r'(\d{1,2}[,.]\d{1,3})\s*%(?:&nbsp;|\s|<[^>]*>)*(?:–|-|—|&ndash;|&mdash;)'},
            {"name": "Т-Банк", "url": "https://www.tbank.ru/loans/cash-loan/nopledge/tariffs/", "badge": "Скрытые комиссии", "regex": r'(\d{1,2}[,.]\d{1,2})\s*%(?:&nbsp;|\s|<[^>]*>)*(?:–|-|—|&ndash;|&mdash;)'},
            {"name": "Газпромбанк", "url": "https://www.gazprombank.ru/personal/credits/", "badge": "Зарплатным клиентам", "regex": r'[Оо]т(?:&nbsp;|\s|<[^>]*>)*(\d{1,2}[,.]\d{1,2})\s*%'},
            {"name": "ПСБ", "url": "https://www.psbank.ru/Personal/Loans", "badge": "Госслужащим", "regex": r'[Оо]т(?:&nbsp;|\s|<[^>]*>)*(\d{1,2}[,.]\d{1,3})\s*%'},
            {"name": "Россельхозбанк", "url": "https://www.rshb.ru/natural/loans/", "badge": "Крупный банк", "regex": r'[Оо]т(?:&nbsp;|\s|<[^>]*>)*(\d{1,2}[,.]\d{1,2})\s*%'},
            {"name": "Совкомбанк", "url": "https://sovcombank.ru/credits/", "badge": "С картой Халва", "regex": r'[Оо]т(?:&nbsp;|\s|<[^>]*>)*(\d{1,2}[,.]\d{1,2})\s*%'},
            {"name": "Уралсиб", "url": "https://www.uralsib.ru/kredity", "badge": "Быстрое решение", "regex": r'(\d{1,2}[,.]\d{1,2})\s*%(?:&nbsp;|\s)*[–\-]'}
        ]

        for bank in banks_config:
            print(f"\n📍 Иду на {bank['name']}...")
            try:
                page = await context.new_page()
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                await page.goto(bank['url'], timeout=30000)
                
                for _ in range(4):
                    await page.mouse.wheel(0, 800)
                    await page.wait_for_timeout(1000)
                
                html = await page.content()
                
                # Ищем точной регуляркой
                matches = re.findall(bank['regex'], html)
                
                if matches:
                    valid_rates = [float(m.replace(",", ".")) for m in matches if 12.0 <= float(m.replace(",", ".")) <= 50.0]
                    if valid_rates:
                        final_rate = min(valid_rates)
                        print(f"✅ [{bank['name']}] Нашел точную ставку: {final_rate}%")
                        collected_data.append({"name": bank['name'], "rate": final_rate, "badge": bank['badge']})
                    else:
                        print(f"⚠️ [{bank['name']}] Нашел только мусор. Пропускаю, бэкенд сохранит вчерашнюю ставку.")
                else:
                    print(f"⚠️ [{bank['name']}] Регулярка не сработала. Пропускаю.")
                    
                await page.close()
            except Exception as e:
                print(f"❌ [{bank['name']}] Ошибка загрузки: {e}. Пропускаю.")

        await browser.close()

    print(f"\n🚀 Отправляю данные ({len(collected_data)} банков) на сервер...")
    
    if len(collected_data) > 0:
        payload = {"secret_key": SECRET_KEY, "rates": collected_data}
        response = requests.post(RENDER_URL, json=payload)
        
        if response.status_code == 200:
            print("🎉 УСПЕХ! Данные успешно обновлены в БД!")
        else:
            print(f"❌ Ошибка отправки: {response.text}")
    else:
        print("⚠️ Нет данных для отправки!")

if __name__ == "__main__":
    asyncio.run(run_spy())