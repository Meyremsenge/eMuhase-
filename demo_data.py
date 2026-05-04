"""
eMuhasebe Pro - Demo Veri Yükleyici
Her kategoride 25 adet demo veri oluşturur ve Firebase'e yükler
"""
import requests
import json
import random
from datetime import datetime, timedelta

# Firebase Realtime Database URL
FIREBASE_URL = "https://emuhasebe-68388-default-rtdb.firebaseio.com"

# ==================== DEMO VERİLER ====================

# Türk isimleri ve şirket isimleri
ISIMLER = [
    "Ahmet", "Mehmet", "Mustafa", "Ali", "Hüseyin", "Hasan", "İbrahim", "Ömer",
    "Fatma", "Ayşe", "Emine", "Hatice", "Zeynep", "Elif", "Merve", "Esra"
]

SOYISIMLER = [
    "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Yıldırım", "Öztürk",
    "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Koç"
]

SEHIRLER = [
    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Gaziantep",
    "Mersin", "Diyarbakır", "Kayseri", "Eskişehir", "Trabzon", "Samsun", "Denizli"
]

SEKTORLER = [
    "İnşaat", "Tekstil", "Gıda", "Otomotiv", "Elektronik", "Mobilya", "Kimya",
    "Metal", "Plastik", "Ambalaj", "Yazılım", "Danışmanlık", "Lojistik", "Tarım"
]

# Ürün kategorileri ve ürünler
URUN_KATEGORILERI = {
    "Elektronik": [
        ("Laptop", 15000, 18000), ("Monitör", 3500, 4500), ("Klavye", 200, 350),
        ("Mouse", 100, 180), ("Kulaklık", 300, 500), ("Webcam", 400, 600)
    ],
    "Ofis Malzemeleri": [
        ("Kalem Seti", 25, 45), ("Defter", 15, 30), ("Klasör", 20, 35),
        ("Zımba", 30, 50), ("Makas", 15, 25), ("Silgi", 5, 10)
    ],
    "Mobilya": [
        ("Ofis Masası", 2000, 3000), ("Ofis Koltuğu", 1500, 2500), ("Dolap", 1200, 1800),
        ("Sehpa", 400, 700), ("Kitaplık", 800, 1200), ("Sandalye", 300, 500)
    ],
    "Yazılım": [
        ("Antivirüs Lisansı", 200, 350), ("Office Lisansı", 800, 1200), ("ERP Modülü", 5000, 8000),
        ("Bulut Depolama", 100, 200), ("VPN Hizmeti", 150, 250)
    ]
}

BIRIMLER = ["Adet", "Kutu", "Paket", "Kg", "Metre", "Litre", "Set"]
KDV_ORANLARI = [1, 10, 20]

def generate_id():
    """Benzersiz ID oluştur"""
    import uuid
    return str(uuid.uuid4())[:8]

def generate_vergi_no():
    """10 haneli vergi numarası oluştur"""
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def generate_phone():
    """Türk telefon numarası oluştur"""
    return f"0{random.choice(['532', '533', '534', '535', '536', '537', '538', '539', '542', '543', '544', '545'])} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}"

def generate_date(days_back=365):
    """Rastgele tarih oluştur"""
    date = datetime.now() - timedelta(days=random.randint(1, days_back))
    return date.strftime("%Y-%m-%d")

def generate_fatura_no(prefix, index):
    """Fatura numarası oluştur"""
    year = datetime.now().year
    return f"{prefix}{year}-{str(index).zfill(5)}"

# ==================== MÜŞTERİLER ====================
def create_musteriler():
    """25 adet müşteri/tedarikçi oluştur"""
    musteriler = {}
    tipler = ["musteri", "tedarikci", "her_ikisi"]
    
    for i in range(25):
        musteri_id = f"musteri_{i+1}"
        isim = random.choice(ISIMLER)
        soyisim = random.choice(SOYISIMLER)
        sektor = random.choice(SEKTORLER)
        sehir = random.choice(SEHIRLER)
        
        # Şirket veya bireysel
        if random.random() > 0.3:
            unvan = f"{isim} {soyisim} {sektor} Ltd. Şti."
        else:
            unvan = f"{isim} {soyisim}"
        
        musteriler[musteri_id] = {
            "id": musteri_id,
            "unvan": unvan,
            "vergi_no": generate_vergi_no(),
            "vergi_dairesi": f"{sehir} Vergi Dairesi",
            "adres": f"{random.choice(['Atatürk', 'Cumhuriyet', 'İstiklal', 'Fatih', 'Mevlana'])} Cad. No:{random.randint(1,200)} {sehir}",
            "telefon": generate_phone(),
            "email": f"{isim.lower()}.{soyisim.lower()}@{random.choice(['gmail.com', 'hotmail.com', 'outlook.com', 'firma.com.tr'])}",
            "tip": random.choice(tipler),
            "aktif": True,
            "olusturma_tarihi": generate_date(180),
            "guncelleme_tarihi": generate_date(30)
        }
    
    return musteriler

