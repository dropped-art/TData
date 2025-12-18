import requests

class EasyGiftSend:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
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
        url = f"{self.base_url}/{method}"

        try:
            if method == "sendGift":
                query_params = "&".join([f"{k}={v}" for k, v in params.items()])
                url_with_params = f"{url}?{query_params}"
                response = requests.get(url_with_params, timeout=30)
            else:
                # Для других методов используем стандартный GET
                response = requests.get(url, timeout=30)

            result = response.json()
            return result

        except Exception as e:
            error_msg = f"Request error: {str(e)}"
            return {"ok": False, "description": error_msg}

    def get_balance(self):
        try:
            result = self._make_api_request("getMyStarBalance")
            if result.get("ok"):
                balance = result.get("result", {}).get("amount", 0)
                return balance
            else:
                return 0
        except Exception as e:
           
            return 0

    def send_gift(self, gift_emoji, user_id=None, chat_id=None, message=""):
        if gift_emoji not in self.gifts:
            return {"ok": False, "description": f"Подарок '{gift_emoji}' не найден"}

        gift_id = self.gifts[gift_emoji]
        price = self.gift_prices.get(gift_emoji, 0)
        balance = self.get_balance()
        if balance < price:
            return {"ok": False, "description": f"Недостаточно средств. Нужно: {price}, есть: {balance}"}

        params = {
            "gift_id": gift_id,
            "user_id": user_id
        }

        if message:
            params["text"] = message[:128]
        return self._make_api_request("sendGift", params)

    def can_afford_gift(self, gift_emoji):
        price = self.get_gift_price(gift_emoji)
        balance = self.get_balance()
        can_afford = balance >= price
        return can_afford

    def get_gift_price(self, gift_emoji):
        return self.gift_prices.get(gift_emoji, 0)

    def list_available_gifts(self):
        return [
            {"emoji": emoji, "price": price, "id": gift_id}
            for emoji, gift_id in self.gifts.items()
            for price in [self.gift_prices.get(emoji, 0)]
        ]
