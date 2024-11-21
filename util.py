"""
価格表のHTMLから価格データを抽出するための関数を定義
"""

from typing import List, Dict
from domain.price import Price

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
            price_day = tr_tree.xpath('.//td')[0].text_content().strip()

            # 各ユーザー種別の価格を取得
            for j, user_type in enumerate(user_types):
                price_text = tr_tree.xpath('.//td')[j + 1].text_content().strip()
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

def get_prices(tree) -> List[Price]:
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
        print(f"Error: {e}")
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
    shop_address_elements = tree.xpath('//*[@id="stripeBgInner"]/section/div[2]/div/div/div[1]/div[2]/ul/li[1]/address')
    return shop_address_elements[0].text_content().strip()
