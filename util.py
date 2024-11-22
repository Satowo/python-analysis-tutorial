"""
価格表のHTMLから価格データを抽出するための関数を定義
"""


from typing import List, Dict, Union

from lxml import html
import requests
import csv

from domain.price import Price
from domain.shop import Shop

def extract_user_types(price_table_tree) -> List[str]:
    """
    ユーザー種別を取得
    """
    user_types_elements = price_table_tree.xpath('.//tr//th[not(@class="price_title")]')
    return [element.text_content().strip() for element in user_types_elements]

def extract_price_time_data(price_table_tree) -> List[Dict[str, str]]:
    """
    時間帯データを取得
    """
    price_time_elements = price_table_tree.xpath('.//td[@class="price_time"]')
    price_time_data = []
    
    for element in price_time_elements:
        price_time_text = element.text_content().strip()
        rowspan_value = int(element.get('rowspan', 1))  # デフォルト値は1
        price_time_data.append({
            'price_time': price_time_text,
            'rowspan': rowspan_value
        })
    
    return price_time_data

def parse_price_rows(price_table_tree, price_time_data, user_types) -> List[Price]:
    """
    各行の価格データを処理
    """
    prices = []
    tr_trees = price_table_tree.xpath('.//tr[not(@class="price_name")]')
    tr_index = 0

    for price_time in price_time_data:
        for _ in range(price_time['rowspan']):
            tr_tree = tr_trees[tr_index]
            
            # 時間帯を表す要素が存在する場合、削除
            price_time_elements = tr_tree.xpath('.//td[@class="price_time"]')
            if price_time_elements:
                price_time_elements[0].getparent().remove(price_time_elements[0])

            # 日付情報の取得
            td_index = 0
            price_day_elements = tr_tree.xpath('.//td')
            if price_day_elements == []:
                continue

            if price_day_elements[0].get('class').startswith('price'):
                price_day = "全日共通"
            else:
                price_day = price_day_elements[0].text_content().strip()
                td_index += 1

            # 各ユーザー種別の価格を取得
            for j, user_type in enumerate(user_types):
                print(user_type)
                price_text = tr_tree.xpath('.//td')[td_index + j].text_content().strip()
                print(price_text)
                if price_text == '-':
                    continue

                price_value = int(price_text.replace('¥', '').replace(',', ''))

                prices.append(Price(
                    user_type=user_type,
                    price_day=price_day,
                    price_time=price_time['price_time'],
                    price=price_value
                ))

            tr_index += 1

    return prices

def check_if_shop_search_page(tree) -> bool:
    """
    店舗ページかどうかを判定
    """
    shop_search_page_url = 'http://jankara.ne.jp/shop/'

    url_element = tree.xpath('//meta[@property="og:url"]')

    return url_element[0].get("content") == shop_search_page_url

def get_prices(tree, shopnumber) -> List[Price]:
    """
    treeから料金情報を取得
    """
    try:
        price_table_trees = tree.xpath('//div[@class="price_table_area"]')

        result_prices = []

        for price_table_tree in price_table_trees:
            user_types = extract_user_types(price_table_tree)
            price_time_data = extract_price_time_data(price_table_tree)
            prices = parse_price_rows(price_table_tree, price_time_data, user_types)
            result_prices.extend(prices)

        return result_prices
    except Exception as e:
        print(f"Error: {e}, shop_number: {shopnumber}")
        return []

def get_shop_name(tree) -> str:
    """
    treeから店舗名を取得
    """
    shop_name_elements = tree.xpath('//h1[@class="shopinfo__heading"]')
    return shop_name_elements[0].text_content().strip()

def get_shop_address(tree) -> str:
    """
    treeから店舗住所を取得
    """
    shop_address_elements = tree.xpath('//address[@class="shopinfo__detail-address"]')
    return shop_address_elements[0].text_content().strip()

def get_shop(shop_number: int) -> Union[Shop, None]:
    """
    店舗番号から店舗情報を取得
    """
    URL = f'https://jankara.ne.jp/shop/{shop_number}'

    try:
        response = requests.get(URL, timeout=10)
        tree = html.fromstring(response.text)

        is_shop_search_page = check_if_shop_search_page(tree)
        if is_shop_search_page:
            return None

        shop_name = get_shop_name(tree)
        address = get_shop_address(tree)
        prices = get_prices(tree, shop_number)

        return Shop(shop_number=shop_number, name=shop_name, address=address, prices=prices)

    except Exception as e:
        print(f"Error: {e}, shop_number: {shop_number}")
        return None

def create_shop_csv(shops: List[Shop], filename: str):
    """
    ショップ情報をCSVに書き込む
    """
    fieldnames = ["shop_number", "name", "address", "user_type", "price_day", "price_time", "price"]

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        for shop in shops:
            for price in shop.prices:
                writer.writerow({
                    "shop_number": shop.shop_number,
                    "name": shop.name,
                    "address": shop.address,
                    "user_type": price.user_type,
                    "price_day": price.price_day,
                    "price_time": price.price_time,
                    "price": price.price
                })
