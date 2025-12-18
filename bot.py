import telebot
from telebot import types
import os
import json
import sqlite3
import random
import string
import zipfile
import shutil
from datetime import datetime, timedelta
import threading
from time import sleep as wait
from EasyGiftSend import EasyGiftSend as G
token = None
bot = telebot.TeleBot(token)
EasyGiftSend = G(token)

def evaluate_donation_bonus(amount, user_id):
    results = []

    try:
        balance = EasyGiftSend.get_balance()

        if balance < 15:
            return {"ok": False, "description": f"Недостаточно средств на балансе бота. Баланс: {balance}"}

        if amount == 30 or amount == 100:
            if EasyGiftSend.can_afford_gift("🧸"):
                print("🟡 Отправляем мишку за 30 stars")
                result = EasyGiftSend.send_gift(
                    gift_emoji="🧸",
                    user_id=user_id,
                    message="Спасибо за пополнение 30 Stars! 🎁 В качестве благодарности держите подарок."
                )
                results.append(result)




        elif amount == 50:
            if EasyGiftSend.can_afford_gift("🧸") and EasyGiftSend.get_balance() >= 30:
                for i in range(2):
                    wait(1)
                    result = EasyGiftSend.send_gift(
                        gift_emoji="🧸",
                        user_id=user_id,
                        message=f"Спасибо за пополнение 50 Stars! 🎁 Подарок {i+1}/2"
                    )
                    results.append(result)
        elif amount == 500:
            if EasyGiftSend.can_afford_gift("🚀"):
                if EasyGiftSend.get_balance() >= 150:
                    for i in range(3):
                        wait(1)
                        result = EasyGiftSend.send_gift(
                            gift_emoji="🚀",
                            user_id=user_id,
                            message=f"Спасибо за крупное пополнение 500 Stars! 🚀 Подарок {i+1}/3"
                        )
                        results.append(result)
                else:
                    available_gifts = min(3, EasyGiftSend.get_balance() // 50)
                    for i in range(available_gifts):
                        wait(1)
                        result = EasyGiftSend.send_gift(
                            gift_emoji="🚀",
                            user_id=user_id,
                            message=f"Спасибо за пополнение 500 Stars! 🚀 Подарок {i+1}/{available_gifts}"
                        )
                        results.append(result)

        elif amount == 1000:
            if EasyGiftSend.can_afford_gift("🏆"):
                if EasyGiftSend.get_balance() >= 400:
                    for i in range(4):
                        wait(1)
                        result = EasyGiftSend.send_gift(
                            gift_emoji="🏆",
                            user_id=user_id,
                            message=f"Спасибо за крупное пополнение 1000 Stars! 🏆 Подарок {i+1}/4"
                        )
                        results.append(result)
                else:
                    available_gifts = min(4, EasyGiftSend.get_balance() // 100)
                    for i in range(available_gifts):
                        wait(1)
                        result = EasyGiftSend.send_gift(
                            gift_emoji="🏆",
                            user_id=user_id,
                            message=f"Спасибо за пополнение 1000 Stars! 🏆 Подарок {i+1}/{available_gifts}"
                        )
                        results.append(result)

        elif amount > 1000:
            if EasyGiftSend.can_afford_gift("💎"):
                if EasyGiftSend.get_balance() >= 500:
                    for i in range(5):
                        wait(1)
                        result = EasyGiftSend.send_gift(
                            gift_emoji="💎",
                            user_id=user_id,
                            message=f"Спасибо за эксклюзивное пополнение {amount} Stars! 💎 Подарок {i+1}/5"
                        )
                        results.append(result)
                else:
                    available_gifts = min(5, EasyGiftSend.get_balance() // 100)
                    for i in range(available_gifts):
                        wait(1)
                        result = EasyGiftSend.send_gift(
                            gift_emoji="💎",
                            user_id=user_id,
                            message=f"Спасибо за пополнение {amount} Stars! 💎 Подарок {i+1}/{available_gifts}"
                        )
                        results.append(result)
                        
        successful_sends = [r for r in results if r and r.get("ok")]
        failed_sends = [r for r in results if r and not r.get("ok")]

        final_result = {
            "ok": len(failed_sends) == 0,
            "successful_sends": len(successful_sends),
            "failed_sends": len(failed_sends),
            "total_gifts_sent": len(successful_sends),
            "details": results
        }
        return final_result

    except Exception as e:
        error_msg = f"System error: {str(e)}"
        return {"ok": False, "description": error_msg}

ADMINS = []
OWNERS = []
db_lock = threading.Lock()

def get_db_connection():
  
    conn = sqlite3.connect('shop.db', timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL") 
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def init_db():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                crystals REAL DEFAULT 0.0,
                registration_date TEXT,
                role TEXT DEFAULT 'user'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                crystals_amount REAL,
                uses_left INTEGER,
                expiration_date TEXT,
                created_by INTEGER,
                created_date TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS used_promocodes (
                user_id INTEGER,
                code TEXT,
                used_date TEXT,
                PRIMARY KEY (user_id, code)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_accounts (
                account_id TEXT PRIMARY KEY,
                user_id INTEGER,
                account_name TEXT,
                price REAL,
                status TEXT,
                upload_date TEXT,
                file_path TEXT,
                country TEXT DEFAULT 'Кастом',
                is_admin_account BOOLEAN DEFAULT FALSE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchased_accounts (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                account_id TEXT,
                purchase_date TEXT,
                price REAL
            )
        ''')
        for owner_id in OWNERS:
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, crystals, registration_date, role)
                VALUES (?, ?, ?, ?)
            ''', (owner_id, 0.0, datetime.now().isoformat(), 'owner'))

        for admin_id in ADMINS:
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, crystals, registration_date, role)
                VALUES (?, ?, ?, ?)
            ''', (admin_id, 0.0, datetime.now().isoformat(), 'admin'))

        conn.commit()
        conn.close()
def get_user_balance(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT crystals FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            balance = result[0]
        else:
            cursor.execute('''
                INSERT INTO users (user_id, crystals, registration_date, role)
                VALUES (?, ?, ?, ?)
            ''', (user_id, 0.0, datetime.now().isoformat(), 'user'))
            conn.commit()
            balance = 0.0

        conn.close()
        return balance

def update_balance(user_id, amount):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT crystals FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            new_balance = result[0] + amount
            cursor.execute('UPDATE users SET crystals = ? WHERE user_id = ?', (new_balance, user_id))
        else:
            cursor.execute('''
                INSERT INTO users (user_id, crystals, registration_date, role)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, datetime.now().isoformat(), 'user'))

        conn.commit()
        conn.close()
        return True
def get_user_role(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        else:
            return 'user'
def is_owner(user_id):
    return user_id in OWNERS

def is_admin(user_id):
    return get_user_role(user_id) in ['admin', 'owner']

def is_user(user_id):
    return get_user_role(user_id) == 'user'
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🛒 Магазин")
    btn2 = types.KeyboardButton("📄 Соглашение")
    btn3 = types.KeyboardButton("💰 Баланс")

    if is_admin(user_id):
        btn4 = types.KeyboardButton("📤 Выставить аккаунт")
        btn5 = types.KeyboardButton("⚙️ Админ панель")
        markup.add(btn1, btn2, btn3)
        markup.add(btn4, btn5)
    else:
        btn4 = types.KeyboardButton("📤 Предложить аккаунт")
        markup.add(btn1, btn2, btn3, btn4)

    return markup
def get_accounts_page(page=1, per_page=4):
    accounts = scan_all_accounts()
    total_accounts = len(accounts)
    total_pages = (total_accounts + per_page - 1) // per_page if total_accounts > 0 else 1

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return accounts[start_idx:end_idx], page, total_pages
@bot.message_handler(func=lambda message: message.text == "🛒 Магазин")
def show_shop(message):
    accounts, current_page, total_pages = get_accounts_page()

    if not accounts:
        bot.send_message(message.chat.id, "🛒 Магазин пуст. Аккаунтов пока нет.")
        return

    shop_text = f"🛒 **Доступные аккаунты** (Страница {current_page}/{total_pages}):\n\n"

    for i, account in enumerate(accounts, 1):
        status_icon = "✅" if account.get('status') == 'active' else "❌"

        shop_text += f"{i}. {status_icon} {account['country']} - {account['price']} 💎\n"
        shop_text += f"   └ ID: `{account['name']}`\n\n"

    markup = types.InlineKeyboardMarkup()
    for account in accounts:
        if account.get('status') == 'active':
            btn = types.InlineKeyboardButton(
                f"Купить {account['country']} - {account['price']} 💎",
                callback_data=f"buy_{account['name']}"
            )
            markup.add(btn)
    pagination_buttons = []
    if current_page > 1:
        pagination_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{current_page-1}"))
    if current_page < total_pages:
        pagination_buttons.append(types.InlineKeyboardButton("Вперед ➡️", callback_data=f"page_{current_page+1}"))

    if pagination_buttons:
        markup.add(*pagination_buttons)

    bot.send_message(message.chat.id, shop_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def handle_pagination(call):
    try:
        page = int(call.data.split('_')[1])
        accounts, current_page, total_pages = get_accounts_page(page)

        if not accounts:
            bot.answer_callback_query(call.id, "Нет аккаунтов на этой странице")
            return

        shop_text = f"🛒 **Доступные аккаунты** (Страница {current_page}/{total_pages}):\n\n"

        for i, account in enumerate(accounts, 1):
            status_icon = "✅" if account.get('status') == 'active' else "❌"

            shop_text += f"{i}. {status_icon} **{account['country']}** - {account['price']} 💎\n"
            shop_text += f"   └ ID: `{account['name']}`\n\n"

        markup = types.InlineKeyboardMarkup()
        for account in accounts:
            if account.get('status') == 'active':
                btn = types.InlineKeyboardButton(
                    f"Купить {account['country']} - {account['price']} 💎",
                    callback_data=f"buy_{account['name']}"
                )
                markup.add(btn)
        pagination_buttons = []
        if current_page > 1:
            pagination_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{current_page-1}"))
        if current_page < total_pages:
            pagination_buttons.append(types.InlineKeyboardButton("Вперед ➡️", callback_data=f"page_{current_page+1}"))

        if pagination_buttons:
            markup.add(*pagination_buttons)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=shop_text,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Ошибка при загрузке страницы")
        print(str(e))
@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy_account(call):
    try:
        account_id = call.data[4:]
        user_id = call.from_user.id

        accounts = scan_all_accounts()
        account = next((acc for acc in accounts if acc['name'] == account_id), None)

        if not account:
            bot.answer_callback_query(call.id, "❌ Аккаунт не найден")
            return

        user_balance = get_user_balance(user_id)
        account_price = account['price']

        if user_balance < account_price:
            bot.answer_callback_query(call.id, f"❌ Недостаточно средств. Нужно: {account_price} 💎")
            return

        if account.get('status') != 'active':
            bot.answer_callback_query(call.id, "❌ Аккаунт недоступен для покупки")
            return
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute('SELECT crystals FROM users WHERE user_id = ?', (user_id,))
                current_balance = cursor.fetchone()[0]
                new_balance = current_balance - account_price

                if new_balance < 0:
                    conn.rollback()
                    conn.close()
                    bot.answer_callback_query(call.id, "❌ Недостаточно средств")
                    return

                cursor.execute('UPDATE users SET crystals = ? WHERE user_id = ?', (new_balance, user_id))
                cursor.execute('''
                    INSERT INTO purchased_accounts (user_id, account_id, purchase_date, price)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, account_id, datetime.now().isoformat(), account_price))
                seller_id = account.get('seller_id')
                is_admin_account = account.get('is_admin_account', False)

                if not is_admin_account and seller_id:
                    seller_income = account_price * 0.75
                    cursor.execute('SELECT crystals FROM users WHERE user_id = ?', (seller_id,))
                    seller_balance_result = cursor.fetchone()

                    if seller_balance_result:
                        new_seller_balance = seller_balance_result[0] + seller_income
                        cursor.execute('UPDATE users SET crystals = ? WHERE user_id = ?', (new_seller_balance, seller_id))
                    else:
                        cursor.execute('''
                            INSERT INTO users (user_id, crystals, registration_date, role)
                            VALUES (?, ?, ?, ?)
                        ''', (seller_id, seller_income, datetime.now().isoformat(), 'user'))

                conn.commit()
                zip_filename = f"account_{account_id}_{user_id}.zip"
                zip_path = os.path.join("downloads", zip_filename)
                os.makedirs("downloads", exist_ok=True)
                account_path = account['path']
                tdata_path = os.path.join(account_path, "tdata")

                if create_tdata_zip(tdata_path, zip_path):
                    with open(zip_path, 'rb') as file:
                        bot.send_document(
                            call.message.chat.id,
                            file,
                            caption=f"""
Аккаунт успешно куплен!**

┌ Аккаунт: {account['country']}
├ ID: {account_id}
├ Цена: {account_price} 💎
└ Остаток на балансе: {new_balance:.2f} 💎
"""
                        )
                    os.remove(zip_path)
                    try:
                        if os.path.exists(account_path):
                            shutil.rmtree(account_path)
                        if not is_admin_account:
                            cursor.execute('DELETE FROM user_accounts WHERE account_id = ?', (account_id,))
                            conn.commit()

                    except Exception as e:
                        print(f"Ошибка при удалении аккаунта: {e}")

                else:
                    bot.send_message(call.message.chat.id, "❌ Ошибка при создании архива. Обратитесь к администратору.")
                    cursor.execute('UPDATE users SET crystals = ? WHERE user_id = ?', (current_balance, user_id))
                    conn.commit()

                bot.answer_callback_query(call.id, "✅ Покупка завершена!")

            except Exception as e:
                conn.rollback()
                bot.answer_callback_query(call.id, f"❌ Ошибка при покупке: {str(e)}")
            finally:
                conn.close()

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(func=lambda message: message.text == "📤 Выставить аккаунт" and is_admin(message.from_user.id))
def admin_upload_account(message):
    msg = bot.send_message(message.chat.id, """
📤 **Выставить аккаунт в магазин**

Отправьте архив с tdata папкой.
Аккаунт будет сразу добавлен в магазин после проверки.
    """)
    bot.register_next_step_handler(msg, process_admin_upload)

def process_admin_upload(message):
    user_id = message.from_user.id

    if message.document:
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

          
            temp_dir = f"temp_admin_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.makedirs(temp_dir, exist_ok=True)

            zip_path = os.path.join(temp_dir, "uploaded.zip")
            extract_path = os.path.join(temp_dir, "extracted")


            with open(zip_path, 'wb') as f:
                f.write(downloaded_file)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)


            tdata_path = find_tdata_folder(extract_path)

            if tdata_path:
              
                bot.send_message(message.chat.id, "🔍 Проверяю валидность аккаунта...")
                validity_result = check_account_status(tdata_path)

                if validity_result['status'] == 'active':

                    msg = bot.send_message(message.chat.id, f"""
✅ **Аккаунт прошел проверку!**

{validity_result['details']}

Введите данные в формате:
`цена страна описание`

Пример: `150 США Аккаунт премиум`
                    """)
                    bot.register_next_step_handler(msg, process_admin_account_data, tdata_path, temp_dir)

                else:
                    bot.send_message(message.chat.id, f"""
❌ **Аккаунт не прошел проверку**

Причина: {validity_result['details']}
                    """)
                    shutil.rmtree(temp_dir, ignore_errors=True)
            else:
                bot.send_message(message.chat.id, "❌ В архиве не найдена папка tdata")
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка обработки архива: {str(e)}")
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте архив с tdata")

def process_admin_account_data(message, tdata_path, temp_dir):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 2:
            raise ValueError

        price = float(parts[0])
        country = parts[1]
        description = parts[2] if len(parts) > 2 else "Аккаунт администрации"

        if price <= 0:
            bot.send_message(message.chat.id, "❌ Цена должна быть положительным числом")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return

    
        account_id = f"admin_{message.from_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        account_path = os.path.join("tdatas", account_id)
        os.makedirs(account_path, exist_ok=True)


        shutil.copytree(tdata_path, os.path.join(account_path, "tdata"))


        market_data = {
            'price': price,
            'country': country,
            'description': description,
            'seller_id': message.from_user.id,
            'is_admin_account': True
        }

        with open(os.path.join(account_path, "market.json"), 'w', encoding='utf-8') as f:
            json.dump(market_data, f, ensure_ascii=False, indent=2)

        shutil.rmtree(temp_dir, ignore_errors=True)

        bot.send_message(message.chat.id, f"""
✅ **Аккаунт добавлен в магазин!**

┌ **Цена:** {price} 💎
├ **Страна:** {country}
└ **Описание:** {description}

Аккаунт теперь доступен для покупки в магазине.
        """)

    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат данных. Используйте: `цена страна описание`")
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")
        shutil.rmtree(temp_dir, ignore_errors=True)


def generate_promo_code(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@bot.callback_query_handler(func=lambda call: call.data == "admin_create_promo")
def admin_create_promo(call):
    msg = bot.send_message(call.message.chat.id, """
🎁 **Создание промокода**

Введите данные в формате:
`количество_кристаллов количество_использований срок_действия_в_днях`

Пример: `100 5 30` - промокод на 100 кристаллов, 5 использований, срок 30 дней
    """)
    bot.register_next_step_handler(msg, process_promo_creation)

def process_promo_creation(message):
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError

        crystals_amount = float(parts[0])
        uses_left = int(parts[1])
        days_valid = int(parts[2])

        if crystals_amount <= 0 or uses_left <= 0 or days_valid <= 0:
            raise ValueError

      
        promo_code = generate_promo_code()
        expiration_date = (datetime.now() + timedelta(days=days_valid)).isoformat()

 
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO promocodes (code, crystals_amount, uses_left, expiration_date, created_by, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (promo_code, crystals_amount, uses_left, expiration_date, message.from_user.id, datetime.now().isoformat()))
            conn.commit()
            conn.close()

        bot.send_message(message.chat.id, f"""
✅ **Промокод создан!**

┌ **Код:** `{promo_code}`
├ **Кристаллы:** {crystals_amount} 💎
├ **Использований:** {uses_left}
├ **Срок действия:** {days_valid} дней
└ **Активировать до:** {datetime.fromisoformat(expiration_date).strftime('%d.%m.%Y %H:%M')}

Поделитесь этим кодом с пользователями.
        """, parse_mode="Markdown")

    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат данных. Используйте: `кристаллы использования дни`")


def validate_promo_code(code):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT crystals_amount, uses_left, expiration_date
            FROM promocodes
            WHERE code = ? AND uses_left > 0 AND expiration_date > ?
        ''', (code, datetime.now().isoformat()))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'valid': True,
                'crystals_amount': result[0],
                'uses_left': result[1],
                'expiration_date': result[2]
            }
        else:
            return {'valid': False}

def use_promo_code(user_id, code):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
          
            cursor.execute("BEGIN TRANSACTION")

         
            cursor.execute('SELECT * FROM used_promocodes WHERE user_id = ? AND code = ?', (user_id, code))
            if cursor.fetchone():
                conn.rollback()
                conn.close()
                return {'success': False, 'message': 'Вы уже использовали этот промокод'}

            cursor.execute('SELECT uses_left, crystals_amount FROM promocodes WHERE code = ?', (code,))
            promo_result = cursor.fetchone()

            if not promo_result:
                conn.rollback()
                conn.close()
                return {'success': False, 'message': 'Промокод не найден'}

            uses_left, crystals_amount = promo_result

            if uses_left <= 0:
                conn.rollback()
                conn.close()
                return {'success': False, 'message': 'Промокод закончился'}

            cursor.execute('UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?', (code,))

            cursor.execute('SELECT crystals FROM users WHERE user_id = ?', (user_id,))
            user_result = cursor.fetchone()

            if user_result:
                new_balance = user_result[0] + crystals_amount
                cursor.execute('UPDATE users SET crystals = ? WHERE user_id = ?', (new_balance, user_id))
            else:
                cursor.execute('''
                    INSERT INTO users (user_id, crystals, registration_date, role)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, crystals_amount, datetime.now().isoformat(), 'user'))


            cursor.execute('''
                INSERT INTO used_promocodes (user_id, code, used_date)
                VALUES (?, ?, ?)
            ''', (user_id, code, datetime.now().isoformat()))

            conn.commit()
            return {'success': True, 'crystals_amount': crystals_amount}

        except sqlite3.Error as e:
            conn.rollback()
            return {'success': False, 'message': f'Ошибка базы данных: {str(e)}'}
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Неизвестная ошибка: {str(e)}'}
        finally:
            conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "activate_promo")
def activate_promo(call):
    msg = bot.send_message(call.message.chat.id, "Введите промокод:")
    bot.register_next_step_handler(msg, process_promo_activation)

def process_promo_activation(message):
    user_id = message.from_user.id
    promo_code = message.text.strip().upper()

    if not promo_code:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите промокод")
        return

    validation = validate_promo_code(promo_code)

    if not validation['valid']:
        bot.send_message(message.chat.id, "❌ Промокод недействителен, закончился срок действия или использования")
        return

    result = use_promo_code(user_id, promo_code)

    if result['success']:
        bot.send_message(message.chat.id, f"""
✅ **Промокод активирован!**

На ваш баланс начислено: {result['crystals_amount']} 💎
Текущий баланс: {get_user_balance(user_id):.2f} 💎
        """)
    else:
        bot.send_message(message.chat.id, f"❌ {result['message']}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_roles" and is_owner(call.from_user.id))
def admin_roles(call):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("👑 Назначить админа", callback_data="admin_give_admin")
    btn2 = types.InlineKeyboardButton("🔻 Снять админа", callback_data="admin_remove_admin")
    btn3 = types.InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")
    markup.add(btn1, btn2)
    markup.add(btn3)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="👑 **Управление ролями**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_give_admin")
def give_admin(call):
    msg = bot.send_message(call.message.chat.id, "Введите ID пользователя для назначения админом:")
    bot.register_next_step_handler(msg, process_give_admin)

def process_give_admin(message):
    try:
        user_id = int(message.text)

        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET role = "admin" WHERE user_id = ?', (user_id,))

            if cursor.rowcount > 0:
                bot.send_message(message.chat.id, f"✅ Пользователь {user_id} назначен админом")
                try:
                    bot.send_message(user_id, "🎉 Вам выданы права администратора!")
                except:
                    pass
            else:
                cursor.execute('''
                    INSERT INTO users (user_id, crystals, registration_date, role)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, 0.0, datetime.now().isoformat(), 'admin'))
                conn.commit()
                bot.send_message(message.chat.id, f"✅ Пользователь {user_id} создан и назначен админом")

                try:
                    bot.send_message(user_id, "🎉 Вам выданы права администратора!")
                except:
                    pass

            conn.commit()
            conn.close()

    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный ID пользователя")

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_admin")
def remove_admin(call):
    msg = bot.send_message(call.message.chat.id, "Введите ID админа для снятия прав:")
    bot.register_next_step_handler(msg, process_remove_admin)

def process_remove_admin(message):
    try:
        user_id = int(message.text)

        if user_id in OWNERS:
            bot.send_message(message.chat.id, "❌ Нельзя снять права у владельца")
            return

        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET role = "user" WHERE user_id = ? AND role = "admin"', (user_id,))

            if cursor.rowcount > 0:
                bot.send_message(message.chat.id, f"✅ Права админа сняты у пользователя {user_id}")
                try:
                    bot.send_message(user_id, "ℹ️ Ваши права администратора были сняты")
                except:
                    pass
            else:
                bot.send_message(message.chat.id, f"❌ Пользователь {user_id} не является админом")

            conn.commit()
            conn.close()

    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный ID пользователя")

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
        total_admins = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM purchased_accounts')
        total_sales = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(price) FROM purchased_accounts')
        total_revenue = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM promocodes')
        total_promocodes = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM used_promocodes')
        total_used_promocodes = cursor.fetchone()[0]

        conn.close()

    accounts = scan_all_accounts()
    available_accounts = len(accounts)
    BalanceOnBOT = EasyGiftSend.get_balance()
    stats_text = f"""
📊 **Статистика системы**

┌ **Пользователей:** {total_users}
├ **Админов:** {total_admins}
├ **Продаж:** {total_sales}
├ **Общий доход:** {total_revenue:.2f} 💎
├ **Создано промокодов:** {total_promocodes}
├ **Активировано промокодов:** {total_used_promocodes}
├ **Звезды в боте за все время:** {BalanceOnBOT}
└ **Аккаунтов в магазине:** {available_accounts}
    """

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")
    markup.add(btn)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=stats_text,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_moderation")
def admin_moderation(call):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_accounts WHERE status = "moderation"')
        pending_accounts = cursor.fetchall()
        conn.close()

    if not pending_accounts:
        bot.answer_callback_query(call.id, "Нет аккаунтов на модерации")
        return

    moderation_text = "📦 **Аккаунты на модерации:**\n\n"

    for account in pending_accounts:
        account_id, user_id, account_name, price, status, upload_date, file_path, country, is_admin_account = account
        moderation_text += f"┌ **ID:** `{account_id}`\n"
        moderation_text += f"├ **Продавец:** {user_id}\n"
        moderation_text += f"├ **Цена:** {price} 💎\n"
        moderation_text += f"├ **Страна:** {country}\n"
        moderation_text += f"└ **Дата:** {datetime.fromisoformat(upload_date).strftime('%d.%m.%Y %H:%M')}\n\n"

    markup = types.InlineKeyboardMarkup()

    for account in pending_accounts:
        account_id = account[0]
        btn_approve = types.InlineKeyboardButton(f"✅ {account_id}", callback_data=f"approve_{account_id}")
        btn_reject = types.InlineKeyboardButton(f"❌ {account_id}", callback_data=f"reject_{account_id}")
        markup.add(btn_approve, btn_reject)

    btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")
    markup.add(btn_back)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=moderation_text,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_moderation_decision(call):
    action, account_id = call.data.split('_', 1)

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_accounts WHERE account_id = ?', (account_id,))
        account = cursor.fetchone()

        if not account:
            bot.answer_callback_query(call.id, "Аккаунт не найден")
            conn.close()
            return

        account_id, user_id, account_name, price, status, upload_date, file_path, country, is_admin_account = account

        if action == 'approve':
            cursor.execute('UPDATE user_accounts SET status = "approved" WHERE account_id = ?', (account_id,))
            old_path = file_path
            new_path = os.path.join("tdatas", account_id)

            os.makedirs("tdatas", exist_ok=True)
            if os.path.exists(old_path):
                shutil.move(old_path, new_path)

                cursor.execute('UPDATE user_accounts SET file_path = ? WHERE account_id = ?', (new_path, account_id))
                market_data = {
                    'price': price,
                    'country': country,
                    'description': f"Аккаунт пользователя {user_id}",
                    'seller_id': user_id,
                    'is_admin_account': False
                }

                with open(os.path.join(new_path, "market.json"), 'w', encoding='utf-8') as f:
                    json.dump(market_data, f, ensure_ascii=False, indent=2)


            try:
                bot.send_message(user_id, f"""
✅ **Ваш аккаунт одобрен!**

Аккаунт {country} за {price} 💎 теперь доступен в магазине.
После продажи вы получите {price * 0.75} 💎 на баланс.
                """)
            except:
                pass

            bot.answer_callback_query(call.id, "✅ Аккаунт одобрен")

        else:  # reject
            
            cursor.execute('DELETE FROM user_accounts WHERE account_id = ?', (account_id,))
            if os.path.exists(file_path):
                shutil.rmtree(file_path, ignore_errors=True)


            try:
                bot.send_message(user_id, f"""
❌ **Ваш аккаунт отклонен**

Аккаунт {country} за {price} 💎 не прошел модерацию.
Возможно, аккаунт нерабочий или содержит ошибки.
                """)
            except:
                pass

            bot.answer_callback_query(call.id, "❌ Аккаунт отклонен")

        conn.commit()
        conn.close()

   
    admin_moderation(call)



def find_tdata_folder(path):
   
    if not os.path.exists(path):
        return None

    try:
     
        if 'tdata' in os.listdir(path):
            tdata_path = os.path.join(path, 'tdata')
            if os.path.isdir(tdata_path) and is_valid_tdata(tdata_path):
                return tdata_path

       
        for root, dirs, files in os.walk(path):
            if 'tdata' in dirs:
                tdata_path = os.path.join(root, 'tdata')
                if os.path.isdir(tdata_path) and is_valid_tdata(tdata_path):
                    return tdata_path

        return None
    except Exception as e:
        print(f"Ошибка поиска tdata: {e}")
        return None

def is_valid_tdata(tdata_path):
    
    try:
        if not os.path.exists(tdata_path) or not os.path.isdir(tdata_path):
            return False

        contents = os.listdir(tdata_path)


        required_items = [
            'key_datas',  
            'dbs',        
            'maps',       
        ]

     
        has_required = any(item in contents for item in required_items)

        has_sessions = any(f.endswith('.s') for f in contents)

        has_tdata_files = any(f.startswith('tdata') for f in contents)

        return has_required or has_sessions or has_tdata_files

    except Exception as e:
        print(f"Ошибка проверки tdata: {e}")
        return False

def check_account_status(tdata_path):
  
    if not tdata_path or not os.path.exists(tdata_path):
        return {'status': 'invalid', 'details': 'Папка tdata не найдена'}

    if not is_valid_tdata(tdata_path):
        return {'status': 'invalid', 'details': 'Невалидная структура tdata папки'}

    try:
        return basic_tdata_check(tdata_path)
    except Exception as e:
        print(f"Проверка не удалась: {e}")
        return {'status': 'error', 'details': f'Ошибка проверки: {str(e)}'}

def basic_tdata_check(tdata_path):
    try:
        contents = os.listdir(tdata_path)

        key_elements = [
            'key_datas',  
            'dbs',        
            'maps',       
            'user_data',  
        ]

        found_elements = [elem for elem in key_elements if elem in contents]

        if not found_elements:
          
            session_files = [f for f in contents if f.endswith('.s')]
            if session_files:
                return {'status': 'active', 'details': f'Найдены session файлы: {len(session_files)} шт.'}
            else:
                return {'status': 'invalid', 'details': 'Не найдены ключевые элементы tdata'}

        
        total_size = 0
        for item in found_elements:
            item_path = os.path.join(tdata_path, item)
            if os.path.exists(item_path):
                if os.path.isfile(item_path):
                    total_size += os.path.getsize(item_path)
                else:
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)

        if total_size < 100:  
            return {'status': 'invalid', 'details': 'Недостаточно данных в tdata'}

        return {
            'status': 'active',
            'details': f'Базовая проверка пройдена. Найдены: {", ".join(found_elements)}'
        }

    except Exception as e:
        return {'status': 'error', 'details': f'Ошибка базовой проверки: {str(e)}'}

def create_tdata_zip(tdata_path, zip_path):
   
    if not tdata_path or not os.path.exists(tdata_path):
        return False

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(tdata_path):
                for file in files:
                    file_path = os.path.join(root, file)

                   
                    if os.path.getsize(file_path) > 100 * 1024 * 1024:  # 100MB limit
                        continue

           
                    if file.endswith(('.exe', '.dll', '.bat', '.cmd')):
                        continue

                    arcname = os.path.relpath(file_path, os.path.dirname(tdata_path))
                    zipf.write(file_path, arcname)

       
        if os.path.exists(zip_path) and os.path.getsize(zip_path) > 0:
            return True
        else:
            return False

    except Exception as e:
        print(f"Ошибка создания архива: {e}")
        return False

def scan_all_accounts():

    accounts = []
    tdatas_dir = "tdatas"

    if not os.path.exists(tdatas_dir):
        return accounts

    try:
        for account_folder in os.listdir(tdatas_dir):
            account_path = os.path.join(tdatas_dir, account_folder)
            if os.path.isdir(account_path):
                market_file = os.path.join(account_path, "market.json")
                tdata_folder = os.path.join(account_path, "tdata")

             
                if os.path.exists(market_file) and os.path.exists(tdata_folder):
                    try:
                        with open(market_file, 'r', encoding='utf-8') as f:
                            market_data = json.load(f)

                 
                        if 'price' in market_data and 'country' in market_data:
                           
                            status = check_account_status(tdata_folder)

                            account_info = {
                                'name': account_folder,
                                'path': account_path,
                                'price': float(market_data.get('price', 0)),
                                'country': market_data.get('country', 'Unknown'),
                                'status': status['status']
                            }

                            
                            if 'seller_id' in market_data:
                                account_info['seller_id'] = market_data['seller_id']
                            if 'is_admin_account' in market_data:
                                account_info['is_admin_account'] = market_data['is_admin_account']

                            accounts.append(account_info)
                    except Exception as e:
                        print(f"Ошибка чтения market.json для {account_folder}: {e}")
                        continue
    except Exception as e:
        print(f"Ошибка сканирования аккаунтов: {e}")


    return [acc for acc in accounts if acc.get('status') == 'active']

def validate_user_upload(file_path, user_id):
    try:
       
        if os.path.getsize(file_path) > 10 * 1024 * 1024:
            return {'valid': False, 'message': 'Файл слишком большой (максимум 10MB)'}


        if not file_path.lower().endswith('.zip'):
            return {'valid': False, 'message': 'Файл должен быть в формате ZIP'}

        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()

            has_tdata = any('tdata/' in f for f in file_list)
            if not has_tdata:
                return {'valid': False, 'message': 'В архиве не найдена папка tdata'}


            for file in file_list:
                if file.endswith(('.exe', '.py', '.dll', '.bat', '.cmd', '.vbs', '.js')):
                    return {'valid': False, 'message': 'Архив содержит запрещенные файлы'}

        return {'valid': True, 'message': 'Файл прошел проверку'}

    except Exception as e:
        return {'valid': False, 'message': f'Ошибка проверки файла: {str(e)}'}


@bot.message_handler(func=lambda message: message.text == "💰 Баланс")
def show_balance(message):
    user_id = message.from_user.id
    balance = get_user_balance(user_id)

    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🎁 Активировать промокод", callback_data="activate_promo")
    btn2 = types.InlineKeyboardButton("Купить Кристаллы", callback_data="topup_stars")
    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        f"💰 **Ваш баланс:** {balance:.2f} 💎\n\nВыберите способ пополнения:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "topup_stars")
def topup_stars(call):
    user_id = call.from_user.id
    balance = get_user_balance(user_id) 
    markup = types.InlineKeyboardMarkup()
 
    amounts = [1, 5, 10, 30, 100, 500, 1000, 1500, 10000]
    buttons = []
    for amount in amounts:
        buttons.append(types.InlineKeyboardButton(f"{amount} ⭐", callback_data=f"stars_{amount}"))
        
        if len(buttons) == 2:
            markup.add(*buttons)
            buttons = []
    if buttons:
        markup.add(*buttons)
    btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_balance")
    markup.add(btn_back)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"Выберите сумму для пополнения баланса:\n\nОбратите внимание, что покупая больше 30 кристаллов вам будет отдан подарок в виде благодарности.\nPS:\nПодарок нельзя перевести в звезды",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('stars_'))
