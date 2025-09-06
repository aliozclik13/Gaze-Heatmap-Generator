# **Web Tabanlı Göz Takibi ile Dinamik Dikkat Haritası Üretimi**

Bu proje, standart bir web kamerası kullanarak dinamik video uyaranları karşısında katılımcıların göz takip verilerini toplayan ve bu verilerden kolektif dikkat haritaları (saliency maps) üreten, baştan sona bütünleşik bir sistemdir. Araştırma, özel donanım gerektirmeyen, erişilebilir ve ölçeklenebilir bir metodoloji sunmayı amaçlamaktadır.

Bu depo, başlıklı bilimsel çalışmada kullanılan yazılımın kaynak kodunu içermektedir.

### **✨ Temel Özellikler**

* **Web Tabanlı Veri Toplama:** Katılımcıların deneye herhangi bir modern web tarayıcısı üzerinden katılabilmesi.  
* **Donanım Bağımsız:** Sadece standart bir web kamerası gerektirir.  
* **Etkileşimli Kalibrasyon ve Doğrulama:** Yüksek veri doğruluğu için GazeRecorder'dan esinlenilmiş, tıklama tabanlı kalibrasyon ve nicel doğrulama adımları.  
* **Otomatik Test Yönetimi:** Her katılımcı ve test seansı için verileri otomatik olarak organize eder ve üzerine yazmayı engeller.  
* **Dinamik Heatmap Üretimi:** Toplanan kolektif verilerden, video üzerine işlenmiş, zamanla değişen dikkat haritaları oluşturur.  
* **Çoklu Test Desteği:** Farklı test gruplarının (test1, test2 vb.) sonuçlarını ayrı ayrı işler ve karşılaştırmaya olanak tanır.

### **📂 Proje Yapısı**

.  
├── static/  
│   ├── webgazer.js     \# Göz takip kütüphanesi  
│   └── video.mp4       \# Deneyde kullanılacak örnek video  
├── templates/  
│   └── index.html      \# Katılımcının gördüğü web arayüzü  
├── app.py              \# Veri toplama sunucusu (Flask)  
├── process\_gaze.py     \# Veri işleme ve heatmap üretme script'i  
├── requirements.txt    \# Gerekli Python kütüphaneleri  
└── README.md           \# Bu dosya

### **🚀 Kurulum ve Kullanım**

Bu projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin.

#### **1\. Ön Gereksinimler**

* [Python 3.9](https://www.python.org/downloads/) veya daha üstü  
* [Git](https://git-scm.com/downloads/)

#### **2\. Kurulum**

\# 1\. Proje deposunu klonlayın  
git clone \[https://github.com/senin-kullanici-adin/Gaze-Heatmap-Generator.git\](https://github.com/senin-kullanici-adin/Gaze-Heatmap-Generator.git)  
cd Gaze-Heatmap-Generator

\# 2\. Bir sanal ortam oluşturup aktive edin (Önerilir)  
python \-m venv venv  
\# Windows için:  
venv\\Scripts\\activate  
\# macOS/Linux için:  
source venv/bin/activate

\# 3\. Gerekli Python kütüphanelerini yükleyin  
pip install \-r requirements.txt

#### **3\. Kullanım**

Proje iki ana aşamadan oluşur: Veri Toplama ve Veri İşleme.

**Aşama 1: Veri Toplama**

1. Deneyde kullanacağınız videoyu static/video.mp4 olarak kaydedin.  
2. Aşağıdaki komutla veri toplama sunucusunu başlatın:  
   python app.py

3. Bir web tarayıcısı açın ve http://127.0.0.1:5000 adresine gidin.  
4. Katılımcı ID'si belirlemek için URL'ye parametre ekleyebilirsiniz, örneğin: http://127.0.0.1:5000/?pid=ali  
5. Arayüzdeki talimatları izleyerek deneyi tamamlayın. Toplanan veriler, proje ana dizininde otomatik olarak oluşturulan data/ klasörüne kaydedilecektir.

**Aşama 2: Veri İşleme ve Heatmap Üretimi**

1. Veri toplama işlemi bittikten sonra, aşağıdaki komutu çalıştırarak dikkat haritası videosunu oluşturun:  
   python process\_gaze.py

2. Script, data/ klasöründeki tüm test gruplarını otomatik olarak bulacak ve her biri için ayrı bir video üretecektir.  
3. Sonuç videoları, proje ana dizininde otomatik olarak oluşturulan results/ klasörüne heatmap\_video\_test1.mp4, heatmap\_video\_test2.mp4 vb. isimlerle kaydedilecektir.

### **📄 Atıf (Citation)**

Bu çalışmayı kendi araştırmanızda kullanırsanız, lütfen aşağıdaki makalemize atıfta bulunun:

\[MAKALE KÜNYESİ BURAYA GELECEK: Yazar(lar), "Makale Başlığı", Yayın Adı, Cilt, Sayı, Sayfa Numaraları, Yıl.\]

### **⚖️ Lisans**

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için LICENSE dosyasına bakınız.