import asyncio
import re
from playwright.async_api import async_playwright
from db import init_db, save_rate

async def run_heavy_artillery():
    print("🚀 [СНАЙПЕР] Запускаю парсинг по ПРЯМЫМ ССЫЛКАМ...")
    init_db()

    async with async_playwright() as p:
        # ВНИМАНИЕ: Для сервера headless обязательно должен быть True!
        browser = await p.chromium.launch(headless=True) 
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale="ru-RU", 
            timezone_id="Europe/Moscow" 
        )
        page = await context.new_page()
        
        # Наш плащ-невидимка
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # ---------------------------------------------------------
        # 1. ЦБ РФ
        # ---------------------------------------------------------
        print("\n📍 Иду на ЦБ РФ...")
        try:
            await page.goto("https://www.cbr.ru/", wait_until="domcontentloaded", timeout=30000)
            block_text = await page.evaluate('''() => {
                const elements = Array.from(document.querySelectorAll('*'));
                const label = elements.find(el => el.textContent.trim() === 'Ключевая ставка' && el.children.length === 0);
                if (!label) return null;
                let parent = label.parentElement;
                while (parent && parent.innerText.indexOf('%') === -1) {
                    parent = parent.parentElement;
                }
                return parent ? parent.innerText : null;
            }''')
            if block_text:
                match = re.search(r'(\d+[,.]\d+)\s*%', block_text)
                if match:
                    rate = float(match.group(1).replace(",", "."))
                    print(f"✅ [ЦБ РФ] Нашел: {rate}%")
                    save_rate("ЦБ РФ", rate, "Ключевая ставка")
        except Exception as e:
            print(f"❌ [ЦБ РФ] Ошибка: {e}")

        # ---------------------------------------------------------
        # 2. СНАЙПЕРСКИЙ ОБХОДЧИК ПО БАНКАМ
        # ---------------------------------------------------------
        banks_config = [
            {"name": "Альфа-Банк", "url": "https://alfabank.ru/get-money/credit/", "badge": "Лучшее решение"},
            {"name": "СберБанк", "url": "https://www.sberbank.ru/ru/person/credits/money/na_50000_rublej", "badge": "+ 21 000 ₽ переплаты", "is_sber": True},
            {"name": "ВТБ", "url": "https://www.vtb.ru/personal/kredit/nalichnymi/", "badge": "Обязательная страховка", "is_vtb": True},
            {"name": "Т-Банк", "url": "https://www.tbank.ru/loans/cash-loan/nopledge/tariffs/", "badge": "Скрытые комиссии"}
        ]

        for bank in banks_config:
            print(f"\n📍 Иду на {bank['name']}...")
            try:
                await page.goto(bank['url'], wait_until="domcontentloaded", timeout=30000)
                
                # Скроллим страницу, чтобы таблицы тарифов прогрузились
                for _ in range(4):
                    await page.mouse.wheel(0, 800)
                    await page.wait_for_timeout(1000)
                
                # Забираем текст и убиваем неразрывные пробелы
                text = await page.evaluate("document.body.innerText")
                text = text.replace('\xa0', ' ').replace('\n', ' ')
                
                # Страхуемся сырым HTML
                html = await page.content()
                
                # --- УМНЫЕ ФИЛЬТРЫ ---
                if bank.get("is_sber"):
                    # Сбер: Ищем только со словом "От"
                    matches = re.findall(r'[Оо]т\s*(\d{1,2}[,.]\d{1,2})\s*%', text)
                    if not matches:
                        matches = re.findall(r'[Оо]т(?:&nbsp;|\s|<[^>]*>)*(\d{1,2}[,.]\d{1,2})\s*%', html)
                
                elif bank.get("is_vtb"):
                    # ВТБ: Ищем формат ПСК (где после процента идет тире)
                    matches = re.findall(r'(\d{1,2}[,.]\d{1,3})\s*%(?:&nbsp;|\s|<[^>]*>)*(?:–|-|—)', text)
                    if not matches:
                        matches = re.findall(r'(\d{1,2}[,.]\d{1,3})\s*%(?:&nbsp;|\s|<[^>]*>)*(?:–|-|—)', html)
                
                else:
                    # Альфа и Т-Банк: Обычный поиск
                    matches = re.findall(r'(\d{1,2}[,.]\d{1,3})\s*%', text)
                    if not matches:
                        matches = re.findall(r'(\d{1,2}[,.]\d{1,3})\s*%', html)
                
                # --- ФИЛЬТРАЦИЯ И СОХРАНЕНИЕ ---
                if matches:
                    valid_rates = []
                    for m in matches:
                        rate = float(m.replace(",", "."))
                        # Берем ставки строго от 10% до 60%
                        if 10.0 <= rate <= 60.0:
                            valid_rates.append(rate)
                    
                    if valid_rates:
                        final_rate = min(valid_rates)
                        print(f"✅ [{bank['name']}] ТОЧНОЕ ПОПАДАНИЕ! Ставка: {final_rate}%")
                        save_rate(bank['name'], final_rate, bank['badge'])
                    else:
                        print(f"⚠️ [{bank['name']}] Нашел только странные цифры: {matches}. Ставлю 0.")
                        save_rate(bank['name'], 0.0, bank['badge'])
                else:
                    print(f"❌ [{bank['name']}] Вообще ничего не нашел. Ставлю 0.")
                    save_rate(bank['name'], 0.0, bank['badge'])
                    
            except Exception as e:
                print(f"❌ [{bank['name']}] Ошибка загрузки. Ставлю 0.")
                save_rate(bank['name'], 0.0, bank['badge'])

        print("\n🏁 [СНАЙПЕР] Обход завершен! База данных обновлена.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_heavy_artillery())