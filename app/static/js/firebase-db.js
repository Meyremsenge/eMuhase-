// Firebase Realtime Database Operations
import { initializeApp } from 'https://www.gstatic.com/firebasejs/11.0.0/firebase-app.js';
import { getDatabase, ref, push, set, get, update, remove, onValue, query, orderByChild, equalTo } from 'https://www.gstatic.com/firebasejs/11.0.0/firebase-database.js';
import { firebaseConfig } from './firebase-config.js';

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

// ==================== MÜŞTERİLER ====================
export const Musteriler = {
    // Tüm müşterileri getir (realtime)
    dinle: (callback) => {
        const musteriRef = ref(db, 'musteriler');
        onValue(musteriRef, (snapshot) => {
            const data = snapshot.val();
            const musteriler = data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
            callback(musteriler);
        });
    },

    // Tek seferlik getir
    hepsiniGetir: async () => {
        const snapshot = await get(ref(db, 'musteriler'));
        const data = snapshot.val();
        return data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
    },

    // Tek müşteri getir
    getir: async (id) => {
        const snapshot = await get(ref(db, `musteriler/${id}`));
        return snapshot.val() ? { id, ...snapshot.val() } : null;
    },

    // Yeni müşteri ekle
    ekle: async (musteri) => {
        const yeniRef = push(ref(db, 'musteriler'));
        await set(yeniRef, {
            ...musteri,
            olusturma_tarihi: new Date().toISOString(),
            guncelleme_tarihi: new Date().toISOString()
        });
        return yeniRef.key;
    },

    // Müşteri güncelle
    guncelle: async (id, musteri) => {
        await update(ref(db, `musteriler/${id}`), {
            ...musteri,
            guncelleme_tarihi: new Date().toISOString()
        });
    },

    // Müşteri sil
    sil: async (id) => {
        await remove(ref(db, `musteriler/${id}`));
    },

    // Tip'e göre filtrele
    tipFiltrele: async (tip) => {
        const snapshot = await get(ref(db, 'musteriler'));
        const data = snapshot.val();
        if (!data) return [];
        return Object.entries(data)
            .map(([id, val]) => ({ id, ...val }))
            .filter(m => tip === 'hepsi' || m.tip === tip);
    }
};

// ==================== ÜRÜNLER ====================
export const Urunler = {
    // Tüm ürünleri getir (realtime)
    dinle: (callback) => {
        const urunRef = ref(db, 'urunler');
        onValue(urunRef, (snapshot) => {
            const data = snapshot.val();
            const urunler = data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
            callback(urunler);
        });
    },

    // Tek seferlik getir
    hepsiniGetir: async () => {
        const snapshot = await get(ref(db, 'urunler'));
        const data = snapshot.val();
        return data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
    },

    // Tek ürün getir
    getir: async (id) => {
        const snapshot = await get(ref(db, `urunler/${id}`));
        return snapshot.val() ? { id, ...snapshot.val() } : null;
    },

    // Yeni ürün ekle
    ekle: async (urun) => {
        const yeniRef = push(ref(db, 'urunler'));
        await set(yeniRef, {
            ...urun,
            olusturma_tarihi: new Date().toISOString(),
            guncelleme_tarihi: new Date().toISOString()
        });
        return yeniRef.key;
    },

    // Ürün güncelle
    guncelle: async (id, urun) => {
        await update(ref(db, `urunler/${id}`), {
            ...urun,
            guncelleme_tarihi: new Date().toISOString()
        });
    },

    // Ürün sil
    sil: async (id) => {
        await remove(ref(db, `urunler/${id}`));
    }
};

