import asyncio
import re
import requests
from playwright.async_api import async_playwright

RENDER_URL = "https://finprosto-backend.onrender.com/api/update_rates"
SECRET_KEY = "GOGIH_SUPER_SECRET_2026"

async def run_spy():
    print("🕵️‍♂️ [ШПИОН] Запускаюсь в скрытом режиме с МАСКИРОВКОЙ под человека...")
    
    collected_data = []

    async with async_playwright() as p:
        # Браузер невидимый, но с маскировкой!
        browser = await p.chromium.launch(headless=True)
        
        # Создаем профиль реального человека (User-Agent и разрешение экрана)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 1. ЦБ РФ
        try:
            print("\n📍 Иду на ЦБ РФ...")
            page = await context.new_page()
            # ПЛАЩ-НЕВИДИМКА: стираем клеймо "я бот" из браузера
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            await page.goto("https://www.cbr.ru/", timeout=30000)
            text = await page.locator("body").inner_text()
            match = re.search(r'Ключевая ставка.*?(\d+[,.]\d+)\s*%', text, re.IGNORECASE | re.DOTALL)
            if match:
                rate = float(match.group(1).replace(",", "."))
                print(f"✅ [ЦБ РФ] Нашел: {rate}%")
                collected_data.append({"name": "ЦБ РФ", "rate": rate, "badge": "Ключевая ставка"})
            else:
                print("⚠️ [ЦБ РФ] Не нашел ставку! Ставлю 16.0%")
            await page.close()
        except Exception as e:
            print(f"❌ [ЦБ РФ] Ошибка: {e}")

        # 2. БАНКИ (Используем твои секретные прямые ссылки на тарифы!)
        banks_config = [
            {"name": "Альфа-Банк", "url": "https://alfabank.ru/get-money/credit/", "fallback": 17.4, "badge": "Лучшее решение", "regex": r'(\d{1,2}[,.]\d{1,2})\s*%'},
            {"name": "СберБанк", "url": "https://www.sberbank.ru/ru/person/credits/money/na_50000_rublej", "fallback": 17.9, "badge": "+ 21 000 ₽ переплаты", "regex": r'[Оо]т(?:&nbsp;|\s)*(\d{1,2}[,.]\d{1,2})\s*%'},
            {"name": "ВТБ", "url": "https://www.vtb.ru/personal/kredit/nalichnymi/", "fallback": 15.9, "badge": "Обязательная страховка", "regex": r'(\d{1,2}[,.]\d{1,3})\s*%(?:&nbsp;|\s|<[^>]*>)*(?:–|-|—|&ndash;|&mdash;)'},
            {"name": "Т-Банк", "url": "https://www.tbank.ru/loans/cash-loan/nopledge/tariffs/", "fallback": 14.9, "badge": "Скрытые комиссии", "regex": r'(\d{1,2}[,.]\d{1,2})\s*%(?:&nbsp;|\s|<[^>]*>)*(?:–|-|—|&ndash;|&mdash;)'}
        ]

        for bank in banks_config:
            print(f"\n📍 Иду на {bank['name']}...")
            try:
                page = await context.new_page()
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                await page.goto(bank['url'], timeout=30000)
                
                # Скроллим вниз
                for _ in range(4):
                    await page.mouse.wheel(0, 800)
                    await page.wait_for_timeout(1000)
                
                html = await page.content()
                text = await page.evaluate("document.body.innerText")
                
                matches = re.findall(bank['regex'], html)
                if not matches:
                    matches = re.findall(r'(\d{1,2}(?:[,.]\d{1,2})?)\s*%', text)
                
                if matches:
                    valid_rates = [float(m.replace(",", ".")) for m in matches if 12.0 <= float(m.replace(",", ".")) <= 50.0]
                    if valid_rates:
                        final_rate = min(valid_rates)
                        print(f"✅ [{bank['name']}] Нашел: {final_rate}%")
                        collected_data.append({"name": bank['name'], "rate": final_rate, "badge": bank['badge']})
                    else:
                        print(f"⚠️ [{bank['name']}] Нашел только мусор: {matches}. Ставлю резерв: {bank['fallback']}%")
                        collected_data.append({"name": bank['name'], "rate": bank['fallback'], "badge": bank['badge']})
                else:
                    print(f"⚠️ [{bank['name']}] Страница загрузилась, но процентов нет. Ставлю резерв: {bank['fallback']}%")
                    collected_data.append({"name": bank['name'], "rate": bank['fallback'], "badge": bank['badge']})
                    
                await page.close()
            except Exception as e:
                print(f"❌ [{bank['name']}] Ошибка загрузки: {e}")
                collected_data.append({"name": bank['name'], "rate": bank['fallback'], "badge": bank['badge']})

        await browser.close()

    print("\n🚀 Отправляю данные на сервер Vercel...")
    payload = {"secret_key": SECRET_KEY, "rates": collected_data}
    response = requests.post(RENDER_URL, json=payload)
    
    if response.status_code == 200:
        print("🎉 УСПЕХ! Данные успешно загружены на сайт!")
    else:
        print(f"❌ Ошибка отправки: {response.text}")

if __name__ == "__main__":
    asyncio.run(run_spy())