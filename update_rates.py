import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

FIREBASE_URL = "https://dollr-ads-default-rtdb.firebaseio.com/rates.json"

def fetch_price(url):
    """
    جلب سعر الشراء والمبيع من موقع sp-today.com
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن عناصر "Buy" و "Sell" في الصفحة
        # السعر عادة يظهر بصيغة: 139.00SYP (new)
        
        # نبحث عن كل العناصر التي تحتوي على "SYP (new)"
        elements = soup.find_all(string=lambda text: text and 'SYP (new)' in text)
        
        if len(elements) < 2:
            print(f"⚠️ لم يتم العثور على سعري الشراء والمبيع في: {url}")
            return None, None
        
        # السعر الأول عادة هو Buy، والثاني هو Sell
        # (لأن الصفحة تعرض Buy أولاً ثم Sell)
        buy_text = elements[0].strip()
        sell_text = elements[1].strip()
        
        print(f"Buy: {buy_text}")
        print(f"Sell: {sell_text}")
        
        # استخراج الأرقام
        buy_match = re.search(r'(\d+\.?\d*)', buy_text)
        sell_match = re.search(r'(\d+\.?\d*)', sell_text)
        
        if buy_match and sell_match:
            buy_new = float(buy_match.group(1))
            sell_new = float(sell_match.group(1))
            # تحويل إلى ليرة قديمة (ضرب في 100)
            buy_old = int(buy_new * 100)
            sell_old = int(sell_new * 100)
            return buy_old, sell_old
        else:
            print(f"⚠️ لم يتم استخراج الأرقام من: {url}")
            return None, None
            
    except Exception as e:
        print(f"❌ خطأ في جلب السعر من {url}: {e}")
        return None, None

def fetch_gold_price():
    """
    جلب سعر الأونصة العالمي
    """
    try:
        response = requests.get('https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT', timeout=10)
        data = response.json()
        return float(data['symbols'][0]['price'])
    except Exception as e:
        print(f"❌ فشل جلب الذهب: {e}")
        return 4156.19

# === جلب أسعار العملات ===
print("🔄 جاري جلب أسعار العملات...")

# الدولار
usd_buy, usd_sell = fetch_price("https://sp-today.com/en/currency/us-dollar")
if usd_buy is None:
    print("⚠️ فشل جلب سعر الدولار، استخدام السعر الافتراضي")
    usd_buy = 13900
    usd_sell = 13975
print(f"✅ الدولار: شراء = {usd_buy}, مبيع = {usd_sell}")

# اليورو
eur_buy, eur_sell = fetch_price("https://sp-today.com/en/currency/euro")
if eur_buy is None:
    print("⚠️ فشل جلب سعر اليورو، استخدام السعر الافتراضي")
    eur_buy = 15490
    eur_sell = 15690
print(f"✅ اليورو: شراء = {eur_buy}, مبيع = {eur_sell}")

# الليرة التركية
try_buy, try_sell = fetch_price("https://sp-today.com/en/currency/turkish-lira")
if try_buy is None:
    print("⚠️ فشل جلب سعر الليرة التركية، استخدام السعر الافتراضي")
    try_buy = 281
    try_sell = 285
print(f"✅ الليرة التركية: شراء = {try_buy}, مبيع = {try_sell}")

# === جلب سعر الذهب وحسابه ===
gold_usd = fetch_gold_price()
gold_gram_usd = gold_usd / 31.1035
gold_21_sell = int(gold_gram_usd * usd_sell * 0.875 * 1.05)
gold_18_sell = int(gold_gram_usd * usd_sell * 0.75 * 1.05)
gold_24_sell = int(gold_gram_usd * usd_sell * 1.05)
print(f"✅ الذهب (عيار 21): {gold_21_sell}")

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
