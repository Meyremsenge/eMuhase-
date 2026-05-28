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
    return new Date(Date.now() - offsetDays * 24 * 60 * 60 * 1000).toISOString();
}

function createSeedData() {
    // Müşteriler ve tedarikçiler — form/list ile aynı alan adlarını kullanır:
    // unvan, tip ∈ {musteri, tedarikci, her_ikisi}, vergi_no, telefon, email, adres, aktif
    const customers = {
        customer_1:  { unvan: 'Atlas Endüstri A.Ş.',       tip: 'musteri',   vergi_no: '1112223334', telefon: '0212 555 01 01', email: 'info@atlas.com',  adres: 'İstanbul', aktif: true, olusturma_tarihi: buildSeedDate(42), guncelleme_tarihi: buildSeedDate(42) },
        customer_2:  { unvan: 'Nova Teknoloji Ltd. Şti.',  tip: 'musteri',   vergi_no: '2223334445', telefon: '0312 555 01 02', email: 'info@nova.com',   adres: 'Ankara',   aktif: true, olusturma_tarihi: buildSeedDate(35), guncelleme_tarihi: buildSeedDate(35) },
        customer_3:  { unvan: 'Mavi Sağlık Hizmetleri',    tip: 'musteri',   vergi_no: '3334445556', telefon: '0232 555 01 03', email: 'info@mavi.com',   adres: 'İzmir',    aktif: true, olusturma_tarihi: buildSeedDate(30), guncelleme_tarihi: buildSeedDate(30) },
        customer_4:  { unvan: 'Kuzey Lojistik',            tip: 'musteri',   vergi_no: '4445556667', telefon: '0224 555 01 04', email: 'info@kuzey.com',  adres: 'Bursa',    aktif: true, olusturma_tarihi: buildSeedDate(28), guncelleme_tarihi: buildSeedDate(28) },
        customer_5:  { unvan: 'Deniz Yapı Market',         tip: 'musteri',   vergi_no: '5556667778', telefon: '0242 555 01 05', email: 'info@deniz.com',  adres: 'Antalya',  aktif: true, olusturma_tarihi: buildSeedDate(24), guncelleme_tarihi: buildSeedDate(24) },
        customer_6:  { unvan: 'Selin Yılmaz',              tip: 'musteri',   vergi_no: '12345678901',telefon: '0532 111 22 33', email: 'selin@example.com', adres: 'Eskişehir', aktif: true, olusturma_tarihi: buildSeedDate(20), guncelleme_tarihi: buildSeedDate(20) },
        customer_7:  { unvan: 'Tekno Dağıtım',             tip: 'tedarikci', vergi_no: '6667778889', telefon: '0212 555 02 01', email: 'info@tekno.com',  adres: 'İstanbul', aktif: true, olusturma_tarihi: buildSeedDate(18), guncelleme_tarihi: buildSeedDate(18) },
        customer_8:  { unvan: 'Marmara Bilişim',           tip: 'tedarikci', vergi_no: '7778889990', telefon: '0212 555 02 02', email: 'info@marmara.com',adres: 'İstanbul', aktif: true, olusturma_tarihi: buildSeedDate(16), guncelleme_tarihi: buildSeedDate(16) },
        customer_9:  { unvan: 'Anadolu Tedarik',           tip: 'tedarikci', vergi_no: '8889990001', telefon: '0312 555 02 03', email: 'info@anadolu.com',adres: 'Ankara',   aktif: true, olusturma_tarihi: buildSeedDate(13), guncelleme_tarihi: buildSeedDate(13) },
        customer_10: { unvan: 'Penta Çözüm',               tip: 'her_ikisi', vergi_no: '9990001112', telefon: '0262 555 02 04', email: 'info@penta.com',  adres: 'Kocaeli',  aktif: true, olusturma_tarihi: buildSeedDate(11), guncelleme_tarihi: buildSeedDate(11) }
    };

    // Ürünler — form/list ile aynı alan adlarını kullanır:
    // kod, ad, birim, kdv_orani, stok_miktari, alis_fiyat, satis_fiyat, aktif
    const products = {
        product_1:  { kod: 'ELK-001', ad: 'Dell Latitude 5540',         birim: 'Adet',  kdv_orani: 20, stok_miktari: 18,  alis_fiyat: 33500, satis_fiyat: 41900, aktif: true, olusturma_tarihi: buildSeedDate(50), guncelleme_tarihi: buildSeedDate(50) },
        product_2:  { kod: 'ELK-002', ad: 'HP ProBook 450 G10',         birim: 'Adet',  kdv_orani: 20, stok_miktari: 14,  alis_fiyat: 28500, satis_fiyat: 35900, aktif: true, olusturma_tarihi: buildSeedDate(49), guncelleme_tarihi: buildSeedDate(49) },
        product_3:  { kod: 'ELK-010', ad: 'Logitech MX Master 3S',      birim: 'Adet',  kdv_orani: 20, stok_miktari: 36,  alis_fiyat: 1450,  satis_fiyat: 2190,  aktif: true, olusturma_tarihi: buildSeedDate(48), guncelleme_tarihi: buildSeedDate(48) },
        product_4:  { kod: 'ELK-011', ad: 'Samsung 1TB NVMe SSD',       birim: 'Adet',  kdv_orani: 20, stok_miktari: 42,  alis_fiyat: 1950,  satis_fiyat: 2790,  aktif: true, olusturma_tarihi: buildSeedDate(47), guncelleme_tarihi: buildSeedDate(47) },
        product_5:  { kod: 'ELK-005', ad: 'Brother HL-L2375DW',         birim: 'Adet',  kdv_orani: 20, stok_miktari: 11,  alis_fiyat: 7250,  satis_fiyat: 8990,  aktif: true, olusturma_tarihi: buildSeedDate(46), guncelleme_tarihi: buildSeedDate(46) },
        product_6:  { kod: 'ELK-006', ad: 'Cisco 24 Port Switch',       birim: 'Adet',  kdv_orani: 20, stok_miktari: 9,   alis_fiyat: 9800,  satis_fiyat: 12490, aktif: true, olusturma_tarihi: buildSeedDate(45), guncelleme_tarihi: buildSeedDate(45) },
        product_7:  { kod: 'SFT-003', ad: 'A4 Fotokopi Kağıdı',         birim: 'Paket', kdv_orani: 20, stok_miktari: 240, alis_fiyat: 95,    satis_fiyat: 149,   aktif: true, olusturma_tarihi: buildSeedDate(44), guncelleme_tarihi: buildSeedDate(44) },
        product_8:  { kod: 'TEK-001', ad: 'IP Kamera 4MP',              birim: 'Adet',  kdv_orani: 20, stok_miktari: 26,  alis_fiyat: 2100,  satis_fiyat: 2990,  aktif: true, olusturma_tarihi: buildSeedDate(43), guncelleme_tarihi: buildSeedDate(43) },
        product_9:  { kod: 'OFS-001', ad: 'Ofis Koltuğu Ergonomik',     birim: 'Adet',  kdv_orani: 20, stok_miktari: 15,  alis_fiyat: 2650,  satis_fiyat: 3490,  aktif: true, olusturma_tarihi: buildSeedDate(42), guncelleme_tarihi: buildSeedDate(42) },
        product_10: { kod: 'SFT-001', ad: 'İşletim Sistemi Lisans Paketi', birim: 'Adet', kdv_orani: 20, stok_miktari: 60, alis_fiyat: 1250, satis_fiyat: 1890, aktif: true, olusturma_tarihi: buildSeedDate(41), guncelleme_tarihi: buildSeedDate(41) }
    };

    const customerList = Object.entries(customers).map(([id, data]) => ({ id, ...data }));
    const productList = Object.entries(products).map(([id, data]) => ({ id, ...data }));
    const tedarikciList = customerList.filter(c => c.tip === 'tedarikci' || c.tip === 'her_ikisi');
    const aliciList = customerList.filter(c => c.tip === 'musteri' || c.tip === 'her_ikisi');

    const salesInvoices = {};
    const purchaseInvoices = {};
    const returnInvoices = {};

    for (let i = 0; i < 10; i++) {
        const customer = aliciList[i % aliciList.length];
        const tedarikci = tedarikciList[i % tedarikciList.length];
        const product = productList[i % productList.length];

        const saleQty = 2 + (i % 4);
        const saleTotal = product.satis_fiyat * saleQty;
        const saleDate = buildSeedDate(9 - i);
        salesInvoices[`sale_${i + 1}`] = {
            fatura_no: `SF-2026-${String(i + 1).padStart(4, '0')}`,
            musteri_id: customer.id,
            musteri_adi: customer.unvan,
            fatura_tarihi: saleDate,
            genel_toplam: saleTotal,
            ara_toplam: saleTotal,
            kdv_toplam: 0,
            durum: i % 3 === 0 ? 'beklemede' : 'odendi',
            kalemler: [{ aciklama: product.ad, urun_adi: product.ad, miktar: saleQty, birim_fiyat: product.satis_fiyat, kdv_orani: 20, toplam: saleTotal, genel_toplam: saleTotal }],
            olusturma_tarihi: saleDate,
            guncelleme_tarihi: saleDate
        };

        const purchaseQty = 4 + (i % 5);
        const purchaseTotal = product.alis_fiyat * purchaseQty;
        const purchaseDate = buildSeedDate(18 - i);
        purchaseInvoices[`purchase_${i + 1}`] = {
            fatura_no: `AF-2026-${String(i + 1).padStart(4, '0')}`,
            tedarikci_id: tedarikci.id,
            tedarikci_adi: tedarikci.unvan,
            fatura_tarihi: purchaseDate,
            genel_toplam: purchaseTotal,
            ara_toplam: purchaseTotal,
            kdv_toplam: 0,
            durum: i % 4 === 0 ? 'beklemede' : 'odendi',
            kalemler: [{ aciklama: product.ad, urun_adi: product.ad, miktar: purchaseQty, birim_fiyat: product.alis_fiyat, kdv_orani: 20, toplam: purchaseTotal, genel_toplam: purchaseTotal }],
            olusturma_tarihi: purchaseDate,
            guncelleme_tarihi: purchaseDate
        };

        const returnDate = buildSeedDate(5 - i);
        const returnTotal = Math.round(product.satis_fiyat * 0.5);
        returnInvoices[`return_${i + 1}`] = {
            fatura_no: `IF-2026-${String(i + 1).padStart(4, '0')}`,
            iade_tipi: i % 2 === 0 ? 'satis_iade' : 'alis_iade',
            cari_id: i % 2 === 0 ? customer.id : tedarikci.id,
            cari_adi: i % 2 === 0 ? customer.unvan : tedarikci.unvan,
            fatura_tarihi: returnDate,
            genel_toplam: returnTotal,
            ara_toplam: returnTotal,
            kdv_toplam: 0,
            durum: i % 3 === 0 ? 'beklemede' : 'tamamlandi',
            sebep: ['Ürün uyumsuzluğu', 'Kutuda hasar', 'Yanlış model', 'Kurulum problemi'][i % 4],
            kalemler: [{ aciklama: product.ad, urun_adi: product.ad, miktar: 1, birim_fiyat: returnTotal, kdv_orani: 20, toplam: returnTotal, genel_toplam: returnTotal }],
            olusturma_tarihi: returnDate,
            guncelleme_tarihi: returnDate
        };
    }

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
                
                if (localEntries.length > 0) {
                    // Firebase'deki mevcut verileri al
                    const snapshot = await get(ref(firebaseDb, col));
                    const firebaseData = snapshot.val() || {};
                    
                    // Local verileri Firebase'e yükle (merge)
                    for (const [localId, data] of localEntries) {
                        // Eğer Firebase'de bu ID yoksa veya local daha yeniyse yükle
                        if (!firebaseData[localId]) {
                            if (localId.startsWith('local_')) {
                                // Local ID'li kayıtları yeni Firebase ID ile yükle
                                const { push, set: setFn } = await getFirebaseRefs();
                                const newRef = push(ref(firebaseDb, col));
                                await setFn(newRef, { ...data, syncedAt: new Date().toISOString() });
                            } else {
                                // Normal ID'li kayıtları aynı ID ile yükle
                                await set(ref(firebaseDb, `${col}/${localId}`), { ...data, syncedAt: new Date().toISOString() });
                            }
                            uploadedCount++;
                        }
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

window.loadDemoData = async function() {
    try {
        const btn = document.getElementById('demoDataBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Yükleniyor...';
        }
        
        notify.info("Demo veriler ekleniyor, lütfen bekleyin...");
        
        const seedData = createSeedData();
        const customerList = Object.values(seedData.musteriler);
        const productList = Object.values(seedData.urunler);
        
        // Add 10 customers and products
        for (const data of customerList) {
            await Musteriler.ekle(data);
        }
        for (const data of productList) {
            await Urunler.ekle(data);
        }
        
        // Add 20 invoices each
        for (let i = 0; i < 20; i++) {
            const customer = customerList[i % customerList.length];
            const product = productList[i % productList.length];
            
            const saleQty = 2 + (i % 4);
            const saleTotal = product.satis_fiyat * saleQty;
            const saleDate = buildSeedDate(20 - i);
            await SatisFaturalari.ekle({
                fatura_no: Yardimci.faturaNo('SF'),
                musteri_adi: customer.ad,
                fatura_tarihi: saleDate,
                genel_toplam: saleTotal,
                durum: i % 3 === 0 ? 'beklemede' : 'odendi',
                kalemler: [{ urun_adi: product.ad, miktar: saleQty, birim_fiyat: product.satis_fiyat, toplam: saleTotal }]
            });
            
            const purchaseQty = 4 + (i % 5);
            const purchaseTotal = product.alis_fiyat * purchaseQty;
            const purchaseDate = buildSeedDate(25 - i);
            await AlisFaturalari.ekle({
                fatura_no: Yardimci.faturaNo('AF'),
                tedarikci_adi: ['Tekno Dağıtım', 'Marmara Bilişim', 'Anadolu Tedarik', 'Metro Elektronik', 'Penta Çözüm'][i % 5],
                fatura_tarihi: purchaseDate,
                genel_toplam: purchaseTotal,
                durum: i % 4 === 0 ? 'beklemede' : 'odendi',
                kalemler: [{ urun_adi: product.ad, miktar: purchaseQty, birim_fiyat: product.alis_fiyat, toplam: purchaseTotal }]
            });
            
            const returnDate = buildSeedDate(15 - i);
            await IadeFaturalari.ekle({
                fatura_no: Yardimci.faturaNo('IF'),
                musteri_adi: customer.ad,
                fatura_tarihi: returnDate,
                genel_toplam: Math.round(product.satis_fiyat * 0.5),
                sebep: ['Ürün uyumsuzluğu', 'Kutuda hasar', 'Yanlış model', 'Kurulum problemi'][i % 4],
                kalemler: [{ urun_adi: product.ad, miktar: 1, birim_fiyat: Math.round(product.satis_fiyat * 0.5), toplam: Math.round(product.satis_fiyat * 0.5) }]
            });
        }
        
        notify.success("20 adet demo veri başarıyla eklendi!");
        setTimeout(() => window.location.reload(), 1500);
    } catch (e) {
        console.error(e);
        notify.error("Demo veriler eklenirken hata oluştu.");
    } finally {
        const btn = document.getElementById('demoDataBtn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span class="demo-data-icon"><i class="fas fa-database"></i></span><span class="demo-data-label">Demo Veri Ekle</span>';
        }
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
            
            // Firebase modunda otomatik senkronizasyon yap
            setTimeout(async () => {
                await Sync.fullSync(true);
                // Otomatik sync başlat (her 2 dakikada bir)
                Sync.startAutoSync(120000);
            }, 1000);
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
