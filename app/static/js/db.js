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

// Firebase modüllerini dinamik import et
async function initFirebase() {
    // Manuel local mod aktifse Firebase'e bağlanma
    if (getForceLocalMode()) {
        console.log('💾 Manuel LocalStorage modu aktif');
        firebaseConnected = false;
        return false;
    }
    
    try {
        const { initializeApp } = await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-app.js');
        const { getDatabase, ref, get, onValue } = await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-database.js');
        const { firebaseConfig } = await import('./firebase-config.js');
        
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
        return 'local_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
    }
};

function buildSeedDate(offsetDays) {
    return new Date(Date.now() - offsetDays * 24 * 60 * 60 * 1000).toISOString();
}

function createSeedData() {
    const customers = {
        customer_1: { ad: 'Atlas Endüstri A.Ş.', tip: 'kurumsal', sehir: 'İstanbul', telefon: '0212 555 01 01', olusturma_tarihi: buildSeedDate(42), guncelleme_tarihi: buildSeedDate(42) },
        customer_2: { ad: 'Nova Teknoloji Ltd. Şti.', tip: 'kurumsal', sehir: 'Ankara', telefon: '0312 555 01 02', olusturma_tarihi: buildSeedDate(35), guncelleme_tarihi: buildSeedDate(35) },
        customer_3: { ad: 'Mavi Sağlık Hizmetleri', tip: 'kurumsal', sehir: 'İzmir', telefon: '0232 555 01 03', olusturma_tarihi: buildSeedDate(30), guncelleme_tarihi: buildSeedDate(30) },
        customer_4: { ad: 'Kuzey Lojistik', tip: 'kurumsal', sehir: 'Bursa', telefon: '0224 555 01 04', olusturma_tarihi: buildSeedDate(28), guncelleme_tarihi: buildSeedDate(28) },
        customer_5: { ad: 'Deniz Yapı Market', tip: 'kurumsal', sehir: 'Antalya', telefon: '0242 555 01 05', olusturma_tarihi: buildSeedDate(24), guncelleme_tarihi: buildSeedDate(24) },
        customer_6: { ad: 'Selin Yılmaz', tip: 'bireysel', sehir: 'Eskişehir', telefon: '0532 111 22 33', olusturma_tarihi: buildSeedDate(20), guncelleme_tarihi: buildSeedDate(20) },
        customer_7: { ad: 'Emre Kaya', tip: 'bireysel', sehir: 'Konya', telefon: '0533 222 33 44', olusturma_tarihi: buildSeedDate(18), guncelleme_tarihi: buildSeedDate(18) },
        customer_8: { ad: 'Pera Danışmanlık', tip: 'kurumsal', sehir: 'İstanbul', telefon: '0212 555 01 08', olusturma_tarihi: buildSeedDate(16), guncelleme_tarihi: buildSeedDate(16) },
        customer_9: { ad: 'Yıldız Ofis Çözümleri', tip: 'kurumsal', sehir: 'Ankara', telefon: '0312 555 01 09', olusturma_tarihi: buildSeedDate(13), guncelleme_tarihi: buildSeedDate(13) },
        customer_10: { ad: 'Alya Bilişim', tip: 'kurumsal', sehir: 'Kocaeli', telefon: '0262 555 01 10', olusturma_tarihi: buildSeedDate(11), guncelleme_tarihi: buildSeedDate(11) }
    };

    const products = {
        product_1: { ad: 'Dell Latitude 5540', kategori: 'Bilgisayar', stok: 18, alis_fiyat: 33500, satis_fiyat: 41900, kdv: 20, olusturma_tarihi: buildSeedDate(50), guncelleme_tarihi: buildSeedDate(50) },
        product_2: { ad: 'HP ProBook 450 G10', kategori: 'Bilgisayar', stok: 14, alis_fiyat: 28500, satis_fiyat: 35900, kdv: 20, olusturma_tarihi: buildSeedDate(49), guncelleme_tarihi: buildSeedDate(49) },
        product_3: { ad: 'Logitech MX Master 3S', kategori: 'Aksesuar', stok: 36, alis_fiyat: 1450, satis_fiyat: 2190, kdv: 20, olusturma_tarihi: buildSeedDate(48), guncelleme_tarihi: buildSeedDate(48) },
        product_4: { ad: 'Samsung 1TB NVMe SSD', kategori: 'Depolama', stok: 42, alis_fiyat: 1950, satis_fiyat: 2790, kdv: 20, olusturma_tarihi: buildSeedDate(47), guncelleme_tarihi: buildSeedDate(47) },
        product_5: { ad: 'Brother HL-L2375DW', kategori: 'Yazıcı', stok: 11, alis_fiyat: 7250, satis_fiyat: 8990, kdv: 20, olusturma_tarihi: buildSeedDate(46), guncelleme_tarihi: buildSeedDate(46) },
        product_6: { ad: 'Cisco 24 Port Switch', kategori: 'Ağ', stok: 9, alis_fiyat: 9800, satis_fiyat: 12490, kdv: 20, olusturma_tarihi: buildSeedDate(45), guncelleme_tarihi: buildSeedDate(45) },
        product_7: { ad: 'A4 Fotokopi Kağıdı', kategori: 'Sarf', stok: 240, alis_fiyat: 95, satis_fiyat: 149, kdv: 20, olusturma_tarihi: buildSeedDate(44), guncelleme_tarihi: buildSeedDate(44) },
        product_8: { ad: 'IP Kamera 4MP', kategori: 'Güvenlik', stok: 26, alis_fiyat: 2100, satis_fiyat: 2990, kdv: 20, olusturma_tarihi: buildSeedDate(43), guncelleme_tarihi: buildSeedDate(43) },
        product_9: { ad: 'Ofis Koltuğu Ergonomik', kategori: 'Ofis', stok: 15, alis_fiyat: 2650, satis_fiyat: 3490, kdv: 20, olusturma_tarihi: buildSeedDate(42), guncelleme_tarihi: buildSeedDate(42) },
        product_10: { ad: 'İşletim Sistemi Lisans Paketi', kategori: 'Yazılım', stok: 60, alis_fiyat: 1250, satis_fiyat: 1890, kdv: 20, olusturma_tarihi: buildSeedDate(41), guncelleme_tarihi: buildSeedDate(41) }
    };

    const customerList = Object.entries(customers).map(([id, data]) => ({ id, ...data }));
    const productList = Object.entries(products).map(([id, data]) => ({ id, ...data }));

    const salesInvoices = {};
    const purchaseInvoices = {};
    const returnInvoices = {};

    for (let i = 0; i < 10; i++) {
        const customer = customerList[i % customerList.length];
        const product = productList[i % productList.length];
        const saleQty = 2 + (i % 4);
        const saleTotal = product.satis_fiyat * saleQty;
        const saleDate = buildSeedDate(9 - i);
        salesInvoices[`sale_${i + 1}`] = {
            fatura_no: `SF-2026-${String(i + 1).padStart(4, '0')}`,
            musteri_adi: customer.ad,
            fatura_tarihi: saleDate,
            genel_toplam: saleTotal,
            durum: i % 3 === 0 ? 'beklemede' : 'odendi',
            kalemler: [{ urun_adi: product.ad, miktar: saleQty, birim_fiyat: product.satis_fiyat, toplam: saleTotal }],
            olusturma_tarihi: saleDate,
            guncelleme_tarihi: saleDate
        };

        const purchaseQty = 4 + (i % 5);
        const purchaseTotal = product.alis_fiyat * purchaseQty;
        const purchaseDate = buildSeedDate(18 - i);
        purchaseInvoices[`purchase_${i + 1}`] = {
            fatura_no: `AF-2026-${String(i + 1).padStart(4, '0')}`,
            tedarikci_adi: ['Tekno Dağıtım', 'Marmara Bilişim', 'Anadolu Tedarik', 'Metro Elektronik', 'Penta Çözüm'][i % 5],
            fatura_tarihi: purchaseDate,
            genel_toplam: purchaseTotal,
            durum: i % 4 === 0 ? 'beklemede' : 'odendi',
            kalemler: [{ urun_adi: product.ad, miktar: purchaseQty, birim_fiyat: product.alis_fiyat, toplam: purchaseTotal }],
            olusturma_tarihi: purchaseDate,
            guncelleme_tarihi: purchaseDate
        };

        const returnDate = buildSeedDate(5 - i);
        returnInvoices[`return_${i + 1}`] = {
            fatura_no: `IF-2026-${String(i + 1).padStart(4, '0')}`,
            musteri_adi: customer.ad,
            fatura_tarihi: returnDate,
            genel_toplam: Math.round(product.satis_fiyat * 0.5),
            sebep: ['Ürün uyumsuzluğu', 'Kutuda hasar', 'Yanlış model', 'Kurulum problemi'][i % 4],
            kalemler: [{ urun_adi: product.ad, miktar: 1, birim_fiyat: Math.round(product.satis_fiyat * 0.5), toplam: Math.round(product.satis_fiyat * 0.5) }],
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
function createCRUD(collectionName) {
    return {
        // Realtime dinle
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
                // LocalStorage için polling veya event dinle
                const getData = () => {
                    const data = LocalDB.get(collectionName);
                    const items = Object.entries(data).map(([id, val]) => ({ id, ...val }));
                    callback(items);
                };
                getData(); // İlk yükleme
                
                // Değişiklik dinle
                window.addEventListener('localdb-change', (e) => {
                    if (e.detail.collection === collectionName) {
                        getData();
                    }
                });
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

// ==================== ALIŞ FATURALARI ====================
export const AlisFaturalari = {
    ...createCRUD('alis_faturalari'),
    
    // Bu ayki toplam
    aylikToplam: async () => {
        const faturalar = await AlisFaturalari.hepsiniGetir();
        const buAy = new Date();
        const ayBaslangic = new Date(buAy.getFullYear(), buAy.getMonth(), 1);
        
        return faturalar
            .filter(f => new Date(f.fatura_tarihi) >= ayBaslangic)
            .reduce((toplam, f) => toplam + (parseFloat(f.genel_toplam) || 0), 0);
    }
};

// ==================== SATIŞ FATURALARI ====================
export const SatisFaturalari = {
    ...createCRUD('satis_faturalari'),
    
    // Bu ayki toplam
    aylikToplam: async () => {
        const faturalar = await SatisFaturalari.hepsiniGetir();
        const buAy = new Date();
        const ayBaslangic = new Date(buAy.getFullYear(), buAy.getMonth(), 1);
        
        return faturalar
            .filter(f => new Date(f.fatura_tarihi) >= ayBaslangic)
            .reduce((toplam, f) => toplam + (parseFloat(f.genel_toplam) || 0), 0);
    }
};

// ==================== İADE FATURALARI ====================
export const IadeFaturalari = createCRUD('iade_faturalari');

// ==================== DASHBOARD İSTATİSTİKLERİ ====================
export const Dashboard = {
    // Tüm istatistikleri getir
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

        const aylikAlis = alis
            .filter(f => new Date(f.fatura_tarihi) >= ayBaslangic)
            .reduce((t, f) => t + (parseFloat(f.genel_toplam) || 0), 0);

        const aylikSatis = satis
            .filter(f => new Date(f.fatura_tarihi) >= ayBaslangic)
            .reduce((t, f) => t + (parseFloat(f.genel_toplam) || 0), 0);

        return {
            toplam_alis_fatura: alis.length,
            toplam_satis_fatura: satis.length,
            toplam_iade_fatura: iade.length,
            toplam_musteri: musteriler.length,
            toplam_urun: urunler.length,
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
            
            // LocalDB değişikliklerini dinle
            window.addEventListener('localdb-change', async () => {
                const stats = await Dashboard.istatistikler();
                callback(stats);
            });
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
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
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
            loadDemoData,
            Musteriler,
            Urunler,
            AlisFaturalari,
            SatisFaturalari,
            IadeFaturalari,
            Dashboard,
            Yardimci,
            Sync,
            Toast
        };
        // Durum göster
        const mode = getMode();
        const forceLocal = getForceLocalMode();
        
        if (mode === 'firebase') {
            // Firebase modunda otomatik senkronizasyon yap
                loadDemoData,
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
