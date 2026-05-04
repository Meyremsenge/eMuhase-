/**
 * Firebase Initialization - Güvenli Backend Config Yüklemesi
 * 
 * Firebase config'i backend'den dinamik olarak yüklenir.
 * Credentials GitHub'a commit edilmez, sadece .env'de tutulur.
 */

let firebaseConfig = null;
let firebaseInitialized = false;

/**
 * Backend'den Firebase config'i yükle
 */
async function initializeFirebase() {
    if (firebaseInitialized) return firebaseConfig;
    
    try {
        const response = await fetch('/api/config/firebase');
        
        if (!response.ok) {
            throw new Error(`Firebase config yüklenemedi: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.config) {
            console.warn('⚠️ Firebase yapılandırması yok. Demo modu kullanılıyor.');
            firebaseInitialized = true;
            return null;
        }
        
        firebaseConfig = data.config;
        firebaseInitialized = true;
        
        console.log('✅ Firebase config başarıyla yüklendi');
        return firebaseConfig;
        
    } catch (error) {
        console.error('❌ Firebase config yuerülkemedi:', error);
        console.log('💡 Demo modu (localStorage) kullanılacaktır');
        firebaseInitialized = true;
        return null;
    }
}

/**
 * Firebase ve Database'i başlat
 */
async function setupFirebase() {
    const config = await initializeFirebase();
    
    if (!config) {
        console.log('📝 Firebase devre dışı - localStorage modunda çalışılıyor');
        return null;
    }
    
    try {
        const { initializeApp } = await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-app.js');
        const { getDatabase } = await import('https://www.gstatic.com/firebasejs/11.0.0/firebase-database.js');
        
        const app = initializeApp(config);
        const db = getDatabase(app);
        
        return { app, db };
    } catch (error) {
        console.error('❌ Firebase SDK başlatma hatası:', error);
        return null;
    }
}

export { initializeFirebase, setupFirebase, firebaseConfig };
