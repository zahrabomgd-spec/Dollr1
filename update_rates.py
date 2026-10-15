import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

FIREBASE_URL = "https://dollr-ads-default-rtdb.firebaseio.com/rates.json"

def fetch_price(url, currency_name):
    """
    جلب سعر الشراء والمبيع من موقع sp-today.com بطريقة دقيقة جداً
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ✅ الطريقة الأكثر دقة: البحث عن العناصر التي تحتوي على "شراء" أو "مبيع"
        # نبحث عن النص الذي يحتوي على "شراء" (Buy) و "مبيع" (Sell)
        
        buy_price = None
        sell_price = None
        
        # البحث عن جميع العناصر النصية في الصفحة
        all_elements = soup.find_all(string=True)
        
        # البحث عن السعر بجانب كلمة "شراء"
        for i, elem in enumerate(all_elements):
            text = elem.strip()
            if 'شراء' in text or 'Buy' in text:
                # ابحث عن الرقم في العنصر الحالي أو التالي
                match = re.search(r'(\d+\.\d+)', text)
                if match:
                    buy_price = float(match.group(1))
                    break
                # إذا لم يوجد رقم في نفس العنصر، ابحث في العنصر التالي
                if i + 1 < len(all_elements):
                    next_text = all_elements[i + 1].strip()
                    match = re.search(r'(\d+\.\d+)', next_text)
                    if match:
                        buy_price = float(match.group(1))
                        break
        
        # البحث عن السعر بجانب كلمة "مبيع"
        for i, elem in enumerate(all_elements):
            text = elem.strip()
            if 'مبيع' in text or 'Sell' in text:
                match = re.search(r'(\d+\.\d+)', text)
                if match:
                    sell_price = float(match.group(1))
                    break
                if i + 1 < len(all_elements):
                    next_text = all_elements[i + 1].strip()
                    match = re.search(r'(\d+\.\d+)', next_text)
                    if match:
                        sell_price = float(match.group(1))
                        break
        
        # إذا لم نجد السعر بالطريقة أعلاه، نستخدم الطريقة الاحتياطية
        if buy_price is None or sell_price is None:
            print(f"⚠️ استخدام الطريقة الاحتياطية لـ {currency_name}")
            price_elements = soup.find_all(string=lambda text: text and re.search(r'\d+\.\d+', text))
            decimal_prices = []
            for elem in price_elements:
                match = re.search(r'(\d+\.\d+)', elem.strip())
                if match:
                    decimal_prices.append(float(match.group(1)))
            
            if len(decimal_prices) >= 2:
                buy_price = decimal_prices[0]
                sell_price = decimal_prices[1]
        
        if buy_price is None or sell_price is None:
            print(f"❌ فشل استخراج سعر {currency_name}")
            return None, None
        
        # تحويل إلى ليرة قديمة (ضرب في 100)
        buy_old = int(buy_price * 100)
        sell_old = int(sell_price * 100)
        
        print(f"✅ {currency_name}: شراء = {buy_old}, مبيع = {sell_old}")
        return buy_old, sell_old
            
    except Exception as e:
        print(f"❌ خطأ في جلب سعر {currency_name}: {e}")
        return None, None

def fetch_gold_price():
    try:
        response = requests.get('https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT', timeout=10)
        data = response.json()
        return float(data['symbols'][0]['price'])
    except Exception as e:
        print(f"❌ فشل جلب الذهب: {e}")
        return 4156.19

# === جلب أسعار العملات ===
print("🔄 جاري جلب أسعار العملات...")

usd_buy, usd_sell = fetch_price("https://sp-today.com/en/currency/us-dollar", "الدولار")
if usd_buy is None:
    usd_buy = 13900
    usd_sell = 13975

eur_buy, eur_sell = fetch_price("https://sp-today.com/en/currency/euro", "اليورو")
if eur_buy is None:
    eur_buy = 15450
    eur_sell = 15600

try_buy, try_sell = fetch_price("https://sp-today.com/en/currency/turkish-lira", "الليرة التركية")
if try_buy is None:
    try_buy = 279
    try_sell = 283

# === جلب سعر الذهب وحسابه ===
gold_usd = fetch_gold_price()
gold_gram_usd = gold_usd / 31.1035
gold_21_sell = int(gold_gram_usd * usd_sell * 0.875 * 1.05)
gold_18_sell = int(gold_gram_usd * usd_sell * 0.75 * 1.05)
gold_24_sell = int(gold_gram_usd * usd_sell * 1.05)

# === تجهيز البيانات ===
payload = {
    'lastUpdated': f'تم التحديث آلياً الساعة {datetime.now().strftime("%H:%M")}',
    'exchangeData': {
        'damascus': {
            'name': 'دمشق',
            'usd': {'buy': usd_buy, 'sell': usd_sell},
            'eur': {'buy': eur_buy, 'sell': eur_sell},
            'try': {'buy': try_buy, 'sell': try_sell},
            'gold21': {'buy': gold_21_sell - 200, 'sell': gold_21_sell},
            'gold18': {'buy': gold_18_sell - 200, 'sell': gold_18_sell},
            'gold24': {'buy': gold_24_sell - 300, 'sell': gold_24_sell}
        }
    }
}

# === إرسال إلى Firebase ===
response = requests.put(FIREBASE_URL, json=payload)
print("📤 Firebase Response Status:", response.status_code)
print("📤 Response Text:", response.text)
