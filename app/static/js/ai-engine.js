/**
 * eMuhasebe Pro - AI Engine
 * ============================================================
 * Üç bağımsız yapay zeka modülü:
 *  1. nakitAkisiTahmini  – Lineer regresyon + hareketli ortalama
 *  2. anomaliTespiti     – Z-score tabanlı anormallik tespiti
 *  3. akilliFaturaOneri  – Geçmiş faturalardan ürün/fiyat önerisi
 * ============================================================
 */

// ================================================================
// MODÜL 1 — NAKİT AKIŞI TAHMİNİ
// Girdiler: Satış ve alış fatura dizileri, kaç ay ileri tahmin
// Çıktı  : { gecmis: [...], tahminler: [...] }
// ================================================================
export function nakitAkisiTahmini(satisFaturalari, alisFaturalari, ayAdet = 3) {
    const now = new Date();

    // ---- Geriye dönük 6 aylık gerçek veriler ----
    const gecmis = [];
    for (let i = 5; i >= 0; i--) {
        const ay = new Date(now.getFullYear(), now.getMonth() - i, 1);

        const gelir = satisFaturalari
            .filter(f => {
                const d = new Date(f.tarih || f.olusturma_tarihi);
                return d.getMonth() === ay.getMonth() && d.getFullYear() === ay.getFullYear();
            })
            .reduce((s, f) => s + (parseFloat(f.toplam_tutar) || 0), 0);

        const gider = alisFaturalari
            .filter(f => {
                const d = new Date(f.tarih || f.olusturma_tarihi);
                return d.getMonth() === ay.getMonth() && d.getFullYear() === ay.getFullYear();
            })
            .reduce((s, f) => s + (parseFloat(f.toplam_tutar) || 0), 0);

        gecmis.push({ ay, gelir, gider, net: gelir - gider, tahmin: false });
    }

    // ---- Basit Lineer Regresyon ----
    function lineerRegresyon(values) {
        const n = values.length;
        if (n < 2) return { egim: 0, kesim: values[0] || 0 };

        const xOrt = (n - 1) / 2;
        const yOrt = values.reduce((a, b) => a + b, 0) / n;
        let sayac = 0, payda = 0;
        values.forEach((y, x) => {
            sayac += (x - xOrt) * (y - yOrt);
            payda += (x - xOrt) ** 2;
        });
        const egim = payda !== 0 ? sayac / payda : 0;
        return { egim, kesim: yOrt - egim * xOrt };
    }

    const gelirler = gecmis.map(v => v.gelir);
    const giderler = gecmis.map(v => v.gider);
    const gelirReg = lineerRegresyon(gelirler);
    const giderReg = lineerRegresyon(giderler);

    // ---- Gelecek ayları tahmin et ----
    const tahminler = [];
    for (let i = 1; i <= ayAdet; i++) {
        const x = gelirler.length - 1 + i;
        const tahminAy = new Date(now.getFullYear(), now.getMonth() + i, 1);

        // Son 3 ayın hareketli ortalaması
        const son3Gelir = gelirler.slice(-3);
        const son3Gider = giderler.slice(-3);
        const hoGelir = son3Gelir.reduce((a, b) => a + b, 0) / son3Gelir.length;
        const hoGider = son3Gider.reduce((a, b) => a + b, 0) / son3Gider.length;

        // %60 hareketli ortalama + %40 regresyon (denge)
        const regGelir = gelirReg.kesim + gelirReg.egim * x;
        const regGider = giderReg.kesim + giderReg.egim * x;
        const tahminGelir = Math.max(0, hoGelir * 0.6 + regGelir * 0.4);
        const tahminGider = Math.max(0, hoGider * 0.6 + regGider * 0.4);

        tahminler.push({
            ay: tahminAy,
            gelir: Math.round(tahminGelir),
            gider: Math.round(tahminGider),
            net: Math.round(tahminGelir - tahminGider),
            tahmin: true
        });
    }

    return { gecmis, tahminler };
}

// ================================================================
// MODÜL 2 — ANOMALİ TESPİTİ
// Girdiler: Fatura dizisi, z-score eşiği (varsayılan 2.5)
// Çıktı  : Anomali olan faturalar (z-score bilgisiyle)
// ================================================================
export function anomaliTespiti(faturalar, esik = 2.5) {
    if (faturalar.length < 3) return [];

    const tutarlar = faturalar
        .map(f => parseFloat(f.toplam_tutar) || 0)
        .filter(t => t > 0);

    if (tutarlar.length < 3) return [];

    const ort = tutarlar.reduce((a, b) => a + b, 0) / tutarlar.length;
    const varyans = tutarlar.reduce((a, b) => a + (b - ort) ** 2, 0) / tutarlar.length;
    const stdSapma = Math.sqrt(varyans);

    if (stdSapma === 0) return [];

    return faturalar
        .filter(f => {
            const tutar = parseFloat(f.toplam_tutar) || 0;
            return tutar > 0 && Math.abs((tutar - ort) / stdSapma) > esik;
        })
        .map(f => {
            const tutar = parseFloat(f.toplam_tutar) || 0;
            const z = (tutar - ort) / stdSapma;
            return {
                ...f,
                z_skoru: Math.abs(z).toFixed(2),
                seviye: Math.abs(z) > 3.5 ? 'kritik' : 'uyari',
                sapma_yonu: tutar > ort ? 'yüksek' : 'düşük'
            };
        });
}

// ================================================================
// MODÜL 3 — AKILLI FATURA ÖNERİ
// Girdiler: Geçmiş satış faturaları, kullanıcının yazdığı metin
// Çıktı  : En sık kullanılan ürün/hizmet listesi (fiyat + KDV ile)
// ================================================================
export function akilliFaturaOneri(satisFaturalari, aramaMetni = '') {
    const sayac = {};

    satisFaturalari.forEach(fatura => {
        const kalemler = fatura.kalemler || fatura.urunler || [];
        kalemler.forEach(kalem => {
            const ad = (kalem.urun_adi || kalem.ad || kalem.aciklama || '').trim();
            if (!ad) return;

            if (!sayac[ad]) {
                sayac[ad] = { ad, sayi: 0, fiyatlar: [], kdvOranlari: [], toplamCiro: 0 };
            }

            sayac[ad].sayi++;
            const fiyat = parseFloat(kalem.birim_fiyat) || 0;
            const tutar = parseFloat(kalem.toplam) || parseFloat(kalem.tutar) || 0;
            if (fiyat > 0) sayac[ad].fiyatlar.push(fiyat);
            if (tutar > 0) sayac[ad].toplamCiro += tutar;
            if (kalem.kdv_orani) sayac[ad].kdvOranlari.push(parseInt(kalem.kdv_orani));
        });
    });

    const oneriler = Object.values(sayac).map(u => {
        const ortFiyat = u.fiyatlar.length > 0
            ? u.fiyatlar.reduce((a, b) => a + b, 0) / u.fiyatlar.length
            : 0;
        const ortKdv = u.kdvOranlari.length > 0
            ? Math.round(u.kdvOranlari.reduce((a, b) => a + b, 0) / u.kdvOranlari.length)
            : 20;
        return {
            ad: u.ad,
            kullanim: u.sayi,
            ort_fiyat: Math.round(ortFiyat * 100) / 100,
            ciro: u.toplamCiro,
            kdv: ortKdv
        };
    });

    const filtre = aramaMetni.length >= 2
        ? oneriler.filter(o => o.ad.toLowerCase().includes(aramaMetni.toLowerCase()))
        : oneriler;

    return filtre.sort((a, b) => b.kullanim - a.kullanim).slice(0, 8);
}
