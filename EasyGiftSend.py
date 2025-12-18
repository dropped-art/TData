# EasyGiftSend.py
import requests

class EasyGiftSend:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

        # Словарь подарков
        self.gifts = {
            "💝": "5170145012310081615",
            "🧸": "5170233102089322756",
            "🎁": "5170250947678437525",
            "🌹": "5168103777563050263",
            "🎂": "5170144170496491616",
            "💐": "5170314324215857265",
            "🚀": "5170564780938756245",
            "🏆": "5168043875654172773",
            "💍": "5170690322832818290",
            "💎": "5170521118301225164",
            "🍾": "6028601630662853006"
        }

        self.gift_prices = {
            "💝": 15, "🧸": 15, "🎁": 25, "🌹": 25, "🎂": 50,
            "💐": 50, "🚀": 50, "🍾": 50, "🏆": 100, "💍": 100, "💎": 100
        }

    def _make_api_request(self, method, params=None):
        """Улучшенный метод для выполнения запросов"""
        url = f"{self.base_url}/{method}"

        try:
            print(f"🟡 API запрос: {method}, параметры: {params}")

            if method == "sendGift":
                # Для sendGift используем GET с параметрами в URL
                query_params = "&".join([f"{k}={v}" for k, v in params.items()])
                url_with_params = f"{url}?{query_params}"
                print(f"🟡 Final URL: {url_with_params}")
                response = requests.get(url_with_params, timeout=30)
            else:
                # Для других методов используем стандартный GET
                response = requests.get(url, timeout=30)

            result = response.json()
            print(f"🟢 API ответ: {result}")
            return result

        except Exception as e:
            error_msg = f"Request error: {str(e)}"
            print(f"🔴 Ошибка API: {error_msg}")
            return {"ok": False, "description": error_msg}

    def get_balance(self):
        """Получение баланса - исправленная версия"""
        try:
            result = self._make_api_request("getMyStarBalance")
            if result.get("ok"):
                # Баланс находится в result['result']['amount']
                balance = result.get("result", {}).get("amount", 0)
                print(f"💰 Получен баланс: {balance}")
                return balance
            else:
                print(f"🔴 Ошибка получения баланса: {result}")
                return 0
        except Exception as e:
            print(f"🔴 Исключение при получении баланса: {e}")
            return 0

    def send_gift(self, gift_emoji, user_id=None, chat_id=None, message=""):
        """Отправка подарка"""
        if gift_emoji not in self.gifts:
            return {"ok": False, "description": f"Подарок '{gift_emoji}' не найден"}

        gift_id = self.gifts[gift_emoji]
        price = self.gift_prices.get(gift_emoji, 0)

        print(f"🎁 Попытка отправить подарок {gift_emoji} (ID: {gift_id}) стоимостью {price} пользователю {user_id}")

        # Проверяем баланс
        balance = self.get_balance()
        if balance < price:
            return {"ok": False, "description": f"Недостаточно средств. Нужно: {price}, есть: {balance}"}

        params = {
            "gift_id": gift_id,
            "user_id": user_id
        }

        # Добавляем текст, если он есть
        if message:
            params["text"] = message[:128]

        print(f"🟡 Параметры для sendGift: {params}")
        return self._make_api_request("sendGift", params)

    def can_afford_gift(self, gift_emoji):
        """Проверка возможности отправки подарка"""
        price = self.get_gift_price(gift_emoji)
        balance = self.get_balance()
        can_afford = balance >= price
        print(f"💳 Проверка средств: подарок {gift_emoji} - цена {price}, баланс {balance}, возможно: {can_afford}")
        return can_afford

    def get_gift_price(self, gift_emoji):
        return self.gift_prices.get(gift_emoji, 0)

    def list_available_gifts(self):
        """Список доступных подарков"""
        return [
            {"emoji": emoji, "price": price, "id": gift_id}
            for emoji, gift_id in self.gifts.items()
            for price in [self.gift_prices.get(emoji, 0)]
        ]