# ==================== ÜRÜNLER ====================
def create_urunler():
    """25 adet ürün oluştur"""
    urunler = {}
    urun_index = 1
    
    for kategori, urun_listesi in URUN_KATEGORILERI.items():
        for urun_adi, alis_min, satis_max in urun_listesi:
            if urun_index > 25:
                break
                
            urun_id = f"urun_{urun_index}"
            alis_fiyat = random.randint(alis_min, int((alis_min + satis_max) / 2))
            # Satış fiyatının alış fiyatından yüksek olmasını garantile
            min_satis = alis_fiyat + int(alis_fiyat * 0.15)  # En az %15 kar
            satis_fiyat = random.randint(min_satis, max(min_satis + 100, satis_max))
            
            urunler[urun_id] = {
                "id": urun_id,
                "kod": f"URN-{str(urun_index).zfill(4)}",
                "ad": f"{urun_adi} - {kategori}",
                "aciklama": f"{kategori} kategorisinde kaliteli {urun_adi.lower()}",
                "birim": random.choice(BIRIMLER),
                "alis_fiyat": alis_fiyat,
                "satis_fiyat": satis_fiyat,
                "kdv_orani": random.choice(KDV_ORANLARI),
                "stok_miktari": random.randint(10, 500),
                "aktif": True,
                "olusturma_tarihi": generate_date(365),
                "guncelleme_tarihi": generate_date(60)
            }
            urun_index += 1
    
    return urunler

# ==================== ALIŞ FATURALARI ====================
def create_alis_faturalari(musteriler, urunler):
    """25 adet alış faturası oluştur"""
    faturalar = {}
    musteri_ids = [m for m, data in musteriler.items() if data["tip"] in ["tedarikci", "her_ikisi"]]
    urun_ids = list(urunler.keys())
    durumlar = ["beklemede", "odendi", "odendi", "odendi"]  # Çoğu ödendi olsun
    
    for i in range(25):
        fatura_id = f"alis_{i+1}"
        fatura_tarihi = generate_date(180)
        vade_tarihi = (datetime.strptime(fatura_tarihi, "%Y-%m-%d") + timedelta(days=random.randint(15, 60))).strftime("%Y-%m-%d")
        
        # Fatura kalemleri oluştur (1-5 kalem)
        kalemler = {}
        ara_toplam = 0
        kdv_toplam = 0
        
        kalem_sayisi = random.randint(1, 5)
        for k in range(kalem_sayisi):
            urun_id = random.choice(urun_ids)
            urun = urunler[urun_id]
            miktar = random.randint(1, 20)
            birim_fiyat = urun["alis_fiyat"]
            kdv_orani = urun["kdv_orani"]
            indirim_orani = random.choice([0, 0, 0, 5, 10])
            
            tutar = miktar * birim_fiyat
            indirim = tutar * (indirim_orani / 100)
            net_tutar = tutar - indirim
            kdv_tutar = net_tutar * (kdv_orani / 100)
            
            kalem_id = f"kalem_{k+1}"
            kalemler[kalem_id] = {
                "id": kalem_id,
                "urun_id": urun_id,
                "urun_adi": urun["ad"],
                "aciklama": urun["ad"],
                "miktar": miktar,
                "birim": urun["birim"],
                "birim_fiyat": birim_fiyat,
                "kdv_orani": kdv_orani,
                "indirim_orani": indirim_orani,
                "toplam": net_tutar,
                "kdv_tutar": kdv_tutar,
                "genel_toplam": net_tutar + kdv_tutar
            }
            
            ara_toplam += net_tutar
            kdv_toplam += kdv_tutar
        
        tedarikci_id = random.choice(musteri_ids) if musteri_ids else list(musteriler.keys())[0]
        
        faturalar[fatura_id] = {
            "id": fatura_id,
            "fatura_no": generate_fatura_no("ALF", i+1),
            "fatura_tarihi": fatura_tarihi,
            "vade_tarihi": vade_tarihi,
            "tedarikci_id": tedarikci_id,
            "tedarikci_unvan": musteriler[tedarikci_id]["unvan"],
            "ara_toplam": round(ara_toplam, 2),
            "kdv_toplam": round(kdv_toplam, 2),
            "indirim_toplam": 0,
            "genel_toplam": round(ara_toplam + kdv_toplam, 2),
            "durum": random.choice(durumlar),
            "aciklama": f"Alış faturası - {musteriler[tedarikci_id]['unvan']}",
            "kalemler": kalemler,
            "olusturma_tarihi": fatura_tarihi,
            "guncelleme_tarihi": generate_date(30)
        }
    
    return faturalar