// ==================== ALIŞ FATURALARI ====================
export const AlisFaturalari = {
    // Tüm faturaları getir (realtime)
    dinle: (callback) => {
        const faturaRef = ref(db, 'alis_faturalari');
        onValue(faturaRef, (snapshot) => {
            const data = snapshot.val();
            const faturalar = data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
            callback(faturalar);
        });
    },

    // Tek seferlik getir
    hepsiniGetir: async () => {
        const snapshot = await get(ref(db, 'alis_faturalari'));
        const data = snapshot.val();
        return data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
    },

    // Tek fatura getir
    getir: async (id) => {
        const snapshot = await get(ref(db, `alis_faturalari/${id}`));
        return snapshot.val() ? { id, ...snapshot.val() } : null;
    },

    // Yeni fatura ekle
    ekle: async (fatura) => {
        const yeniRef = push(ref(db, 'alis_faturalari'));
        await set(yeniRef, {
            ...fatura,
            olusturma_tarihi: new Date().toISOString(),
            guncelleme_tarihi: new Date().toISOString()
        });
        return yeniRef.key;
    },

    // Fatura güncelle
    guncelle: async (id, fatura) => {
        await update(ref(db, `alis_faturalari/${id}`), {
            ...fatura,
            guncelleme_tarihi: new Date().toISOString()
        });
    },

    // Fatura sil
    sil: async (id) => {
        await remove(ref(db, `alis_faturalari/${id}`));
    },

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
    // Tüm faturaları getir (realtime)
    dinle: (callback) => {
        const faturaRef = ref(db, 'satis_faturalari');
        onValue(faturaRef, (snapshot) => {
            const data = snapshot.val();
            const faturalar = data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
            callback(faturalar);
        });
    },

    // Tek seferlik getir
    hepsiniGetir: async () => {
        const snapshot = await get(ref(db, 'satis_faturalari'));
        const data = snapshot.val();
        return data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
    },

    // Tek fatura getir
    getir: async (id) => {
        const snapshot = await get(ref(db, `satis_faturalari/${id}`));
        return snapshot.val() ? { id, ...snapshot.val() } : null;
    },

    // Yeni fatura ekle
    ekle: async (fatura) => {
        const yeniRef = push(ref(db, 'satis_faturalari'));
        await set(yeniRef, {
            ...fatura,
            olusturma_tarihi: new Date().toISOString(),
            guncelleme_tarihi: new Date().toISOString()
        });
        return yeniRef.key;
    },

    // Fatura güncelle
    guncelle: async (id, fatura) => {
        await update(ref(db, `satis_faturalari/${id}`), {
            ...fatura,
            guncelleme_tarihi: new Date().toISOString()
        });
    },

    // Fatura sil
    sil: async (id) => {
        await remove(ref(db, `satis_faturalari/${id}`));
    },

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
export const IadeFaturalari = {
    // Tüm faturaları getir (realtime)
    dinle: (callback) => {
        const faturaRef = ref(db, 'iade_faturalari');
        onValue(faturaRef, (snapshot) => {
            const data = snapshot.val();
            const faturalar = data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
            callback(faturalar);
        });
    },

    // Tek seferlik getir
    hepsiniGetir: async () => {
        const snapshot = await get(ref(db, 'iade_faturalari'));
        const data = snapshot.val();
        return data ? Object.entries(data).map(([id, val]) => ({ id, ...val })) : [];
    },

    // Tek fatura getir
    getir: async (id) => {
        const snapshot = await get(ref(db, `iade_faturalari/${id}`));
        return snapshot.val() ? { id, ...snapshot.val() } : null;
    },

    // Yeni fatura ekle
    ekle: async (fatura) => {
        const yeniRef = push(ref(db, 'iade_faturalari'));
        await set(yeniRef, {
            ...fatura,
            olusturma_tarihi: new Date().toISOString(),
            guncelleme_tarihi: new Date().toISOString()
        });
        return yeniRef.key;
    },

    // Fatura güncelle
    guncelle: async (id, fatura) => {
        await update(ref(db, `iade_faturalari/${id}`), {
            ...fatura,
            guncelleme_tarihi: new Date().toISOString()
        });
    },

    // Fatura sil
    sil: async (id) => {
        await remove(ref(db, `iade_faturalari/${id}`));
    }
};

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
            son_alis_faturalari: alis.slice(-5).reverse(),
            son_satis_faturalari: satis.slice(-5).reverse()
        };
    },

    // Realtime dinleme
    dinle: (callback) => {
        // Tüm koleksiyonları dinle
        const refs = ['alis_faturalari', 'satis_faturalari', 'iade_faturalari', 'musteriler', 'urunler'];
        refs.forEach(path => {
            onValue(ref(db, path), async () => {
                const stats = await Dashboard.istatistikler();
                callback(stats);
            });
        });
    }
};

// ==================== YARDIMCI FONKSİYONLAR ====================
export const Yardimci = {
    // Para formatla
    paraFormat: (tutar) => {
        return new Intl.NumberFormat('tr-TR', {
            style: 'currency',
            currency: 'TRY'
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
    }
};

// Global erişim için window'a ekle
window.FirebaseDB = {
    Musteriler,
    Urunler,
    AlisFaturalari,
    SatisFaturalari,
    IadeFaturalari,
    Dashboard,
    Yardimci
};

console.log('🔥 Firebase Realtime Database bağlantısı kuruldu!');
