"""
価格表のHTMLから価格データを抽出するための関数を定義
"""

from typing import Tuple
from typing import List, Dict, Union

from lxml import html
import requests
import csv, re

from domain.price import Price
from domain.shop import Shop

def extract_user_types(price_table_tree) -> List[str]:
    """
    ユーザー種別を取得
    """
    user_types_elements = price_table_tree.xpath('.//tr//th[not(@class="price_title")]')
    return [element.text_content().strip() for element in user_types_elements]

def extract_price_time_data(price_table_tree, opening_hour, closing_hour) -> List[Dict[str, str]]:
    """
    時間帯データを取得
    """
    price_time_elements = price_table_tree.xpath('.//td[@class="price_time"]')
    price_time_data = []

    for element in price_time_elements:
        price_time_text = element.text_content().strip()
        price_time_parts = [part.strip() for part in price_time_text.split() if part.strip()]

        try:
            start_time, end_time = price_time_parts[1].split(chr(65374))
        except ValueError:
            start_time = "-"
            end_time = "-"

        if start_time == "開店":
            start_time = opening_hour
        else:
            start_time = convert_time_format(start_time)

        if end_time == "閉店":
            end_time = closing_hour
        else:
            end_time = convert_time_format(end_time)

        rowspan_value = int(element.get('rowspan', 1))
        price_time_data.append({
            'system': price_time_parts[0],
            'start_time': start_time,
            'end_time': end_time,
            'rowspan': rowspan_value
        })

    return price_time_data

def parse_price_rows(price_table_tree, price_time_data, user_types) -> List[Price]:
    """
    各行の価格データを処理
    """
    prices: List[Price] = []
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
                price_text = tr_tree.xpath('.//td')[td_index + j].text_content().strip()
                if price_text == '-':
                    continue

                price_value = int(price_text.replace('¥', '').replace(',', ''))

                prices.append(Price(
                    user_type=user_type,
                    price_day=price_day,
                    start_time=price_time['start_time'],
                    end_time=price_time['end_time'],
                    system=price_time['system'],
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

def get_prices(tree, shop_number: int, opening_hour: str, closing_hour: str) -> List[Price]:
    """
    treeから料金情報を取得
    """
    try:
        price_table_trees = tree.xpath('//div[@class="price_table_area"]')

        result_prices = []

        for price_table_tree in price_table_trees:
            user_types = extract_user_types(price_table_tree)
            price_time_data = extract_price_time_data(price_table_tree, opening_hour, closing_hour)
            prices = parse_price_rows(price_table_tree, price_time_data, user_types)
            result_prices.extend(prices)

        return result_prices
    except Exception as e:
        print(f"Error: {e}, shop_number: {shop_number}")
        return []

def get_shop_name(tree) -> str:
    """
    treeから店舗名を取得
    """
    shop_name_elements = tree.xpath('//h1[@class="shopinfo__heading"]')
    return shop_name_elements[0].text_content().strip()

def get_shop_address(tree) -> Tuple[str, str]:
    """
    treeから店舗の郵便番号と住所を取得
    """
    shop_address_elements = tree.xpath('//address[@class="shopinfo__detail-address"]')

    if not shop_address_elements:
        return "", ""

    # addressのテキストを取得
    raw_text = shop_address_elements[0].text_content().strip()

    # 郵便番号と住所を分割
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    if len(lines) < 2:
        return "", ""

    # 郵便番号
    postal_code = lines[0].replace("〒", "").strip()

    # 住所 (改行や不要なHTMLエンティティを処理)
    address = lines[1].replace("&nbsp;", " ").strip()

    return postal_code, address

def get_shop_opening_and_closing_hours(tree) -> Tuple[str, str]:
    """
    treeから店舗の営業時間を取得
    """
    elements = tree.xpath('//i[@class="fa fa-clock-o fa-fw"]/following-sibling::p[1]')
    if not elements:
        return "", ""

    opening_and_closing_hours = elements[0].text_content().strip()

    try:
        opening_hours, closing_hours = opening_and_closing_hours.split("〜")
    except ValueError:
        return "", ""

    return opening_hours.strip(), closing_hours.strip()

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
            print(f"Shop {shop_number} is not found.")
            return None

        shop_name = get_shop_name(tree)
        postal_code, address = get_shop_address(tree)
        opening_hour, closing_hour = get_shop_opening_and_closing_hours(tree)
        prices = get_prices(tree, shop_number, opening_hour, closing_hour)

        return Shop(shop_number=shop_number, name=shop_name, postal_code=postal_code, address=address, prices=prices)

    except Exception as e:
        print(f"Error: {e}, shop_number: {shop_number}")
        return None

def create_shop_csv(shops: List[Shop], filename: str):
    """
    ショップ情報をCSVに書き込む
    """
    fieldnames = ["店舗名", "郵便番号", "住所", "曜日帯", "開始時間", "終了時間", "種別", "システム", "料金"]

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        for shop in shops:
            for price in shop.prices:
                writer.writerow({
                    "店舗名": shop.name,
                    "郵便番号": shop.postal_code,
                    "住所": shop.address,
                    "曜日帯": price.price_day,
                    "開始時間": price.start_time,
                    "終了時間": price.end_time,
                    "種別": price.user_type,
                    "システム": price.system,
                    "料金": price.price
                })

def convert_time_format(time_string: str) -> str:
    """
    時間表記を変換する関数
    - "X時" → "X:00"
    - "X時半" → "X:30"
    - "X時Y分" → "X:Y"
    """
    if "時半" in time_string:
        # "X時半" を "X:30" に変換
        return time_string.replace("時半", ":30")
    elif "時" in time_string and "分" in time_string:
        # "X時Y分" を "X:Y" に変換
        match = re.match(r"(\d+)時(\d+)分", time_string)
        if match:
            hour, minute = match.groups()
            return f"{hour}:{minute}"
    elif "時" in time_string:
        # "X時" を "X:00" に変換
        return time_string.replace("時", ":00")
    else:
        # 変換不要の場合はそのまま返す
        return time_string