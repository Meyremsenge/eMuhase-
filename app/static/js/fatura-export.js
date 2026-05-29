/**
 * eMuhasebe Pro — Fatura Dışa Aktarma Modülü
 *
 * Sağlanan fonksiyonlar:
 *   - faturaPdfIndir(fatura, opts)  → jsPDF ile PDF üretip indirir
 *   - faturaXmlIndir(fatura, opts)  → UBL-TR uyumlu XML üretip indirir
 *     (e-Fatura mesaj formatına benzer; gerçek GIB gönderimi için imza
 *      ve özel paketleme gerekir — bu çıktı muhasebe entegrasyonları için.)
 *
 * jsPDF CDN'i sayfada yüklü olmalı:
 *   <script src="https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js"></script>
 *   <script src="https://cdn.jsdelivr.net/npm/jspdf-autotable@3.8.2/dist/jspdf.plugin.autotable.min.js"></script>
 */

function paraFormat(tutar) {
    return new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(tutar || 0);
}

function tarihFormat(t) {
    return t ? new Date(t).toLocaleDateString('tr-TR') : '-';
}

function escapeXml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');
}

function kalemleriDuzgunListeyeCevir(fatura) {
    const raw = fatura.kalemler || fatura.urunler || [];
    if (Array.isArray(raw)) return raw;
    return Object.values(raw);
}

// ── PDF için Türkçe (Unicode) font ──
// jsPDF'in varsayılan Helvetica fontu Türkçe karakterleri (ş, ı, ğ, ö, ü, ç)
// göstermez → "Taşımacılık" yerine "Ta_1mac1l1k" çıkar. DejaVuSans TTF'i CDN'den
// çekip gömüyoruz; bir kez yüklenince window üzerinde önbelleğe alınır.
let _pdfFontCache = null;

function _arrayBufferToBase64(buf) {
    let binary = '';
    const bytes = new Uint8Array(buf);
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
        binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return btoa(binary);
}

async function _turkceFontYukle() {
    if (_pdfFontCache) return _pdfFontCache;
    if (window._emuPdfFont) { _pdfFontCache = window._emuPdfFont; return _pdfFontCache; }
    const base = 'https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/';
    const [reg, bold] = await Promise.all([
        fetch(base + 'DejaVuSans.ttf').then(r => r.arrayBuffer()),
        fetch(base + 'DejaVuSans-Bold.ttf').then(r => r.arrayBuffer()),
    ]);
    _pdfFontCache = {
        normal: _arrayBufferToBase64(reg),
        bold: _arrayBufferToBase64(bold),
    };
    window._emuPdfFont = _pdfFontCache; // sonraki PDF'ler için önbellek
    return _pdfFontCache;
}

