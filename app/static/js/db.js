/**
 * eMuhasebe Pro - Veritabanı Soyutlama Katmanı
 * Firebase bağlantısı varsa Firebase kullan, yoksa localStorage (SQLite benzeri)
 * Manuel mod değiştirme desteklenir
 * Otomatik senkronizasyon ve toast bildirimleri
 */

// ==================== BİLDİRİM (NOTIFY) SİSTEMİ ====================
function ensureFlashArea() {
    let container = document.getElementById('flashNotificationArea');
    if (!container) {
        container = document.createElement('div');
        container.id = 'flashNotificationArea';
        container.className = 'flash-notification-area';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        document.body.appendChild(container);
    }
    return container;
}

function getNotificationElements() {
    return {
        list: document.getElementById('notificationList'),
        badge: document.getElementById('notifBadge')
    };
}

function getNotifyIcon(type) {
    const icons = {
        success: 'check-circle',
        danger: 'circle-exclamation',
        error: 'circle-exclamation',
        warning: 'triangle-exclamation',
        info: 'circle-info',
        sync: 'arrows-rotate',
        firebase: 'fire',
        local: 'database'
    };
    return icons[type] || icons.info;
}

function renderNotificationItem(item) {
    const type = item.type || 'info';
    const icon = item.icon || getNotifyIcon(type);
    const time = item.time || 'Şimdi';
    return `
        <div class="notification-item">
            <div class="notification-icon ${type}">
                <i class="fas fa-${icon}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-text">${item.text}</div>
                <div class="notification-time">${time}</div>
            </div>
        </div>
    `;
}

const notify = function(message, level = 'info', options = {}) {
    const mappedLevel = level === 'error' ? 'danger' : level;
    const duration = typeof options.duration === 'number' ? options.duration : 4000;
    const addToList = options.addToList !== false;
    const showToast = options.showToast !== false;
    const timeLabel = options.time || 'Şimdi';
    const icon = options.icon || getNotifyIcon(mappedLevel);
    let toastItem = null;

    if (showToast) {
        const container = ensureFlashArea();
        toastItem = document.createElement('div');
        toastItem.className = `flash-notification flash-${mappedLevel} fade-in`;
        toastItem.setAttribute('role', 'status');
        toastItem.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
            <button type="button" class="flash-close" aria-label="Bildirimi kapat">
                <i class="fas fa-times"></i>
            </button>
        `;
        container.appendChild(toastItem);
        const closeBtn = toastItem.querySelector('.flash-close');
        if (closeBtn) closeBtn.addEventListener('click', () => toastItem.remove());
        if (duration > 0) setTimeout(() => toastItem.remove(), duration);
    }

    if (addToList) {
        notify.addToList({ type: mappedLevel, icon, text: message, time: timeLabel });
    }

    return toastItem;
};

notify.addToList = function(item) {
    const { list, badge } = getNotificationElements();
    if (!list) return;

    if (list.querySelector('.empty-state')) list.innerHTML = '';
    list.insertAdjacentHTML('afterbegin', renderNotificationItem(item));

    if (badge) {
        const count = list.querySelectorAll('.notification-item').length;
        badge.textContent = count;
        badge.classList.toggle('is-hidden', count === 0);
    }
};

notify.setList = function(items) {
    const { list, badge } = getNotificationElements();
    if (!list) return;

    if (!items || items.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-check-circle"></i>
                <p>Tüm işlemler yolunda!</p>
            </div>
        `;
    } else {
        list.innerHTML = items.map(renderNotificationItem).join('');
    }

    if (badge) {
        const count = items ? items.length : 0;
        badge.textContent = count;
        badge.classList.toggle('is-hidden', count === 0);
    }
};

notify.success = (msg, duration, options = {}) => notify(msg, 'success', { ...options, duration });
notify.error = (msg, duration, options = {}) => notify(msg, 'error', { ...options, duration });
notify.warning = (msg, duration, options = {}) => notify(msg, 'warning', { ...options, duration });
notify.info = (msg, duration, options = {}) => notify(msg, 'info', { ...options, duration });
notify.sync = (msg, duration, options = {}) => notify(msg, 'sync', { ...options, duration });
notify.firebase = (msg, duration, options = {}) => notify(msg, 'firebase', { ...options, duration });
notify.local = (msg, duration, options = {}) => notify(msg, 'local', { ...options, duration });

window.notify = notify;
window.Toast = {
    success: (msg, duration, options) => notify.success(msg, duration, options),
    error: (msg, duration, options) => notify.error(msg, duration, options),
    warning: (msg, duration, options) => notify.warning(msg, duration, options),
    info: (msg, duration, options) => notify.info(msg, duration, options),
    sync: (msg, duration, options) => notify.sync(msg, duration, options),
    firebase: (msg, duration, options) => notify.firebase(msg, duration, options),
    local: (msg, duration, options) => notify.local(msg, duration, options)
};

// ==================== BAĞLANTI YÖNETİMİ ====================
let firebaseConnected = false;
let firebaseApp = null;
let firebaseDb = null;
let lastSyncTime = null;

// localStorage'dan force local modu oku
function getForceLocalMode() {
    return localStorage.getItem('emuhasebe_force_local') === 'true';
}

// Mod değiştirme
export function setMode(mode) {
    if (mode === 'local') {
        localStorage.setItem('emuhasebe_force_local', 'true');
        console.log('💾 LocalStorage moduna geçildi');
    } else if (mode === 'firebase') {
        localStorage.setItem('emuhasebe_force_local', 'false');
        console.log('🔥 Firebase moduna geçiliyor...');
    }
    // Mod değişikliği event'i
    window.dispatchEvent(new CustomEvent('db-mode-change', { detail: { mode } }));
}

// Mevcut modu al
export function getMode() {
    if (getForceLocalMode()) return 'local';
    return firebaseConnected ? 'firebase' : 'local';
}

// Firebase config'i yükle.
// Öncelik sırası:
//   1) Kullanıcının UI'dan girdiği config (localStorage 'emuhasebe_firebase_config')
//   2) Backend tarafında env var ile sağlanan config (/api/config/firebase)
//
// Bu, "kendi Firebase projemi bağlamak istiyorum" akışını destekler ama
// kurumsal kurulumlarda env'den otomatik gelmeye de izin verir.
const FIREBASE_LOCAL_CONFIG_KEY = 'emuhasebe_firebase_config';

export function getLocalFirebaseConfig() {
    try {
        const raw = localStorage.getItem(FIREBASE_LOCAL_CONFIG_KEY);
        if (!raw) return null;
        const cfg = JSON.parse(raw);
        const required = ['apiKey', 'authDomain', 'databaseURL', 'projectId'];
        const ok = required.every(k => cfg && typeof cfg[k] === 'string' && cfg[k].trim());
        return ok ? cfg : null;
    } catch (e) {
        return null;
    }
}

export function setLocalFirebaseConfig(cfg) {
    if (cfg) {
        localStorage.setItem(FIREBASE_LOCAL_CONFIG_KEY, JSON.stringify(cfg));
    } else {
        localStorage.removeItem(FIREBASE_LOCAL_CONFIG_KEY);
    }
}

async function loadFirebaseConfig() {
    // 1) Önce kullanıcı UI'sından gelen config
    const local = getLocalFirebaseConfig();
    if (local) return local;

    // 2) Sonra backend env config
    try {
        const response = await fetch('/api/config/firebase');
        if (!response.ok) return null;
        const data = await response.json();
        return data.config || null;
    } catch (e) {
        return null;
    }
}

// Firebase modüllerini dinamik import et
async function initFirebase() {
    // Manuel local mod aktifse Firebase'e bağlanma
    if (getForceLocalMode()) {
        console.log('💾 Manuel LocalStorage modu aktif');
        firebaseConnected = false;
        return false;
    }

    const firebaseConfig = await loadFirebaseConfig();
    if (!firebaseConfig) {
        console.warn('⚠️ Firebase yapılandırması yok, LocalStorage moduna geçiliyor.');
        firebaseConnected = false;
        return false;
    }

    try {
        const { initializeApp } = await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-app.js');
        const { getDatabase, ref, get, onValue } = await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-database.js');

        firebaseApp = initializeApp(firebaseConfig);
        firebaseDb = getDatabase(firebaseApp);
        
        // Bağlantı testi - basit bir okuma denemesi yap
        const testRef = ref(firebaseDb, 'connection_test');
        const testPromise = get(testRef);
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Firebase bağlantı zaman aşımı')), 1500)
        );
        
        await Promise.race([testPromise, timeoutPromise]);
        firebaseConnected = true;
        console.log('🔥 Firebase bağlantısı başarılı!');
        return true;
    } catch (error) {
        console.warn('⚠️ Firebase bağlantısı kurulamadı, localStorage kullanılacak:', error.message);
        firebaseConnected = false;
        return false;
    }
}

