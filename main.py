"""
ジャンカラの各店舗の料金表を取得するスクリプト
"""

import time
from typing import Union

import requests
from lxml import html

from domain.shop import Shop
from util import get_prices, get_shop_name, get_shop_address

def main():
    number_of_shops = 254
    for shop_number in range(1, number_of_shops):
        shop = get_shop(shop_number)

        if (shop_number + 1) % 5 == 0:
            print("Sleeping for 3 seconds...")
            time.sleep(3)
        
        if shop is None:
            continue
        
        print(f"Shop number: {shop_number}")
        print(shop)

def get_shop(shop_number: int) -> Union[Shop, None]:
    """
    店舗番号から店舗情報を取得
    """
    URL = f'https://jankara.ne.jp/shop/{shop_number}'
    
    try:
        response = requests.get(URL)
        tree = html.fromstring(response.text)

        shop_name = get_shop_name(tree)

        address = get_shop_address(tree)
        prices = get_prices(tree)

        return Shop(name=shop_name, address=address, prices=prices)
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    main()