// ═══════════════════════════════════════════════════════════════════
// PDF İNDİR
// ═══════════════════════════════════════════════════════════════════
export async function faturaPdfIndir(fatura, opts = {}) {
    if (typeof window.jspdf === 'undefined') {
        throw new Error('jsPDF yüklü değil. Sayfaya jsPDF CDN ekle.');
    }
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: 'mm', format: 'a4' });

    // Türkçe karakterler için Unicode font göm; yüklenemezse helvetica'ya düş.
    let FONT = 'helvetica';
    try {
        const f = await _turkceFontYukle();
        doc.addFileToVFS('DejaVuSans.ttf', f.normal);
        doc.addFont('DejaVuSans.ttf', 'DejaVuSans', 'normal');
        doc.addFileToVFS('DejaVuSans-Bold.ttf', f.bold);
        doc.addFont('DejaVuSans-Bold.ttf', 'DejaVuSans', 'bold');
        FONT = 'DejaVuSans';
    } catch (e) {
        console.warn('PDF Türkçe font yüklenemedi, helvetica kullanılacak:', e);
    }

    const baslik       = opts.baslik       || 'FATURA';
    const cariEtiket   = opts.cariEtiket   || 'Müşteri / Tedarikçi';
    const cariAdi      = opts.cariAdi      || fatura.musteri_adi || fatura.tedarikci_adi || fatura.cari_adi || '-';
    const firmaAdi     = opts.firmaAdi     || 'eMuhasebe Pro';
    const accentColor  = opts.accentColor  || [51, 65, 85]; // slate-700

    // Üst başlık şeridi
    doc.setFillColor(accentColor[0], accentColor[1], accentColor[2]);
    doc.rect(0, 0, 210, 22, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFont(FONT, 'bold');
    doc.setFontSize(18);
    doc.text(firmaAdi, 14, 14);
    doc.setFontSize(11);
    doc.text(baslik, 196, 14, { align: 'right' });

    // Fatura meta
    doc.setTextColor(15, 23, 42);
    doc.setFont(FONT, 'normal');
    doc.setFontSize(10);
    let y = 32;
    const metaSatirlari = [
        ['Fatura No',     fatura.fatura_no || '-'],
        ['Fatura Tarihi', tarihFormat(fatura.fatura_tarihi)],
        ['Vade Tarihi',   tarihFormat(fatura.vade_tarihi)],
        [cariEtiket,      cariAdi],
        ['Durum',         (fatura.durum || '-').toUpperCase()],
    ];
    metaSatirlari.forEach(([k, v]) => {
        doc.setFont(FONT, 'bold');
        doc.text(k + ':', 14, y);
        doc.setFont(FONT, 'normal');
        doc.text(String(v), 60, y);
        y += 6;
    });

    if (fatura.aciklama) {
        y += 2;
        doc.setFont(FONT, 'bold');
        doc.text('Açıklama:', 14, y);
        doc.setFont(FONT, 'normal');
        const aciklamaLines = doc.splitTextToSize(fatura.aciklama, 130);
        doc.text(aciklamaLines, 60, y);
        y += aciklamaLines.length * 5;
    }

    // Kalemler tablosu (jsPDF-AutoTable)
    const kalemler = kalemleriDuzgunListeyeCevir(fatura);
    const head = [['#', 'Ürün / Açıklama', 'Miktar', 'Birim Fiyat', 'KDV %', 'KDV Tutar', 'Toplam']];
    const body = kalemler.map((k, i) => {
        const ad   = k.urun_adi || k.aciklama || '-';
        const m    = parseFloat(k.miktar) || 0;
        const bf   = parseFloat(k.birim_fiyat) || 0;
        const ko   = parseInt(k.kdv_orani) || 0;
        const tut  = parseFloat(k.toplam) || (m * bf);
        const kdvT = parseFloat(k.kdv_tutar ?? k.kdv_tutari) || (tut * ko / 100);
        const gt   = parseFloat(k.genel_toplam) || (tut + kdvT);
        return [
            String(i + 1),
            ad,
            String(m),
            paraFormat(bf) + ' TL',
            '%' + ko,
            paraFormat(kdvT) + ' TL',
            paraFormat(gt) + ' TL',
        ];
    });

    if (doc.autoTable) {
        doc.autoTable({
            head, body,
            startY: y + 4,
            theme: 'striped',
            headStyles: { fillColor: accentColor, textColor: 255, fontStyle: 'bold', font: FONT },
            styles: { fontSize: 9, cellPadding: 2.5, font: FONT },
            columnStyles: {
                0: { halign: 'center', cellWidth: 8 },
                2: { halign: 'right' },
                3: { halign: 'right' },
                4: { halign: 'center' },
                5: { halign: 'right' },
                6: { halign: 'right', fontStyle: 'bold' },
            },
            margin: { left: 14, right: 14 },
        });
        y = doc.lastAutoTable.finalY + 4;
    } else {
        // jsPDF-AutoTable yoksa basit listele
        doc.setFontSize(9);
        body.forEach(row => {
            doc.text(row.join(' | '), 14, y);
            y += 5;
        });
    }

    // Toplam kutusu
    const araT = parseFloat(fatura.ara_toplam) || 0;
    const kdvT = parseFloat(fatura.kdv_toplam) || 0;
    const genT = parseFloat(fatura.genel_toplam) || (araT + kdvT);
    const totBoxX = 130;
    doc.setDrawColor(...accentColor);
    doc.setLineWidth(0.4);
    doc.rect(totBoxX, y, 66, 26);
    doc.setFontSize(10);
    doc.setFont(FONT, 'normal');
    doc.text('Ara Toplam:', totBoxX + 3, y + 7);
    doc.text(paraFormat(araT) + ' TL', 194, y + 7, { align: 'right' });
    doc.text('KDV Toplam:', totBoxX + 3, y + 14);
    doc.text(paraFormat(kdvT) + ' TL', 194, y + 14, { align: 'right' });
    doc.setFont(FONT, 'bold');
    doc.setFontSize(11);
    doc.text('Genel Toplam:', totBoxX + 3, y + 22);
    doc.text(paraFormat(genT) + ' TL', 194, y + 22, { align: 'right' });

    // Footer
    doc.setFontSize(8);
    doc.setFont(FONT, 'normal');
    doc.setTextColor(100, 116, 139);
    const now = new Date().toLocaleString('tr-TR');
    doc.text(`eMuhasebe Pro tarafından ${now} oluşturuldu.`, 14, 290);

    const fileName = `${baslik.replace(/\s+/g, '_')}_${fatura.fatura_no || 'fatura'}.pdf`;
    doc.save(fileName);
}