# ==================== SATIŞ FATURALARI ====================
def create_satis_faturalari(musteriler, urunler):
    """25 adet satış faturası oluştur"""
    faturalar = {}
    musteri_ids = [m for m, data in musteriler.items() if data["tip"] in ["musteri", "her_ikisi"]]
    urun_ids = list(urunler.keys())
    durumlar = ["beklemede", "tahsil_edildi", "tahsil_edildi", "tahsil_edildi"]
    
    for i in range(25):
        fatura_id = f"satis_{i+1}"
        fatura_tarihi = generate_date(180)
        vade_tarihi = (datetime.strptime(fatura_tarihi, "%Y-%m-%d") + timedelta(days=random.randint(15, 60))).strftime("%Y-%m-%d")
        
        # Fatura kalemleri oluştur (1-5 kalem)
        kalemler = {}
        ara_toplam = 0
        kdv_toplam = 0
        
        kalem_sayisi = random.randint(1, 5)
        for k in range(kalem_sayisi):
            urun_id = random.choice(urun_ids)
            urun = urunler[urun_id]
            miktar = random.randint(1, 15)
            birim_fiyat = urun["satis_fiyat"]
            kdv_orani = urun["kdv_orani"]
            indirim_orani = random.choice([0, 0, 0, 5, 10, 15])
            
            tutar = miktar * birim_fiyat
            indirim = tutar * (indirim_orani / 100)
            net_tutar = tutar - indirim
            kdv_tutar = net_tutar * (kdv_orani / 100)
            
            kalem_id = f"kalem_{k+1}"
            kalemler[kalem_id] = {
                "id": kalem_id,
                "urun_id": urun_id,
                "urun_adi": urun["ad"],
                "aciklama": urun["ad"],
                "miktar": miktar,
                "birim": urun["birim"],
                "birim_fiyat": birim_fiyat,
                "kdv_orani": kdv_orani,
                "indirim_orani": indirim_orani,
                "toplam": net_tutar,
                "kdv_tutar": kdv_tutar,
                "genel_toplam": net_tutar + kdv_tutar
            }
            
            ara_toplam += net_tutar
            kdv_toplam += kdv_tutar
        
        musteri_id = random.choice(musteri_ids) if musteri_ids else list(musteriler.keys())[0]
        
        faturalar[fatura_id] = {
            "id": fatura_id,
            "fatura_no": generate_fatura_no("STF", i+1),
            "fatura_tarihi": fatura_tarihi,
            "vade_tarihi": vade_tarihi,
            "musteri_id": musteri_id,
            "musteri_unvan": musteriler[musteri_id]["unvan"],
            "ara_toplam": round(ara_toplam, 2),
            "kdv_toplam": round(kdv_toplam, 2),
            "indirim_toplam": 0,
            "genel_toplam": round(ara_toplam + kdv_toplam, 2),
            "durum": random.choice(durumlar),
            "aciklama": f"Satış faturası - {musteriler[musteri_id]['unvan']}",
            "kalemler": kalemler,
            "olusturma_tarihi": fatura_tarihi,
            "guncelleme_tarihi": generate_date(30)
        }
    
    return faturalar

# ==================== İADE FATURALARI ====================
def create_iade_faturalari(musteriler, urunler):
    """25 adet iade faturası oluştur"""
    faturalar = {}
    musteri_ids = list(musteriler.keys())
    urun_ids = list(urunler.keys())
    iade_tipleri = ["alis_iade", "satis_iade"]
    durumlar = ["beklemede", "tamamlandi", "tamamlandi", "tamamlandi"]
    
    for i in range(25):
        fatura_id = f"iade_{i+1}"
        fatura_tarihi = generate_date(120)
        iade_tipi = random.choice(iade_tipleri)
        
        # Fatura kalemleri oluştur (1-3 kalem - iadeler genelde az kalemli)
        kalemler = {}
        ara_toplam = 0
        kdv_toplam = 0
        
        kalem_sayisi = random.randint(1, 3)
        for k in range(kalem_sayisi):
            urun_id = random.choice(urun_ids)
            urun = urunler[urun_id]
            miktar = random.randint(1, 5)
            birim_fiyat = urun["satis_fiyat"] if iade_tipi == "satis_iade" else urun["alis_fiyat"]
            kdv_orani = urun["kdv_orani"]
            
            tutar = miktar * birim_fiyat
            kdv_tutar = tutar * (kdv_orani / 100)
            
            kalem_id = f"kalem_{k+1}"
            kalemler[kalem_id] = {
                "id": kalem_id,
                "urun_id": urun_id,
                "urun_adi": urun["ad"],
                "aciklama": f"İade: {urun['ad']}",
                "miktar": miktar,
                "birim": urun["birim"],
                "birim_fiyat": birim_fiyat,
                "kdv_orani": kdv_orani,
                "indirim_orani": 0,
                "toplam": tutar,
                "kdv_tutar": kdv_tutar,
                "genel_toplam": tutar + kdv_tutar
            }
            
            ara_toplam += tutar
            kdv_toplam += kdv_tutar
        
        firma_id = random.choice(musteri_ids)
        iade_nedenleri = [
            "Ürün hasarlı geldi",
            "Yanlış ürün gönderildi", 
            "Müşteri fikir değiştirdi",
            "Ürün beklentiyi karşılamadı",
            "Sipariş iptal edildi",
            "Kalite sorunu",
            "Fiyat uyuşmazlığı"
        ]
        
        faturalar[fatura_id] = {
            "id": fatura_id,
            "fatura_no": generate_fatura_no("IAD", i+1),
            "fatura_tarihi": fatura_tarihi,
            "firma_id": firma_id,
            "firma_unvan": musteriler[firma_id]["unvan"],
            "iade_tipi": iade_tipi,
            "ara_toplam": round(ara_toplam, 2),
            "kdv_toplam": round(kdv_toplam, 2),
            "genel_toplam": round(ara_toplam + kdv_toplam, 2),
            "durum": random.choice(durumlar),
            "aciklama": random.choice(iade_nedenleri),
            "kalemler": kalemler,
            "olusturma_tarihi": fatura_tarihi,
            "guncelleme_tarihi": generate_date(30)
        }
    
    return faturalar