// Bağlantı durumunu al
export function isOnline() {
    return firebaseConnected && !getForceLocalMode();
}

// Verilen config ile Firebase bağlantısını TEST et (kalıcı bağlanmaz).
// UI'dan "Test Et" butonu için kullanılır.
export async function testFirebaseConfig(cfg) {
    if (!cfg) return { ok: false, error: 'Config boş' };
    const required = ['apiKey', 'authDomain', 'databaseURL', 'projectId'];
    const missing = required.filter(k => !cfg[k] || !String(cfg[k]).trim());
    if (missing.length) {
        return { ok: false, error: `Eksik alanlar: ${missing.join(', ')}` };
    }
    try {
        const { initializeApp, deleteApp } = await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-app.js');
        const { getDatabase, ref, get } = await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-database.js');
        const testApp = initializeApp(cfg, 'emuhasebe-test-' + Date.now());
        const testDb = getDatabase(testApp);
        try {
            await Promise.race([
                get(ref(testDb, 'connection_test')),
                new Promise((_, rej) => setTimeout(() => rej(new Error('Zaman aşımı (5s)')), 5000))
            ]);
            return { ok: true };
        } finally {
            try { await deleteApp(testApp); } catch (e) { /* ignore */ }
        }
    } catch (error) {
        return { ok: false, error: error.message || 'Bağlantı kurulamadı' };
    }
}

// ==================== LOCALSTORAGE OPERASYONLARI ====================
const LocalDB = {
    // Veri al
    get: (collection) => {
        const data = localStorage.getItem(`emuhasebe_${collection}`);
        return data ? JSON.parse(data) : {};
    },
    
    // Veri kaydet
    set: (collection, data) => {
        localStorage.setItem(`emuhasebe_${collection}`, JSON.stringify(data));
        // Değişiklik event'i tetikle
        window.dispatchEvent(new CustomEvent('localdb-change', { detail: { collection } }));
    },
    
    // Benzersiz ID oluştur
    generateId: () => {
        return 'local_' + Date.now().toString(36) + Math.random().toString(36).substring(2, 11);
    }
};