// ═══════════════════════════════════════════════════════════════════
// e-FATURA XML İNDİR  (UBL-TR benzeri; entegrasyon için)
// ═══════════════════════════════════════════════════════════════════
export function faturaXmlIndir(fatura, opts = {}) {
    const cariAdi    = opts.cariAdi    || fatura.musteri_adi || fatura.tedarikci_adi || fatura.cari_adi || '-';
    const profile    = opts.profile    || 'TICARIFATURA';
    const faturaTipi = opts.faturaTipi || 'SATIS';
    const para       = opts.paraBirimi || 'TRY';
    const docId      = fatura.fatura_no || ('FTR-' + Date.now());

    const kalemler = kalemleriDuzgunListeyeCevir(fatura);
    const araToplam = parseFloat(fatura.ara_toplam) || kalemler.reduce((s, k) => {
        const m = parseFloat(k.miktar) || 0;
        const bf = parseFloat(k.birim_fiyat) || 0;
        return s + (parseFloat(k.toplam) || m * bf);
    }, 0);
    const kdvToplam = parseFloat(fatura.kdv_toplam) || 0;
    const genelToplam = parseFloat(fatura.genel_toplam) || (araToplam + kdvToplam);

    const linesXml = kalemler.map((k, i) => {
        const m   = parseFloat(k.miktar) || 0;
        const bf  = parseFloat(k.birim_fiyat) || 0;
        const ko  = parseInt(k.kdv_orani) || 0;
        const tut = parseFloat(k.toplam) || (m * bf);
        const kdv = parseFloat(k.kdv_tutar ?? k.kdv_tutari) || (tut * ko / 100);
        const ad  = k.urun_adi || k.aciklama || 'Kalem';
        const birim = k.birim || 'NIU';
        return `    <cac:InvoiceLine>
      <cbc:ID>${i + 1}</cbc:ID>
      <cbc:InvoicedQuantity unitCode="${escapeXml(birim)}">${m}</cbc:InvoicedQuantity>
      <cbc:LineExtensionAmount currencyID="${para}">${tut.toFixed(2)}</cbc:LineExtensionAmount>
      <cac:TaxTotal>
        <cbc:TaxAmount currencyID="${para}">${kdv.toFixed(2)}</cbc:TaxAmount>
        <cac:TaxSubtotal>
          <cbc:TaxableAmount currencyID="${para}">${tut.toFixed(2)}</cbc:TaxableAmount>
          <cbc:TaxAmount currencyID="${para}">${kdv.toFixed(2)}</cbc:TaxAmount>
          <cbc:Percent>${ko}</cbc:Percent>
          <cac:TaxCategory>
            <cac:TaxScheme><cbc:Name>KDV</cbc:Name><cbc:TaxTypeCode>0015</cbc:TaxTypeCode></cac:TaxScheme>
          </cac:TaxCategory>
        </cac:TaxSubtotal>
      </cac:TaxTotal>
      <cac:Item><cbc:Name>${escapeXml(ad)}</cbc:Name></cac:Item>
      <cac:Price><cbc:PriceAmount currencyID="${para}">${bf.toFixed(4)}</cbc:PriceAmount></cac:Price>
    </cac:InvoiceLine>`;
    }).join('\n');

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
  <cbc:CustomizationID>TR1.2</cbc:CustomizationID>
  <cbc:ProfileID>${escapeXml(profile)}</cbc:ProfileID>
  <cbc:ID>${escapeXml(docId)}</cbc:ID>
  <cbc:IssueDate>${(fatura.fatura_tarihi || '').slice(0, 10)}</cbc:IssueDate>
  <cbc:InvoiceTypeCode>${escapeXml(faturaTipi)}</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>${para}</cbc:DocumentCurrencyCode>
  <cbc:Note>${escapeXml(fatura.aciklama || '')}</cbc:Note>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cac:PartyName><cbc:Name>${escapeXml(cariAdi)}</cbc:Name></cac:PartyName>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="${para}">${araToplam.toFixed(2)}</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="${para}">${araToplam.toFixed(2)}</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="${para}">${genelToplam.toFixed(2)}</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="${para}">${genelToplam.toFixed(2)}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="${para}">${kdvToplam.toFixed(2)}</cbc:TaxAmount>
  </cac:TaxTotal>
${linesXml}
</Invoice>
`;

    const blob = new Blob([xml], { type: 'application/xml;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `eFatura_${docId}.xml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