# ==================== FIREBASE'E YÜKLEME ====================
def upload_to_firebase(collection, data):
    """Veriyi Firebase Realtime Database'e yükle"""
    url = f"{FIREBASE_URL}/{collection}.json"
    response = requests.put(url, json=data)
    
    if response.status_code == 200:
        print(f"✅ {collection}: {len(data)} kayıt başarıyla yüklendi")
        return True
    else:
        print(f"❌ {collection}: Yükleme başarısız - {response.status_code}")
        print(response.text)
        return False

def main():
    """Ana fonksiyon - tüm demo verileri oluştur ve yükle"""
    print("\n" + "="*60)
    print("  eMuhasebe Pro - Demo Veri Yükleyici")
    print("="*60 + "\n")
    
    # Verileri oluştur
    print("📦 Veriler oluşturuluyor...\n")
    
    print("  👥 Müşteriler/Tedarikçiler oluşturuluyor...")
    musteriler = create_musteriler()
    print(f"     ✓ {len(musteriler)} müşteri/tedarikçi oluşturuldu")
    
    print("  📦 Ürünler oluşturuluyor...")
    urunler = create_urunler()
    print(f"     ✓ {len(urunler)} ürün oluşturuldu")
    
    print("  🛒 Alış faturaları oluşturuluyor...")
    alis_faturalari = create_alis_faturalari(musteriler, urunler)
    print(f"     ✓ {len(alis_faturalari)} alış faturası oluşturuldu")
    
    print("  💰 Satış faturaları oluşturuluyor...")
    satis_faturalari = create_satis_faturalari(musteriler, urunler)
    print(f"     ✓ {len(satis_faturalari)} satış faturası oluşturuldu")
    
    print("  ↩️  İade faturaları oluşturuluyor...")
    iade_faturalari = create_iade_faturalari(musteriler, urunler)
    print(f"     ✓ {len(iade_faturalari)} iade faturası oluşturuldu")
    
    # Firebase'e yükle
    print("\n🚀 Firebase'e yükleniyor...\n")
    
    success_count = 0
    success_count += upload_to_firebase("musteriler", musteriler)
    success_count += upload_to_firebase("urunler", urunler)
    success_count += upload_to_firebase("alis_faturalari", alis_faturalari)
    success_count += upload_to_firebase("satis_faturalari", satis_faturalari)
    success_count += upload_to_firebase("iade_faturalari", iade_faturalari)
    
    # Özet
    print("\n" + "="*60)
    if success_count == 5:
        print("  ✅ TÜM VERİLER BAŞARIYLA YÜKLENDİ!")
        print("\n  📊 Özet:")
        print(f"     • {len(musteriler)} Müşteri/Tedarikçi")
        print(f"     • {len(urunler)} Ürün")
        print(f"     • {len(alis_faturalari)} Alış Faturası")
        print(f"     • {len(satis_faturalari)} Satış Faturası")
        print(f"     • {len(iade_faturalari)} İade Faturası")
        print(f"\n     Toplam: {len(musteriler) + len(urunler) + len(alis_faturalari) + len(satis_faturalari) + len(iade_faturalari)} kayıt")
    else:
        print(f"  ⚠️  {5 - success_count} koleksiyon yüklenemedi")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
