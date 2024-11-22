"""
ジャンカラの各店舗の料金表を取得するスクリプト
"""

import time

from util import get_shop, create_shop_csv

def main():
    number_of_shops = 254
    result_shops = []
    for shop_number in range(1, number_of_shops):
        shop = get_shop(shop_number)

        if (shop_number) % 5 == 0:
            print("Sleeping for 3 seconds...")
            time.sleep(3)

        if shop is None:
            continue

        result_shops.append(shop)

    create_shop_csv(result_shops, "jankara.csv")

if __name__ == "__main__":
    main()