function buildSeedDate(offsetDays) {
    return new Date(Date.now() - offsetDays * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
}

function mkFatura(kalemler) {
    const ara = kalemler.reduce((s, k) => s + k.miktar * k.birim_fiyat, 0);
    const kdv = kalemler.reduce((s, k) => s + k.miktar * k.birim_fiyat * (k.kdv_orani / 100), 0);
    return { ara_toplam: Math.round(ara), kdv_toplam: Math.round(kdv), genel_toplam: Math.round(ara + kdv) };
}

function mkKalem(urun, miktar) {
    const tutar = urun.satis_fiyat * miktar;
    const kdv_tutar = tutar * (urun.kdv_orani / 100);
    return { urun_id: urun.id, urun_adi: urun.ad, aciklama: urun.ad, birim: urun.birim, miktar, birim_fiyat: urun.satis_fiyat, kdv_orani: urun.kdv_orani, tutar, kdv_tutar, genel_toplam: tutar + kdv_tutar };
}

function mkAlisKalem(urun, miktar) {
    const tutar = urun.alis_fiyat * miktar;
    const kdv_tutar = tutar * (urun.kdv_orani / 100);
    return { urun_id: urun.id, urun_adi: urun.ad, aciklama: urun.ad, birim: urun.birim, miktar, birim_fiyat: urun.alis_fiyat, kdv_orani: urun.kdv_orani, tutar, kdv_tutar, genel_toplam: tutar + kdv_tutar };
}

function createSeedData() {
    const customers = {
        customer_1:  { unvan: 'Atlas Endüstri A.Ş.',        tip: 'musteri',   vergi_no: '1112223334',  vergi_dairesi: 'Beyoğlu VD',  telefon: '0212 555 01 01', email: 'satin.alma@atlas.com.tr',   adres: 'Levent, Beşiktaş / İstanbul', aktif: true, olusturma_tarihi: buildSeedDate(90), guncelleme_tarihi: buildSeedDate(15) },
        customer_2:  { unvan: 'Nova Teknoloji Ltd. Şti.',    tip: 'musteri',   vergi_no: '2223334445',  vergi_dairesi: 'Çankaya VD',  telefon: '0312 555 02 14', email: 'muhasebe@nova-tech.com.tr',  adres: 'Kızılay Mah. Atatürk Bul. No:42 / Ankara', aktif: true, olusturma_tarihi: buildSeedDate(82), guncelleme_tarihi: buildSeedDate(10) },
        customer_3:  { unvan: 'Mavi Sağlık Hizmetleri A.Ş.',tip: 'musteri',   vergi_no: '3334445556',  vergi_dairesi: 'Alsancak VD', telefon: '0232 465 08 90', email: 'info@mavi-saglik.com.tr',    adres: 'Alsancak, Konak / İzmir',     aktif: true, olusturma_tarihi: buildSeedDate(75), guncelleme_tarihi: buildSeedDate(8)  },
        customer_4:  { unvan: 'Kuzey Lojistik ve Taşımacılık',tip:'musteri',  vergi_no: '4445556667',  vergi_dairesi: 'Osmangazi VD',telefon: '0224 272 33 55', email: 'finans@kuzeylojistik.com.tr', adres: 'Organize San. Bölgesi / Bursa', aktif: true, olusturma_tarihi: buildSeedDate(68), guncelleme_tarihi: buildSeedDate(5)  },
        customer_5:  { unvan: 'Deniz Yapı Market',           tip: 'musteri',   vergi_no: '5556667778',  vergi_dairesi: 'Muratpaşa VD',telefon: '0242 312 44 00', email: 'deniz.yapi@gmail.com',       adres: 'Fener Mah. 1234 Sk. No:7 / Antalya', aktif: true, olusturma_tarihi: buildSeedDate(60), guncelleme_tarihi: buildSeedDate(3)  },
        customer_6:  { unvan: 'Yıldız Reklam Ajansı',        tip: 'musteri',   vergi_no: '6661112223',  vergi_dairesi: 'Kadıköy VD',  telefon: '0216 349 77 12', email: 'fatura@yildizreklam.com',    adres: 'Moda Cad. No:88 Kadıköy / İstanbul', aktif: true, olusturma_tarihi: buildSeedDate(55), guncelleme_tarihi: buildSeedDate(2)  },
        customer_7:  { unvan: 'Tekno Dağıtım Tic. A.Ş.',     tip: 'tedarikci', vergi_no: '7778889990',  vergi_dairesi: 'Bağcılar VD', telefon: '0212 671 30 00', email: 'satis@tekno-dagitim.com',    adres: 'İkitelli OSB / İstanbul',     aktif: true, olusturma_tarihi: buildSeedDate(90), guncelleme_tarihi: buildSeedDate(12) },
        customer_8:  { unvan: 'Marmara Bilişim Sistemleri',   tip: 'tedarikci', vergi_no: '8889990001',  vergi_dairesi: 'Şişli VD',    telefon: '0212 224 15 60', email: 'b2b@marmarabilis.com.tr',    adres: 'Bomonti, Şişli / İstanbul',   aktif: true, olusturma_tarihi: buildSeedDate(88), guncelleme_tarihi: buildSeedDate(9)  },
        customer_9:  { unvan: 'Anadolu Tedarik Ltd.',         tip: 'tedarikci', vergi_no: '9990001112',  vergi_dairesi: 'Yenimahalle VD',telefon:'0312 397 44 80',email: 'satis@anadolutedarik.com',   adres: 'Ostim OSB, Yenimahalle / Ankara', aktif: true, olusturma_tarihi: buildSeedDate(85), guncelleme_tarihi: buildSeedDate(7)  },
        customer_10: { unvan: 'Penta Çözüm Merkezi',          tip: 'her_ikisi', vergi_no: '1231231230',  vergi_dairesi: 'Gebze VD',    telefon: '0262 644 50 00', email: 'muhasebe@pentacozum.com.tr', adres: 'Gebze OSB / Kocaeli',         aktif: true, olusturma_tarihi: buildSeedDate(80), guncelleme_tarihi: buildSeedDate(6)  }
    };

    const products = {
        product_1:  { kod: 'BLG-001', ad: 'Dell Latitude 5540 Laptop',      birim: 'Adet',  kdv_orani: 20, stok_miktari: 12, alis_fiyat: 33500, satis_fiyat: 42900, aktif: true, aciklama: 'Intel Core i7, 16GB RAM, 512GB SSD', olusturma_tarihi: buildSeedDate(90), guncelleme_tarihi: buildSeedDate(14) },
        product_2:  { kod: 'BLG-002', ad: 'HP ProBook 450 G10 Laptop',      birim: 'Adet',  kdv_orani: 20, stok_miktari: 9,  alis_fiyat: 27900, satis_fiyat: 35900, aktif: true, aciklama: 'Intel Core i5, 8GB RAM, 256GB SSD',  olusturma_tarihi: buildSeedDate(89), guncelleme_tarihi: buildSeedDate(13) },
        product_3:  { kod: 'BLG-010', ad: 'Logitech MX Master 3S Mouse',    birim: 'Adet',  kdv_orani: 20, stok_miktari: 45, alis_fiyat: 1350,  satis_fiyat: 2190,  aktif: true, aciklama: 'Kablosuz, 8000DPI, USB-C',           olusturma_tarihi: buildSeedDate(88), guncelleme_tarihi: buildSeedDate(11) },
        product_4:  { kod: 'BLG-011', ad: 'Samsung 1TB NVMe SSD 980 Pro',   birim: 'Adet',  kdv_orani: 20, stok_miktari: 38, alis_fiyat: 1850,  satis_fiyat: 2690,  aktif: true, aciklama: 'M.2 PCIe Gen4, 7000MB/s',            olusturma_tarihi: buildSeedDate(87), guncelleme_tarihi: buildSeedDate(10) },
        product_5:  { kod: 'YZC-001', ad: 'Brother HL-L2375DW Yazıcı',     birim: 'Adet',  kdv_orani: 20, stok_miktari: 8,  alis_fiyat: 7100,  satis_fiyat: 9250,  aktif: true, aciklama: 'Lazer, Dubleks, Wi-Fi',              olusturma_tarihi: buildSeedDate(86), guncelleme_tarihi: buildSeedDate(9)  },
        product_6:  { kod: 'AGˊ-001', ad: 'Cisco CBS350-24T Switch',        birim: 'Adet',  kdv_orani: 20, stok_miktari: 7,  alis_fiyat: 10200, satis_fiyat: 13490, aktif: true, aciklama: '24 Port Gigabit Managed Switch',      olusturma_tarihi: buildSeedDate(85), guncelleme_tarihi: buildSeedDate(8)  },
        product_7:  { kod: 'OFS-003', ad: 'A4 Fotokopi Kağıdı 80gr',        birim: 'Paket', kdv_orani: 20, stok_miktari: 310,alis_fiyat: 88,    satis_fiyat: 145,   aktif: true, aciklama: '500 yaprak/paket, 5 paket/koli',     olusturma_tarihi: buildSeedDate(84), guncelleme_tarihi: buildSeedDate(7)  },
        product_8:  { kod: 'GVL-001', ad: 'Hikvision DS-2CD2143 Kamera',    birim: 'Adet',  kdv_orani: 20, stok_miktari: 22, alis_fiyat: 2250,  satis_fiyat: 3290,  aktif: true, aciklama: '4MP IP Dome, PoE, IR 30m',           olusturma_tarihi: buildSeedDate(83), guncelleme_tarihi: buildSeedDate(6)  },
        product_9:  { kod: 'OFS-010', ad: 'Ergonomik Ofis Koltuğu',         birim: 'Adet',  kdv_orani: 20, stok_miktari: 18, alis_fiyat: 2750,  satis_fiyat: 3990,  aktif: true, aciklama: 'Mesh sırtlık, ayarlanabilir',         olusturma_tarihi: buildSeedDate(82), guncelleme_tarihi: buildSeedDate(5)  },
        product_10: { kod: 'LSN-001', ad: 'Windows 11 Pro OEM Lisans',      birim: 'Adet',  kdv_orani: 20, stok_miktari: 75, alis_fiyat: 1150,  satis_fiyat: 1890,  aktif: true, aciklama: 'Dijital lisans, kalıcı aktivasyon',  olusturma_tarihi: buildSeedDate(81), guncelleme_tarihi: buildSeedDate(4)  },
        product_11: { kod: 'LSN-002', ad: 'Microsoft Office 2024 Pro',      birim: 'Adet',  kdv_orani: 20, stok_miktari: 50, alis_fiyat: 2900,  satis_fiyat: 4290,  aktif: true, aciklama: 'Word, Excel, Outlook, Teams dahil',  olusturma_tarihi: buildSeedDate(80), guncelleme_tarihi: buildSeedDate(3)  },
        product_12: { kod: 'GVL-002', ad: 'UPS 1500VA APC Smart',           birim: 'Adet',  kdv_orani: 20, stok_miktari: 14, alis_fiyat: 3200,  satis_fiyat: 4490,  aktif: true, aciklama: 'LCD ekran, USB yönetim, 8 çıkış',    olusturma_tarihi: buildSeedDate(79), guncelleme_tarihi: buildSeedDate(2)  }
    };

    const cList = Object.entries(customers).map(([id, d]) => ({ id, ...d }));
    const pList = Object.entries(products).map(([id, d]) => ({ id, ...d }));
    const tedList = cList.filter(c => c.tip === 'tedarikci' || c.tip === 'her_ikisi');
    const musListesi = cList.filter(c => c.tip === 'musteri' || c.tip === 'her_ikisi');

    const salesInvoices = {};
    const purchaseInvoices = {};
    const returnInvoices = {};

    // --- 25 Satış Faturası (son 90 gün, 2-3 kalemli, gerçekçi) ---
    const satisSenaryolari = [
        { cIdx:0, kList:[{p:0,m:3},{p:3,m:5},{p:9,m:1}], gun:88, durum:'odendi' },
        { cIdx:1, kList:[{p:1,m:2},{p:10,m:2}],           gun:85, durum:'odendi' },
        { cIdx:2, kList:[{p:7,m:4},{p:5,m:1}],            gun:82, durum:'odendi' },
        { cIdx:3, kList:[{p:5,m:1},{p:2,m:3},{p:8,m:2}],  gun:80, durum:'odendi' },
        { cIdx:4, kList:[{p:6,m:1},{p:2,m:2}],            gun:77, durum:'beklemede' },
        { cIdx:0, kList:[{p:0,m:2},{p:11,m:1}],           gun:74, durum:'odendi' },
        { cIdx:1, kList:[{p:3,m:10},{p:9,m:3},{p:2,m:4}], gun:71, durum:'odendi' },
        { cIdx:5, kList:[{p:9,m:2},{p:10,m:2}],           gun:69, durum:'odendi' },
        { cIdx:2, kList:[{p:4,m:2},{p:6,m:3}],            gun:66, durum:'odendi' },
        { cIdx:3, kList:[{p:7,m:8},{p:8,m:2}],            gun:63, durum:'beklemede' },
        { cIdx:4, kList:[{p:1,m:3},{p:3,m:6}],            gun:60, durum:'odendi' },
        { cIdx:5, kList:[{p:0,m:1},{p:11,m:1},{p:2,m:2}], gun:57, durum:'odendi' },
        { cIdx:0, kList:[{p:7,m:15},{p:9,m:5}],           gun:54, durum:'odendi' },
        { cIdx:1, kList:[{p:5,m:2},{p:4,m:1}],            gun:51, durum:'beklemede' },
        { cIdx:2, kList:[{p:6,m:2},{p:10,m:3}],           gun:48, durum:'odendi' },
        { cIdx:3, kList:[{p:3,m:12},{p:2,m:5}],           gun:45, durum:'odendi' },
        { cIdx:4, kList:[{p:0,m:4},{p:1,m:2}],            gun:42, durum:'odendi' },
        { cIdx:5, kList:[{p:8,m:6},{p:7,m:20}],           gun:39, durum:'odendi' },
        { cIdx:0, kList:[{p:9,m:3},{p:10,m:2},{p:11,m:1}],gun:35, durum:'odendi' },
        { cIdx:1, kList:[{p:4,m:3},{p:5,m:1}],            gun:30, durum:'beklemede' },
        { cIdx:2, kList:[{p:0,m:2},{p:3,m:8}],            gun:26, durum:'odendi' },
        { cIdx:3, kList:[{p:6,m:1},{p:7,m:30}],           gun:21, durum:'odendi' },
        { cIdx:4, kList:[{p:1,m:4},{p:2,m:6},{p:10,m:2}], gun:15, durum:'beklemede' },
        { cIdx:5, kList:[{p:11,m:2},{p:8,m:4}],           gun:10, durum:'odendi' },
        { cIdx:0, kList:[{p:3,m:7},{p:9,m:4}],            gun:4,  durum:'odendi' },
    ];
    // Jeneratör: son 90 günde rastgele ama deterministik fatura üret
    const DURUMLAR = ['odendi','odendi','odendi','beklemede','iptal'];
    function genSatis(count, offset) {
        for (let i = 0; i < count; i++) {
            const idx = offset + i;
            const cIdx = idx % musListesi.length;
            const p1 = idx % pList.length;
            const p2 = (idx + 3) % pList.length;
            const p3 = (idx + 7) % pList.length;
            const musteri = musListesi[cIdx];
            const k = p1 === p2 ? [mkKalem(pList[p1], 1+(idx%4)), mkKalem(pList[p3], 1+(idx%3))]
                                : [mkKalem(pList[p1], 1+(idx%4)), mkKalem(pList[p2], 1+(idx%2))];
            const tot = mkFatura(k);
            const gun = 1 + (idx * 7) % 89;
            const dt = buildSeedDate(gun);
            const vadeDt = new Date(new Date(dt).getTime() + 30*24*3600*1000).toISOString().split('T')[0];
            salesInvoices[`sale_${idx+1}`] = { fatura_no: `SF-2026-${String(idx+1).padStart(4,'0')}`, musteri_id: musteri.id, musteri_adi: musteri.unvan, fatura_tarihi: dt, vade_tarihi: vadeDt, durum: DURUMLAR[idx%DURUMLAR.length], aciklama: '', kalemler: k, ...tot, olusturma_tarihi: dt, guncelleme_tarihi: dt };
        }
    }
    function genAlis(count, offset) {
        for (let i = 0; i < count; i++) {
            const idx = offset + i;
            const tIdx = idx % tedList.length;
            const p1 = (idx+1) % pList.length;
            const p2 = (idx+5) % pList.length;
            const ted = tedList[tIdx];
            const k = [mkAlisKalem(pList[p1], 2+(idx%6)), mkAlisKalem(pList[p2], 1+(idx%4))];
            const ara = k.reduce((s,x)=>s+x.miktar*x.birim_fiyat,0);
            const kdv = k.reduce((s,x)=>s+x.miktar*x.birim_fiyat*(x.kdv_orani/100),0);
            const tot = { ara_toplam: Math.round(ara), kdv_toplam: Math.round(kdv), genel_toplam: Math.round(ara+kdv) };
            const gun = 1 + (idx * 11) % 89;
            const dt = buildSeedDate(gun);
            const vadeDt = new Date(new Date(dt).getTime() + 45*24*3600*1000).toISOString().split('T')[0];
            purchaseInvoices[`purchase_${idx+1}`] = { fatura_no: `AF-2026-${String(idx+1).padStart(4,'0')}`, tedarikci_id: ted.id, tedarikci_adi: ted.unvan, fatura_tarihi: dt, vade_tarihi: vadeDt, durum: DURUMLAR[idx%DURUMLAR.length], aciklama: '', kalemler: k, ...tot, olusturma_tarihi: dt, guncelleme_tarihi: dt };
        }
    }
    function genIade(count, offset) {
        const IADE_DURUM = ['tamamlandi','tamamlandi','beklemede'];
        const NEDENLER = ['Ürün hatalı çıktı','Yanlış model gönderildi','Ambalaj hasarlı','Teknik arıza','Müşteri vazgeçti','Eksik teslimat','Standart dışı ürün','Geç teslimat'];
        for (let i = 0; i < count; i++) {
            const idx = offset + i;
            const tip = idx % 3 === 0 ? 'alis_iade' : 'satis_iade';
            const taraf = tip === 'satis_iade' ? musListesi[idx % musListesi.length] : tedList[idx % tedList.length];
            const pr = pList[idx % pList.length];
            const m = 1 + (idx % 3);
            const fiyat = tip === 'satis_iade' ? pr.satis_fiyat : pr.alis_fiyat;
            const tutar = fiyat * m;
            const kdv_tutar = tutar * (pr.kdv_orani / 100);
            const gun = 1 + (idx * 13) % 89;
            const dt = buildSeedDate(gun);
            const kalemler = [{ urun_id: pr.id, urun_adi: pr.ad, aciklama: pr.ad, birim: pr.birim, miktar: m, birim_fiyat: fiyat, kdv_orani: pr.kdv_orani, tutar, kdv_tutar, genel_toplam: tutar + kdv_tutar }];
            returnInvoices[`return_${idx+1}`] = { fatura_no: `IF-2026-${String(idx+1).padStart(4,'0')}`, iade_tipi: tip, cari_id: taraf.id, cari_adi: taraf.unvan, orijinal_fatura_no: (tip==='satis_iade'?'SF':'AF')+`-2026-${String(idx+1).padStart(4,'0')}`, fatura_tarihi: dt, durum: IADE_DURUM[idx%IADE_DURUM.length], iade_nedeni: NEDENLER[idx%NEDENLER.length], kalemler, ara_toplam: Math.round(tutar), kdv_toplam: Math.round(kdv_tutar), genel_toplam: Math.round(tutar+kdv_tutar), olusturma_tarihi: dt, guncelleme_tarihi: dt };
        }
    }

    // Manuel senaryolar (25 satış) + jeneratör ile 75 ek = 100 satış
    satisSenaryolari.forEach((s, i) => {
        const musteri = musListesi[s.cIdx % musListesi.length];
        const kalemler = s.kList.map(k => mkKalem(pList[k.p % pList.length], k.m));
        const tot = mkFatura(kalemler);
        const dt = buildSeedDate(s.gun);
        const vadeDt = new Date(new Date(dt).getTime() + 30*24*3600*1000).toISOString().split('T')[0];
        salesInvoices[`sale_${i+1}`] = { fatura_no: `SF-2026-${String(i+1).padStart(4,'0')}`, musteri_id: musteri.id, musteri_adi: musteri.unvan, fatura_tarihi: dt, vade_tarihi: vadeDt, durum: s.durum, aciklama: '', kalemler, ...tot, olusturma_tarihi: dt, guncelleme_tarihi: dt };
    });
    genSatis(675, 25); // 26–700 (toplam 700 satış)

    // Manuel senaryolar (20 alış) + jeneratör ile 60 ek = 80 alış
    const alisSenaryolari = [
        { tIdx:0, kList:[{p:0,m:5},{p:1,m:3}],            gun:87, durum:'odendi' },
        { tIdx:1, kList:[{p:3,m:20},{p:9,m:10}],          gun:84, durum:'odendi' },
        { tIdx:2, kList:[{p:7,m:10}],                     gun:81, durum:'odendi' },
        { tIdx:0, kList:[{p:5,m:3},{p:4,m:2}],            gun:78, durum:'odendi' },
        { tIdx:1, kList:[{p:2,m:15},{p:10,m:8}],          gun:74, durum:'beklemede' },
        { tIdx:2, kList:[{p:6,m:5}],                      gun:70, durum:'odendi' },
        { tIdx:0, kList:[{p:8,m:10},{p:11,m:5}],          gun:65, durum:'odendi' },
        { tIdx:1, kList:[{p:0,m:4},{p:1,m:4}],            gun:61, durum:'odendi' },
        { tIdx:2, kList:[{p:3,m:30},{p:9,m:15}],          gun:58, durum:'beklemede' },
        { tIdx:0, kList:[{p:7,m:8},{p:4,m:3}],            gun:53, durum:'odendi' },
        { tIdx:1, kList:[{p:5,m:2},{p:6,m:3}],            gun:49, durum:'odendi' },
        { tIdx:2, kList:[{p:2,m:20},{p:10,m:10}],         gun:44, durum:'odendi' },
        { tIdx:0, kList:[{p:8,m:6},{p:11,m:4}],           gun:40, durum:'beklemede' },
        { tIdx:1, kList:[{p:0,m:6},{p:1,m:5}],            gun:36, durum:'odendi' },
        { tIdx:2, kList:[{p:3,m:40}],                     gun:31, durum:'odendi' },
        { tIdx:0, kList:[{p:7,m:12},{p:9,m:8}],           gun:26, durum:'odendi' },
        { tIdx:1, kList:[{p:4,m:5},{p:5,m:3}],            gun:21, durum:'beklemede' },
        { tIdx:2, kList:[{p:6,m:2},{p:10,m:6},{p:11,m:3}],gun:16, durum:'odendi' },
        { tIdx:0, kList:[{p:2,m:10},{p:8,m:5}],           gun:10, durum:'odendi' },
        { tIdx:1, kList:[{p:0,m:3},{p:3,m:15}],           gun:5,  durum:'beklemede' },
    ];
    alisSenaryolari.forEach((s, i) => {
        const ted = tedList[s.tIdx % tedList.length];
        const kalemler = s.kList.map(k => mkAlisKalem(pList[k.p % pList.length], k.m));
        const tot = (() => { const ara = kalemler.reduce((sum,k)=>sum+k.miktar*k.birim_fiyat,0); const kdv = kalemler.reduce((sum,k)=>sum+k.miktar*k.birim_fiyat*(k.kdv_orani/100),0); return { ara_toplam: Math.round(ara), kdv_toplam: Math.round(kdv), genel_toplam: Math.round(ara+kdv) }; })();
        const dt = buildSeedDate(s.gun);
        const vadeDt = new Date(new Date(dt).getTime() + 45*24*3600*1000).toISOString().split('T')[0];
        purchaseInvoices[`purchase_${i+1}`] = { fatura_no: `AF-2026-${String(i+1).padStart(4,'0')}`, tedarikci_id: ted.id, tedarikci_adi: ted.unvan, fatura_tarihi: dt, vade_tarihi: vadeDt, durum: s.durum, aciklama: '', kalemler, ...tot, olusturma_tarihi: dt, guncelleme_tarihi: dt };
    });
    genAlis(680, 20); // 21–700 (toplam 700 alış)

    // --- 8 İade Faturası ---
    const iadeSenaryolari = [
        { cIdx:0, pIdx:0, m:1, gun:80, tip:'satis_iade', neden:'Ürün hatalı çıktı' },
        { cIdx:1, pIdx:3, m:3, gun:72, tip:'satis_iade', neden:'Yanlış model gönderildi' },
        { cIdx:2, pIdx:7, m:2, gun:65, tip:'satis_iade', neden:'Ambalaj hasarlı' },
        { cIdx:4, pIdx:1, m:1, gun:55, tip:'satis_iade', neden:'Teknik arıza tespit edildi' },
        { cIdx:0, pIdx:5, m:1, gun:48, tip:'alis_iade',  neden:'Tedarikçi hatalı fatura' },
        { cIdx:1, pIdx:9, m:5, gun:38, tip:'alis_iade',  neden:'Ürün standart dışı' },
        { cIdx:2, pIdx:2, m:4, gun:22, tip:'satis_iade', neden:'Müşteri vazgeçti' },
        { cIdx:3, pIdx:6, m:1, gun:10, tip:'alis_iade',  neden:'Eksik ürün teslimi' },
    ];
    iadeSenaryolari.forEach((s, i) => {
        const taraf = s.tip === 'satis_iade' ? musListesi[s.cIdx % musListesi.length] : tedList[s.cIdx % tedList.length];
        const pr = pList[s.pIdx % pList.length];
        const fiyat = s.tip === 'satis_iade' ? pr.satis_fiyat : pr.alis_fiyat;
        const tutar = fiyat * s.m;
        const kdv_tutar = tutar * (pr.kdv_orani / 100);
        const dt = buildSeedDate(s.gun);
        const kalemler = [{ urun_id: pr.id, urun_adi: pr.ad, aciklama: pr.ad, birim: pr.birim, miktar: s.m, birim_fiyat: fiyat, kdv_orani: pr.kdv_orani, tutar, kdv_tutar, genel_toplam: tutar + kdv_tutar }];
        returnInvoices[`return_${i+1}`] = { fatura_no: `IF-2026-${String(i+1).padStart(4,'0')}`, iade_tipi: s.tip, cari_id: taraf.id, cari_adi: taraf.unvan, orijinal_fatura_no: s.tip==='satis_iade'?`SF-2026-${String(i+1).padStart(4,'0')}`:`AF-2026-${String(i+1).padStart(4,'0')}`, fatura_tarihi: dt, durum: i%3===0?'beklemede':'tamamlandi', iade_nedeni: s.neden, kalemler, ara_toplam: Math.round(tutar), kdv_toplam: Math.round(kdv_tutar), genel_toplam: Math.round(tutar+kdv_tutar), olusturma_tarihi: dt, guncelleme_tarihi: dt };
    });
    genIade(192, 8); // 9–200 (toplam 200 iade)

    // --- Anomali faturaları: AI anomali tespitini (z-score > 3.5) tetiklemek için
    // ortalamanın çok üstünde, sıra dışı tutarlı birkaç fatura. Gerçekçi senaryo:
    // beklenmedik büyük proje siparişi / toplu alım.
    const anomaliSatis = [
        { gun: 14, urun: 0,  miktar: 110, aciklama: 'Kurumsal toplu laptop alımı (büyük proje)' },
        { gun: 33, urun: 5,  miktar: 380, aciklama: 'Yıllık network altyapı yenileme ihalesi' },
        { gun: 52, urun: 1,  miktar: 140, aciklama: 'Şube açılışı ekipman tedariki' },
    ];
    anomaliSatis.forEach((a, i) => {
        const idx = 700 + i;
        const musteri = musListesi[i % musListesi.length];
        const k = [mkKalem(pList[a.urun], a.miktar)];
        const tot = mkFatura(k);
        const dt = buildSeedDate(a.gun);
        salesInvoices[`sale_${idx+1}`] = { fatura_no: `SF-2026-${String(idx+1).padStart(4,'0')}`, musteri_id: musteri.id, musteri_adi: musteri.unvan, fatura_tarihi: dt, vade_tarihi: dt, durum: 'beklemede', aciklama: a.aciklama, kalemler: k, ...tot, olusturma_tarihi: dt, guncelleme_tarihi: dt };
    });

    const anomaliAlis = [
        { gun: 20, urun: 3,  miktar: 600, aciklama: 'Stok yenileme — yıllık toplu SSD alımı' },
        { gun: 41, urun: 0,  miktar: 90,  aciklama: 'Bayi kampanyası toplu laptop tedariki' },
    ];
    anomaliAlis.forEach((a, i) => {
        const idx = 700 + i;
        const ted = tedList[i % tedList.length];
        const k = [mkAlisKalem(pList[a.urun], a.miktar)];
        const ara = k.reduce((s,x)=>s+x.miktar*x.birim_fiyat,0);
        const kdv = k.reduce((s,x)=>s+x.miktar*x.birim_fiyat*(x.kdv_orani/100),0);
        const dt = buildSeedDate(a.gun);
        purchaseInvoices[`purchase_${idx+1}`] = { fatura_no: `AF-2026-${String(idx+1).padStart(4,'0')}`, tedarikci_id: ted.id, tedarikci_adi: ted.unvan, fatura_tarihi: dt, vade_tarihi: dt, durum: 'beklemede', aciklama: a.aciklama, kalemler: k, ara_toplam: Math.round(ara), kdv_toplam: Math.round(kdv), genel_toplam: Math.round(ara+kdv), olusturma_tarihi: dt, guncelleme_tarihi: dt };
    });

    return {
        musteriler: customers,
        urunler: products,
        satis_faturalari: salesInvoices,
        alis_faturalari: purchaseInvoices,
        iade_faturalari: returnInvoices
    };
}

function hasAnySeedData() {
    return ['musteriler', 'urunler', 'alis_faturalari', 'satis_faturalari', 'iade_faturalari']
        .some((collection) => Object.keys(LocalDB.get(collection)).length > 0);
}

function seedLocalDataIfEmpty() {
    if (getForceLocalMode() && !hasAnySeedData()) {
        const seedData = createSeedData();
        Object.entries(seedData).forEach(([collection, data]) => {
            LocalDB.set(collection, data);
        });
        console.log('🌱 Başlangıç verileri otomatik oluşturuldu');
        return true;
    }
    return false;
}

// ==================== FIREBASE OPERASYONLARI ====================
let firebaseRefs = null;

async function getFirebaseRefs() {
    if (!firebaseRefs) {
        const { ref, push, set, get, update, remove, onValue } = 
            await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-database.js');
        firebaseRefs = { ref, push, set, get, update, remove, onValue };
    }
    return firebaseRefs;
}

// ==================== GENERIC CRUD OPERASYONLARI ====================
// Aktif local listener'ları takip et — leak'i engelle
const _activeLocalListeners = new Map();

function createCRUD(collectionName) {
    return {
        // Realtime dinle — bir collection için sadece tek bir aktif listener tutar
        dinle: async (callback) => {
            if (firebaseConnected) {
                const { ref, onValue } = await getFirebaseRefs();
                const collectionRef = ref(firebaseDb, collectionName);
                onValue(collectionRef, (snapshot) => {
                    const data = snapshot.val();
                    const items = data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
                    callback(items);
                });
            } else {
                // LocalStorage için event dinle (leak yok: önceki listener silinir)
                const getData = () => {
                    const data = LocalDB.get(collectionName);
                    const items = Object.entries(data).map(([id, val]) => ({ id, ...val }));
                    callback(items);
                };
                getData(); // İlk yükleme

                // Önceki listener varsa kaldır
                const previous = _activeLocalListeners.get(collectionName);
                if (previous) {
                    window.removeEventListener('localdb-change', previous);
                }
                const handler = (e) => {
                    if (e.detail && e.detail.collection === collectionName) getData();
                };
                _activeLocalListeners.set(collectionName, handler);
                window.addEventListener('localdb-change', handler);
            }
        },

        // Hepsini getir
        hepsiniGetir: async () => {
            if (firebaseConnected) {
                const { ref, get } = await getFirebaseRefs();
                const snapshot = await get(ref(firebaseDb, collectionName));
                const data = snapshot.val();
                return data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
            } else {
                const data = LocalDB.get(collectionName);
                return Object.entries(data).map(([id, val]) => ({ id, ...val }));
            }
        },

        // Tek kayıt getir
        getir: async (id) => {
            if (firebaseConnected) {
                const { ref, get } = await getFirebaseRefs();
                const snapshot = await get(ref(firebaseDb, `${collectionName}/${id}`));
                return snapshot.val() ? { id, ...snapshot.val() } : null;
            } else {
                const data = LocalDB.get(collectionName);
                return data[id] ? { id, ...data[id] } : null;
            }
        },

        // Ekle
        ekle: async (item) => {
            const now = new Date().toISOString();
            const itemWithDates = {
                ...item,
                olusturma_tarihi: now,
                guncelleme_tarihi: now
            };

            if (firebaseConnected) {
                const { ref, push, set } = await getFirebaseRefs();
                const newRef = push(ref(firebaseDb, collectionName));
                await set(newRef, itemWithDates);
                return newRef.key;
            } else {
                const data = LocalDB.get(collectionName);
                const id = LocalDB.generateId();
                data[id] = itemWithDates;
                LocalDB.set(collectionName, data);
                return id;
            }
        },

        // Güncelle
        guncelle: async (id, item) => {
            const now = new Date().toISOString();
            
            if (firebaseConnected) {
                const { ref, update } = await getFirebaseRefs();
                await update(ref(firebaseDb, `${collectionName}/${id}`), {
                    ...item,
                    guncelleme_tarihi: now
                });
            } else {
                const data = LocalDB.get(collectionName);
                if (data[id]) {
                    data[id] = { ...data[id], ...item, guncelleme_tarihi: now };
                    LocalDB.set(collectionName, data);
                }
            }
        },

        // Sil
        sil: async (id) => {
            if (firebaseConnected) {
                const { ref, remove } = await getFirebaseRefs();
                await remove(ref(firebaseDb, `${collectionName}/${id}`));
            } else {
                const data = LocalDB.get(collectionName);
                delete data[id];
                LocalDB.set(collectionName, data);
            }
        }
    };
}

// ==================== MÜŞTERİLER ====================
export const Musteriler = {
    ...createCRUD('musteriler'),
    
    // Tip'e göre filtrele
    tipFiltrele: async (tip) => {
        const tumu = await Musteriler.hepsiniGetir();
        if (tip === 'hepsi') return tumu;
        return tumu.filter(m => m.tip === tip || m.tip === 'her_ikisi');
    }
};

// ==================== ÜRÜNLER ====================
export const Urunler = createCRUD('urunler');

// ==================== STOK YÖNETİMİ ====================
export const StokYonetimi = {
    stokEkle: async (urun_id, miktar) => {
        if (!urun_id) return;
        const urun = await Urunler.getir(urun_id);
        if (urun) {
            urun.stok_miktari = (parseFloat(urun.stok_miktari) || 0) + parseFloat(miktar);
            await Urunler.guncelle(urun_id, urun);
        }
    },
    stokDus: async (urun_id, miktar) => {
        if (!urun_id) return;
        const urun = await Urunler.getir(urun_id);
        if (urun) {
            urun.stok_miktari = (parseFloat(urun.stok_miktari) || 0) - parseFloat(miktar);
            await Urunler.guncelle(urun_id, urun);
        }
    }
};

function getKalemler(fatura) {
    if (!fatura || !fatura.kalemler) return [];
    return Array.isArray(fatura.kalemler) ? fatura.kalemler : Object.values(fatura.kalemler);
}

// ==================== ALIŞ FATURALARI ====================
const AlisBase = createCRUD('alis_faturalari');
export const AlisFaturalari = {
    ...AlisBase,
    ekle: async (item) => {
        const id = await AlisBase.ekle(item);
        for (let k of getKalemler(item)) await StokYonetimi.stokEkle(k.urun_id, k.miktar);
        return id;
    },
    sil: async (id) => {
        const fatura = await AlisBase.getir(id);
        if (fatura) {
            for (let k of getKalemler(fatura)) await StokYonetimi.stokDus(k.urun_id, k.miktar);
        }
        await AlisBase.sil(id);
    },
    aylikToplam: async () => {
        const faturalar = await AlisBase.hepsiniGetir();
        const buAy = new Date();
        const ayBaslangic = new Date(buAy.getFullYear(), buAy.getMonth(), 1);
        return faturalar.filter(f => new Date(f.fatura_tarihi) >= ayBaslangic)
            .reduce((toplam, f) => toplam + (parseFloat(f.genel_toplam) || 0), 0);
    }
};

// ==================== SATIŞ FATURALARI ====================
const SatisBase = createCRUD('satis_faturalari');
export const SatisFaturalari = {
    ...SatisBase,
    ekle: async (item) => {
        const id = await SatisBase.ekle(item);
        for (let k of getKalemler(item)) await StokYonetimi.stokDus(k.urun_id, k.miktar);
        return id;
    },
    sil: async (id) => {
        const fatura = await SatisBase.getir(id);
        if (fatura) {
            for (let k of getKalemler(fatura)) await StokYonetimi.stokEkle(k.urun_id, k.miktar);
        }
        await SatisBase.sil(id);
    },
    aylikToplam: async () => {
        const faturalar = await SatisBase.hepsiniGetir();
        const buAy = new Date();
        const ayBaslangic = new Date(buAy.getFullYear(), buAy.getMonth(), 1);
        return faturalar.filter(f => new Date(f.fatura_tarihi) >= ayBaslangic)
            .reduce((toplam, f) => toplam + (parseFloat(f.genel_toplam) || 0), 0);
    }
};

// ==================== İADE FATURALARI ====================
const IadeBase = createCRUD('iade_faturalari');
export const IadeFaturalari = {
    ...IadeBase,
    ekle: async (item) => {
        const id = await IadeBase.ekle(item);
        if (item.iade_tipi === 'satis_iade') {
            for (let k of getKalemler(item)) await StokYonetimi.stokEkle(k.urun_id, k.miktar);
        } else if (item.iade_tipi === 'alis_iade') {
            for (let k of getKalemler(item)) await StokYonetimi.stokDus(k.urun_id, k.miktar);
        }
        return id;
    },
    sil: async (id) => {
        const fatura = await IadeBase.getir(id);
        if (fatura) {
            if (fatura.iade_tipi === 'satis_iade') {
                for (let k of getKalemler(fatura)) await StokYonetimi.stokDus(k.urun_id, k.miktar);
            } else if (fatura.iade_tipi === 'alis_iade') {
                for (let k of getKalemler(fatura)) await StokYonetimi.stokEkle(k.urun_id, k.miktar);
            }
        }
        await IadeBase.sil(id);
    }
};

// ==================== DASHBOARD İSTATİSTİKLERİ ====================
export const Dashboard = {
    istatistikler: async () => {
        const [alis, satis, iade, musteriler, urunler] = await Promise.all([
            AlisFaturalari.hepsiniGetir(),
            SatisFaturalari.hepsiniGetir(),
            IadeFaturalari.hepsiniGetir(),
            Musteriler.hepsiniGetir(),
            Urunler.hepsiniGetir()
        ]);

        const buAy = new Date();
        const ayBaslangic = new Date(buAy.getFullYear(), buAy.getMonth(), 1);

        const aylikAlis = alis.filter(f => new Date(f.fatura_tarihi) >= ayBaslangic)
            .reduce((t, f) => t + (parseFloat(f.genel_toplam) || 0), 0);

        const aylikSatis = satis.filter(f => new Date(f.fatura_tarihi) >= ayBaslangic)
            .reduce((t, f) => t + (parseFloat(f.genel_toplam) || 0), 0);
            
        const kritikUrunler = urunler.filter(u => parseFloat(u.stok_miktari) <= 5);

        return {
            toplam_alis_fatura: alis.length,
            toplam_satis_fatura: satis.length,
            toplam_iade_fatura: iade.length,
            toplam_musteri: musteriler.length,
            toplam_urun: urunler.length,
            kritik_urun_sayisi: kritikUrunler.length,
            kritik_urunler: kritikUrunler,
            aylik_alis_toplam: aylikAlis,
            aylik_satis_toplam: aylikSatis,
            son_alis_faturalari: alis.sort((a, b) => new Date(b.olusturma_tarihi) - new Date(a.olusturma_tarihi)).slice(0, 5),
            son_satis_faturalari: satis.sort((a, b) => new Date(b.olusturma_tarihi) - new Date(a.olusturma_tarihi)).slice(0, 5)
        };
    },

    // Realtime dinleme
    dinle: async (callback) => {
        if (firebaseConnected) {
            const { ref, onValue } = await getFirebaseRefs();
            const collections = ['alis_faturalari', 'satis_faturalari', 'iade_faturalari', 'musteriler', 'urunler'];
            collections.forEach(col => {
                onValue(ref(firebaseDb, col), async () => {
                    const stats = await Dashboard.istatistikler();
                    callback(stats);
                });
            });
        } else {
            // İlk yükleme
            const stats = await Dashboard.istatistikler();
            callback(stats);

            // LocalDB değişikliklerini dinle — leak'i engelle
            const previous = _activeLocalListeners.get('__dashboard__');
            if (previous) window.removeEventListener('localdb-change', previous);
            const handler = async () => {
                const stats = await Dashboard.istatistikler();
                callback(stats);
            };
            _activeLocalListeners.set('__dashboard__', handler);
            window.addEventListener('localdb-change', handler);
        }
    }
};

// ==================== YARDIMCI FONKSİYONLAR ====================
export const Yardimci = {
    // Para formatla
    paraFormat: (tutar) => {
        return new Intl.NumberFormat('tr-TR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(tutar || 0);
    },

    // Tarih formatla
    tarihFormat: (tarih) => {
        if (!tarih) return '-';
        return new Date(tarih).toLocaleDateString('tr-TR');
    },

    // Benzersiz ID oluştur
    benzersizId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substring(2);
    },
    
    // Fatura numarası oluştur
    faturaNo: (prefix = 'FTR') => {
        const tarih = new Date();
        const yil = tarih.getFullYear();
        const ay = String(tarih.getMonth() + 1).padStart(2, '0');
        const gun = String(tarih.getDate()).padStart(2, '0');
        const seri = String(Math.floor(Math.random() * 10000)).padStart(4, '0');
        return `${prefix}-${yil}${ay}${gun}-${seri}`;
    }
};

// ==================== SYNC (LocalStorage <-> Firebase) ====================
export const Sync = {
    collections: ['musteriler', 'urunler', 'alis_faturalari', 'satis_faturalari', 'iade_faturalari'],
    isSyncing: false,
    
    // Son senkronizasyon zamanını al
    getLastSyncTime() {
        return localStorage.getItem('emuhasebe_last_sync');
    },
    
    // Son senkronizasyon zamanını kaydet
    setLastSyncTime() {
        const now = new Date().toISOString();
        localStorage.setItem('emuhasebe_last_sync', now);
        lastSyncTime = now;
        return now;
    },
    
    // LocalStorage verilerini Firebase'e yükle
    uploadToFirebase: async (showToast = true) => {
        if (!firebaseConnected) {
            console.warn('Firebase bağlantısı yok, sync yapılamaz.');
            if (showToast) notify.warning('Firebase bağlantısı yok, veriler yüklenemedi.');
            return false;
        }

        if (Sync.isSyncing) return false;
        Sync.isSyncing = true;

        try {
            const { ref, set, get } = await getFirebaseRefs();
            let uploadedCount = 0;

            for (const col of Sync.collections) {
                const localData = LocalDB.get(col);
                const localEntries = Object.entries(localData);

                if (localEntries.length === 0) continue;

                // Firebase'deki mevcut verileri al
                const snapshot = await get(ref(firebaseDb, col));
                const firebaseData = snapshot.val() || {};

                // Local verileri Firebase'e yükle (merge)
                for (const [localId, data] of localEntries) {
                    if (!firebaseData[localId]) {
                        if (localId.startsWith('local_')) {
                            // local_ önekli kayıt: Firebase'e yeni ID ile yükle,
                            // ardından LocalStorage'daki eski local_ kaydını yeni ID ile değiştir.
                            // Böylece bir sonraki sync'te aynı kayıt tekrar yüklenmez.
                            const { push, set: setFn } = await getFirebaseRefs();
                            const newRef = push(ref(firebaseDb, col));
                            const newId = newRef.key;
                            const syncedData = { ...data, syncedAt: new Date().toISOString() };
                            await setFn(newRef, syncedData);

                            // LocalStorage: eski local_ girişini sil, yeni Firebase ID ile kaydet
                            const fresh = LocalDB.get(col);
                            delete fresh[localId];
                            fresh[newId] = syncedData;
                            LocalDB.set(col, fresh);
                        } else {
                            // Normal ID'li kayıtları aynı ID ile yükle
                            await set(ref(firebaseDb, `${col}/${localId}`), { ...data, syncedAt: new Date().toISOString() });
                        }
                        uploadedCount++;
                    }
                }
            }

            Sync.setLastSyncTime();
            console.log(`✅ ${uploadedCount} kayıt Firebase'e yüklendi`);
            if (showToast && uploadedCount > 0) {
                notify.sync(`${uploadedCount} kayıt Firebase'e yüklendi`);
            }
            return true;
        } catch (error) {
            console.error('Upload hatası:', error);
            if (showToast) notify.error('Veriler yüklenirken hata oluştu!');
            return false;
        } finally {
            Sync.isSyncing = false;
        }
    },
    
    // Firebase verilerini LocalStorage'a indir
    downloadFromFirebase: async (showToast = true) => {
        if (!firebaseConnected) {
            console.warn('Firebase bağlantısı yok, download yapılamaz.');
            if (showToast) notify.warning('Firebase bağlantısı yok, veriler indirilemedi.');
            return false;
        }
        
        if (Sync.isSyncing) return false;
        Sync.isSyncing = true;
        
        try {
            const { ref, get } = await getFirebaseRefs();
            let downloadedCount = 0;
            
            for (const col of Sync.collections) {
                const snapshot = await get(ref(firebaseDb, col));
                const firebaseData = snapshot.val() || {};
                const localData = LocalDB.get(col);
                
                // Firebase verilerini local'e merge et
                const mergedData = { ...localData };
                for (const [fbId, fbData] of Object.entries(firebaseData)) {
                    if (!mergedData[fbId]) {
                        mergedData[fbId] = fbData;
                        downloadedCount++;
                    }
                }
                
                LocalDB.set(col, mergedData);
            }
            
            Sync.setLastSyncTime();
            console.log(`✅ ${downloadedCount} kayıt LocalStorage'a indirildi`);
            if (showToast && downloadedCount > 0) {
                notify.sync(`${downloadedCount} kayıt LocalStorage'a indirildi`);
            }
            return true;
        } catch (error) {
            console.error('Download hatası:', error);
            if (showToast) notify.error('Veriler indirilirken hata oluştu!');
            return false;
        } finally {
            Sync.isSyncing = false;
        }
    },
    
    // İki yönlü tam senkronizasyon
    fullSync: async (showToast = true) => {
        if (!firebaseConnected) {
            if (showToast) notify.warning('Firebase bağlantısı yok, senkronizasyon yapılamadı.');
            return false;
        }
        
        if (Sync.isSyncing) {
            if (showToast) notify.info('Senkronizasyon zaten devam ediyor...');
            return false;
        }
        
        const syncToast = showToast ? notify.sync('Veriler senkronize ediliyor...', 0) : null;
        
        try {
            // Önce Firebase'den indir
            await Sync.downloadFromFirebase(false);
            // Sonra local'i Firebase'e yükle
            await Sync.uploadToFirebase(false);
            
            Sync.setLastSyncTime();
            
            if (syncToast) syncToast.remove();
            if (showToast) notify.success('Veriler başarıyla senkronize edildi! 🎉');
            console.log('🔄 Tam senkronizasyon tamamlandı');
            return true;
        } catch (error) {
            console.error('Sync hatası:', error);
            if (syncToast) syncToast.remove();
            if (showToast) notify.error('Senkronizasyon sırasında hata oluştu!');
            return false;
        }
    },
    
    // Otomatik senkronizasyon başlat
    startAutoSync: (intervalMs = 60000) => {
        // Her dakika senkronize et
        setInterval(() => {
            if (firebaseConnected && !getForceLocalMode()) {
                Sync.fullSync(false).then(success => {
                    if (success) console.log('⏰ Otomatik senkronizasyon tamamlandı');
                });
            }
        }, intervalMs);
        console.log(`⏰ Otomatik senkronizasyon başlatıldı (${intervalMs/1000}sn)`);
    },
    
    // LocalStorage'ı temizle
    clearLocal: (showToast = true) => {
        Sync.collections.forEach(col => {
            localStorage.removeItem(`emuhasebe_${col}`);
        });
        console.log('🗑️ LocalStorage temizlendi');
        if (showToast) notify.info('Yerel veriler temizlendi');
    }
};

// Demo veri: koleksiyon başına TEK set() çağrısıyla toplu yazma.
// 1600 ayrı push yerine 5 yazma işlemi — saniyeler içinde biter, çoğalma riski yok.
window.loadDemoData = async function() {
    const btn = document.getElementById('demoDataBtn');
    try {
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Yükleniyor...'; }
        notify.info('Demo veriler hazırlanıyor, lütfen bekleyin...');

        const seed = createSeedData();
        // seed: { musteriler:{id:obj}, urunler:{...}, satis_faturalari:{...}, ... }

        // Çakışmayı önlemek için tüm anahtarlara "demo_" öneki eklenir.
        // Kalemlerdeki urun_id referansı da aynı önekle güncellenir ki ürünle eşleşsin.
        const fixKalem = (k) => ({ ...k, urun_id: k.urun_id ? `demo_${k.urun_id}` : k.urun_id });
        const prefixle = (col, obj) => {
            const yeni = {};
            for (const [k, v] of Object.entries(obj)) {
                const kayit = (v.kalemler && Array.isArray(v.kalemler))
                    ? { ...v, kalemler: v.kalemler.map(fixKalem) }
                    : v;
                yeni[`demo_${k}`] = kayit;
            }
            return yeni;
        };

        const collections = ['musteriler','urunler','satis_faturalari','alis_faturalari','iade_faturalari'];

        if (firebaseConnected) {
            const { ref, get, set } = await getFirebaseRefs();
            for (const col of collections) {
                const snap = await get(ref(firebaseDb, col));
                const mevcut = snap.val() || {};
                await set(ref(firebaseDb, col), { ...mevcut, ...prefixle(col, seed[col]) });
            }
        } else {
            for (const col of collections) {
                const mevcut = LocalDB.get(col);
                LocalDB.set(col, { ...mevcut, ...prefixle(col, seed[col]) });
            }
        }

        notify.success('Demo veriler başarıyla eklendi! (700 satış, 700 alış, 200 iade)');
        setTimeout(() => window.location.reload(), 1500);
    } catch (e) {
        console.error(e);
        notify.error('Demo veriler eklenirken hata oluştu: ' + e.message);
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<span class="demo-data-icon"><i class="fas fa-database"></i></span><span class="demo-data-label">Demo Veri Ekle</span>'; }
    }
};

// ==================== CANLI BİLDİRİMLER (REAL-TIME NOTIFICATIONS) ====================
let isCanliBildirimStarted = false;
async function baslatCanliBildirimler() {
    if (!firebaseConnected || isCanliBildirimStarted) return;
    
    try {
        const { ref, onChildAdded } = await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-database.js');
        const baslangicZamani = new Date().getTime();

        const dinleVeBildir = (koleksiyon, baslikTuru, ikon) => {
            const koleksiyonRef = ref(firebaseDb, koleksiyon);
            onChildAdded(koleksiyonRef, (snapshot) => {
                const data = snapshot.val();
                if (!data || !data.olusturma_tarihi) return;
                
                const kayitZamani = new Date(data.olusturma_tarihi).getTime();
                
                // Sadece uygulama açıldıktan SONRA eklenen yeni kayıtları bildir
                if (kayitZamani > baslangicZamani) {
                    const tutar = data.genel_toplam ? Yardimci.paraFormat(data.genel_toplam) + ' ₺' : '';
                    const mesaj = `Yeni ${baslikTuru} Kesildi: ${data.fatura_no || ''} ${tutar}`;
                    notify(mesaj, 'success', { icon: ikon, duration: 6000 });
                }
            });
        };

        dinleVeBildir('satis_faturalari', 'Satış Faturası', 'file-invoice-dollar');
        dinleVeBildir('alis_faturalari', 'Alış Faturası', 'file-invoice');
        dinleVeBildir('iade_faturalari', 'İade Faturası', 'receipt');
        
        isCanliBildirimStarted = true;
        console.log('📡 Canlı fatura bildirimleri aktif!');
    } catch (e) {
        console.error('Canlı bildirimler başlatılamadı:', e);
    }
}

// ==================== BAŞLATMA ====================
// NOT: initialized flag kaldırıldı - her sayfa yüklenmesinde mod kontrolü yapılır
let initPromise = null;

export async function init() {
    // Tek bir init işlemi garanti et
    if (initPromise) return initPromise;
    
    initPromise = (async () => {
        // Bildirim sistemi hazır
        
        // Her zaman güncel forceLocalMode durumunu oku
        await initFirebase();
        seedLocalDataIfEmpty();
        
        // Global erişim için window'a ekle
        window.DB = {
            isOnline,
            getMode,
            setMode,
            loadDemoData: window.loadDemoData,
            Musteriler,
            Urunler,
            AlisFaturalari,
            SatisFaturalari,
            IadeFaturalari,
            Dashboard,
            Yardimci,
            Sync,
            Toast: window.Toast
        };
        // Durum göster
        const mode = getMode();
        const forceLocal = getForceLocalMode();

        if (mode === 'firebase') {
            // Canlı bildirimleri başlat
            baslatCanliBildirimler();

            // OTOMATİK SENKRONİZASYON TAMAMEN KALDIRILDI.
            // Sebep: her sayfa açılışında LocalStorage'daki eski kayıtların Firebase'e
            // geri yüklenmesi (ve download ile geri inmesi) verilerin üstel çoğalmasına
            // yol açıyordu. Firebase modunda artık LocalStorage bir kopya olarak kullanılmaz;
            // tüm okuma/yazma doğrudan Firebase üzerinden yapılır. Sync yalnızca manuel
            // butonla (Sync.fullSync) tetiklenir.
        }
        
        const status = mode === 'firebase' ? '🔥 Firebase' : '💾 LocalStorage';
        console.log(`${status} modu aktif${forceLocal ? ' (Manuel)' : ''}`);
        
        return firebaseConnected;
    })();
    
    return initPromise;
}

// Otomatik başlat
init();

// Default export
export default {
    init,
    isOnline,
    getMode,
    setMode,
    Musteriler,
    Urunler,
    AlisFaturalari,
    SatisFaturalari,
    IadeFaturalari,
    Dashboard,
    Yardimci,
    Sync
};
