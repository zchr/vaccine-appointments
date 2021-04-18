from bs4 import BeautifulSoup as bs
from decouple import config
import requests, time

MAX_MILES = int(config('VACCINE_MAX_MILES'))
MAX_MINUTES = int(config('VACCINE_MAX_MINUTES'))

def get_page(zip):
    url = f'https://www.getmyvaccine.org/zips/{zip}?sort=distance'
    req = requests.get(url)
    return bs(req.text, features='html.parser')

def get_rows(zip):
    page = get_page(zip)
    rows = []
    for row in page.select('div[class*="Row__SlotRow-"]'):
        try:
            distance = row.select('div[class*="Row__Distance-"]')[0].div.text
            distance_miles = float(distance.replace(' miles', ''))
            address = row.select('h4[class*="Row__SlotTitle-"]')[0].contents[1].text 
            active = row.select('div[class*="Row__Ago-"]')[0].div.text
            book_node = row.select('div[class*="Row__Book-"]')[0]
            book_href = book_node.a.get('href')
            source = book_node.div.text
            unique_id = f'{source} {address} {distance_miles}'.lower()
            rows.append({
                'unique_id': unique_id,
                'address': address,
                'active': active,
                'distance_miles': distance_miles,
                'book_href': book_href,
                'source': source
            })
        except Exception as e:
            print('Unable to parse row')
    return filter_rows(rows)

def is_active(time_str, max_minutes):
    if time_str == 'a few seconds ago':
        return True
    if 'minutes ago' in time_str and int(time_str.replace(' minutes ago', '')) <= max_minutes:
        return True
    return False

def filter_rows(rows):
    return [r for r in rows if r['distance_miles'] <= MAX_MILES and is_active(r['active'], MAX_MINUTES)]
