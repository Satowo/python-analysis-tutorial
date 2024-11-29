"""
Priceクラスを定義
"""

class Price:
    def __init__(self, user_type: str, price_day: str, start_time: str, end_time: str, system: str, price: int):
        self.user_type = user_type
        self.price_day = price_day
        self.start_time = start_time
        self.end_time = end_time
        self.system = system
        self.price = price

    def __repr__(self):
        return f"Price(user_type={self.user_type}, price_day={self.price_day}, start_time={self.start_time}, end_time={self.end_time}, system={self.system}, price={self.price})"
