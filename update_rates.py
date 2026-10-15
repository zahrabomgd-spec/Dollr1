import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

FIREBASE_URL = "https://dollr-ads-default-rtdb.firebaseio.com/rates.json"

def fetch_usd_price():
    url = "https://sp-today.com/en/currency/us-dollar"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        elements = soup.find_all(string=lambda text: text and 'SYP (new)' in text)
        
        if not elements:
            print("لم يتم العثور على عنصر السعر")
            return None, None
        
        price_text = elements[0].strip()
        print(f"النص المستخرج: {price_text}")
        
        match = re.search(r'(\d+\.?\d*)', price_text)
        if match:
            price_new = float(match.group(1))
            price_old = int(price_new * 100)
            return price_old, price_old + 75
        else:
            return None, None
            
    except Exception as e:
        print(f"خطأ في جلب السعر: {e}")
        return None, None

def fetch_gold_price():
    try:
        response = requests.get('https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT', timeout=10)
        data = response.json()
        return float(data['symbols'][0]['price'])
    except Exception as e:
        print(f"فشل جلب الذهب: {e}")
        return 4156.19

usd_sell, usd_buy = fetch_usd_price()

if usd_sell is None:
    print("⚠️ فشل جلب سعر الدولار، استخدام السعر الافتراضي")
    usd_sell = 13975
    usd_buy = 13900

print(f"سعر الدولار: شراء = {usd_buy}, مبيع = {usd_sell}")

gold_usd = fetch_gold_price()
gold_gram_usd = gold_usd / 31.1035
gold_21_sell = int(gold_gram_usd * usd_sell * 0.875 * 1.05)
gold_18_sell = int(gold_gram_usd * usd_sell * 0.75 * 1.05)
gold_24_sell = int(gold_gram_usd * usd_sell * 1.05)

payload = {
    'lastUpdated': f'تم التحديث آلياً الساعة {datetime.now().strftime("%H:%M")}',
    'exchangeData': {
        'damascus': {'name': 'دمشق', 'usd': {'buy': usd_buy, 'sell': usd_sell}, 'eur': {'buy': int(usd_buy*1.08), 'sell': int(usd_sell*1.08)}, 'try': {'buy': 280, 'sell': 285}, 'gold21': {'buy': gold_21_sell - 200, 'sell': gold_21_sell}, 'gold18': {'buy': gold_18_sell - 200, 'sell': gold_18_sell}, 'gold24': {'buy': gold_24_sell - 300, 'sell': gold_24_sell}},
        'aleppo': {'name': 'حلب', 'usd': {'buy': usd_buy, 'sell': usd_sell}, 'eur': {'buy': int(usd_buy*1.08), 'sell': int(usd_sell*1.08)}, 'try': {'buy': 280, 'sell': 285}, 'gold21': {'buy': gold_21_sell - 200, 'sell': gold_21_sell}, 'gold18': {'buy': gold_18_sell - 200, 'sell': gold_18_sell}, 'gold24': {'buy': gold_24_sell - 300, 'sell': gold_24_sell}},
        'idlib': {'name': 'إدلب', 'usd': {'buy': usd_buy+150, 'sell': usd_sell+200}, 'eur': {'buy': int((usd_buy+150)*1.08), 'sell': int((usd_sell+200)*1.08)}, 'try': {'buy': 290, 'sell': 295}, 'gold21': {'buy': gold_21_sell + 200, 'sell': gold_21_sell + 200}, 'gold18': {'buy': gold_18_sell + 200, 'sell': gold_18_sell + 200}, 'gold24': {'buy': gold_24_sell + 250, 'sell': gold_24_sell + 250}},
        'hasakah': {'name': 'الحسكة', 'usd': {'buy': usd_buy+170, 'sell': usd_sell+220}, 'eur': {'buy': int((usd_buy+170)*1.08), 'sell': int((usd_sell+220)*1.08)}, 'try': {'buy': 292, 'sell': 296}, 'gold21': {'buy': gold_21_sell + 230, 'sell': gold_21_sell + 230}, 'gold18': {'buy': gold_18_sell + 230, 'sell': gold_18_sell + 230}, 'gold24': {'buy': gold_24_sell + 280, 'sell': gold_24_sell + 280}}
    }
}

response = requests.put(FIREBASE_URL, json=payload)
print("Firebase Response Status:", response.status_code)
print("Response Text:", response.text)
