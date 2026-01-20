# 🛡️ AeroStat: Endüstriyel IoT Güvenlik ve Otonom Yaşam Destek Sistemi

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![ESP8266](https://img.shields.io/badge/Donanım-NodeMCU-lightgrey?style=for-the-badge&logo=arduino)
![InfluxDB](https://img.shields.io/badge/Veritabanı-InfluxDB-28B766?style=for-the-badge&logo=influxdb)
![Telegram](https://img.shields.io/badge/API-Telegram_Bot-24A1DE?style=for-the-badge&logo=telegram)
![License](https://img.shields.io/badge/Lisans-MIT-green.svg)

**AeroStat**, basit bir sensör okuma projesinin ötesinde; otonom karar verme yeteneğine sahip, hata toleranslı (fault-tolerant) ve acil durum protokolleri içeren uçtan uca (end-to-end) bir **IoT Güvenlik Sistemidir.**

Gömülü sistemleri modern bulut teknolojileriyle birleştiren bu proje, ortam verilerini sadece kaydetmekle kalmaz; **analiz eder, yorumlar ve hayati tehlike durumlarında inisiyatif alarak acil müdahale süreçlerini (112 Arama vb.) başlatır.**

---

## 🏗️ Sistem Mimarisi

Sistem, **Edge Computing** (Uçta İşleme) prensibiyle çalışır. Sensör verisi ham olarak alınmaz, filtrelenir, işlenir ve anlamlı bilgiye dönüştürülerek kullanıcıya sunulur.

```mermaid
graph LR
    A[DHT22 Sensör] -->|Ham Veri| B(NodeMCU ESP8266)
    B -->|Serial/USB| C{Python Gateway}
    C -->|Zaman Serisi| D[(InfluxDB)]
    C -->|Çift Yönlü| E[Telegram Bot API]
    C -->|Otonom Karar| F[Röle/Fan Kontrolü]