def handle_stars_amount(call):
    amount = int(call.data.split('_')[1])
    user_id = call.from_user.id


    prices = [types.LabeledPrice(label=f"Пополнение на {amount} кристаллов", amount=amount)]
    markup = types.InlineKeyboardMarkup()
    pay_button = types.InlineKeyboardButton("Пополнить ⭐", pay=True)
    markup.add(pay_button)

    try:
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=f"Пополнение баланса",
            description=f"На ваш баланс будет зачислено {amount} кристаллов.",
            invoice_payload=f"topup_{user_id}_{amount}", 
            provider_token="",
            currency="XTR",  
            prices=prices,
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Произошла ошибка при создании счета: {e}")


@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    payment_info = message.successful_payment
    user_id = message.from_user.id
    payload_parts = payment_info.invoice_payload.split('_')
    amount = int(payload_parts[2])
    evaluate_donation_bonus(amount, user_id)
    bot.send_message(message.chat.id,f"Спасибо за пополнение {amount} звёзд, держите ваш обещанный подарок!")
    update_balance(user_id, amount) 
    new_balance = get_user_balance(user_id)

    bot.send_message(
        message.chat.id,
        f"✅ Оплата прошла успешно! Ваш баланс пополнен на {amount} кристаллов.\n"
        f"💰 Текущий баланс: {new_balance} 💎"
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_balance")
def back_to_balance(call):
    user_id = call.from_user.id
    balance = get_user_balance(user_id)

    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🎁 Активировать промокод", callback_data="activate_promo")
    btn2 = types.InlineKeyboardButton("Купить Кристаллы", callback_data="topup_stars")
    markup.add(btn1, btn2)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"💰 **Ваш баланс:** {balance:.2f} 💎\n\nВыберите способ пополнения:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

user_data = {}

@bot.message_handler(func=lambda message: message.text == "📤 Предложить аккаунт" and not is_admin(message.from_user.id))
def user_upload_account(message):
    msg = bot.send_message(message.chat.id, """
📤 **Предложить аккаунт на продажу**

Отправьте ZIP архив с папкой tdata аккаунта.

⚠️ **Требования:**
- Размер архива не более 50MB
- В архиве должна быть папка tdata
- Аккаунт должен быть рабочим

После проверки модератором аккаунт будет добавлен в магазин.
Вы получите 75% от стоимости продажи.
    """)
    bot.register_next_step_handler(msg, process_user_upload)

def process_user_upload(message):
    user_id = message.from_user.id

    if message.document:
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

           
            temp_dir = f"temp_user_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.makedirs(temp_dir, exist_ok=True)

            zip_path = os.path.join(temp_dir, "uploaded.zip")

            
            with open(zip_path, 'wb') as f:
                f.write(downloaded_file)

          
            validation = validate_user_upload(zip_path, user_id)
            if not validation['valid']:
                bot.send_message(message.chat.id, f"❌ {validation['message']}")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

            msg = bot.send_message(message.chat.id, """
✅ **Архив прошел проверку!**

Введите данные аккаунта в формате:
`цена страна`

Пример: `100 США`
            """)
            bot.register_next_step_handler(msg, process_user_account_data, temp_dir, zip_path)

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка обработки файла: {str(e)}")
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте ZIP архив")

def process_user_account_data(message, temp_dir, zip_path):
    try:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            raise ValueError

        price = float(parts[0])
        country = parts[1]

        if price <= 0:
            bot.send_message(message.chat.id, "❌ Цена должна быть положительным числом")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return

        if price > 10000:
            bot.send_message(message.chat.id, "❌ Слишком высокая цена (максимум 10000 💎)")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return

      
        account_id = f"user_{message.from_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        account_path = os.path.join("moderation", account_id)
        os.makedirs(account_path, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(account_path)


        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_accounts (account_id, user_id, account_name, price, status, upload_date, file_path, country)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (account_id, message.from_user.id, f"Аккаунт {country}", price, "moderation",
                  datetime.now().isoformat(), account_path, country))
            conn.commit()
            conn.close()


        shutil.rmtree(temp_dir, ignore_errors=True)

        bot.send_message(message.chat.id, f"""
✅ **Аккаунт отправлен на модерацию!**

┌ **Цена:** {price} 💎
├ **Страна:** {country}
└ **Ваш потенциальный доход:** {price * 0.75} 💎

Аккаунт будет проверен администратором и добавлен в магазине.
        """)


        for admin_id in ADMINS:
            try:
                bot.send_message(admin_id, f"""
📦 **Новый аккаунт на модерации**

┌ **Продавец:** {message.from_user.id}
├ **Цена:** {price} 💎
├ **Страна:** {country}
└ **ID аккаунта:** `{account_id}`
                """, parse_mode="Markdown")
            except:
                pass

    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат данных. Используйте: `цена страна`")
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")
        shutil.rmtree(temp_dir, ignore_errors=True)

@bot.message_handler(func=lambda message: message.text == "📄 Соглашение")
def show_agreement(message):
    agreement_text = """
📄 **Пользовательское соглашение**

1. **Общие положения**
   - Бот предназначен для торговли Telegram аккаунтами
   - Администрация не несет ответственности за содержимое аккаунтов

2. **Правила использования**
   - Запрещена продажа нерабочих аккаунтов
   - Запрещено обманывать покупателей
   - Администрация вправе отказать в обслуживании

3. **Финансовые условия**
   - Продавец получает 75% от стоимости аккаунта
   - Комиссия системы составляет 25%
   - Баланс можно вывести через администратора

4. **Модерация**
   - Все аккаунты проходят проверку
   - Администрация вправе отказать без объяснения причин

Нажимая "Принимаю", вы соглашаетесь с условиями.
    """

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("✅ Принимаю", callback_data="accept_agreement")
    markup.add(btn)

    bot.send_message(message.chat.id, agreement_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "accept_agreement")
def accept_agreement(call):
    bot.answer_callback_query(call.id, "✅ Соглашение принято!")
    bot.send_message(call.message.chat.id, "Теперь вы можете пользоваться всеми функциями бота!")

@bot.message_handler(func=lambda message: message.text == "⚙️ Админ панель" and is_admin(message.from_user.id))
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ У вас нет прав доступа")
        return

    admin_text = "⚙️ **Админ панель**\n\nВыберите раздел:"

    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    btn2 = types.InlineKeyboardButton("🎁 Создать промокод", callback_data="admin_create_promo")
    btn3 = types.InlineKeyboardButton("📦 Модерация аккаунтов", callback_data="admin_moderation")

    markup.add(btn1, btn2, btn3)

    if is_owner(message.from_user.id):
        btn4 = types.InlineKeyboardButton("👑 Управление ролями", callback_data="admin_roles")
        markup.add(btn4)

    bot.send_message(message.chat.id, admin_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    admin_panel(call.message)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    welcome_text = "Добро пожаловать в магазин Telegram аккаунтов! Выберите раздел:"

    is_new_user = check_and_register_user(user_id)

    
    if is_new_user:
        promo_code = generate_promo_code()
        crystals_amount = random.randint(5, 10) 


        save_welcome_promo(promo_code, crystals_amount, user_id)

       
        welcome_text += f"\n\n🎁 **Вам выдан приветственный промокод на {crystals_amount} кристаллов:**\n`{promo_code}`\n\nИспользуйте его в разделе '💰 Баланс' -> '🎁 Активировать промокод'"

    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(user_id))

def check_and_register_user(user_id):

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

     
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
          
            conn.close()
            return False
        else:
 
            cursor.execute('''
                INSERT INTO users (user_id, crystals, registration_date, role)
                VALUES (?, ?, ?, ?)
            ''', (user_id, 0.0, datetime.now().isoformat(), 'user'))
            conn.commit()
            conn.close()
            return True

def save_welcome_promo(promo_code, crystals_amount, created_by):
    expiration_date = (datetime.now() + timedelta(days=7)).isoformat()  
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO promocodes (code, crystals_amount, uses_left, expiration_date, created_by, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (promo_code, crystals_amount, 1, expiration_date, created_by, datetime.now().isoformat()))
        conn.commit()
        conn.close()
init_db()
for folder in ["tdatas", "downloads", "moderation"]:
    os.makedirs(folder, exist_ok=True)

if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
