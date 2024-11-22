from enum import Enum

class UserType(Enum):
    STUDENT_MEMBER = "student_member"
    STUDENT_NON_MEMBER = "student_non_member"
    GENERAL_MEMBER = "general_member"
    SENIOR = "senior"
    GENERAL = "general"

class PriceTime(Enum):
    NOON_THIRTY = "昼30分"
    NOON_FREE = "昼フリー"
    EVENING_FREE = "夕方フリー"
    NIGHT_THIRTY = "夜30分"
    NIGHT_FREE = "夜フリー"
    MIDNIGHT_FREE = "深夜フリー"
    
class PriceDay(Enum):
    WEEKDAY = "平日"
    HOLIDAY = "土日祝"
    FRIDAY_HOLIDAY = "金土日祝"
    FRIDAY_SATURDAY_BEFORE_HOLIDAY = "金土祝前"
    FRIDAY_HOLIDAY_BEFORE_HOLIDAY = "金土日祝祝前"

class Price:
    def __init__(self, user_type: str, price_day: str, price_time: str, price: int):
        self.user_type = user_type
        self.price_day = price_day
        self.price_time = price_time
        self.price = price

    def __repr__(self):
        return f"Price(user_type={self.user_type}, price_day={self.price_day}, price_time={self.price_time}, price={self.price})"
