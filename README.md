# 🤖 MikroTik NetOps Bot Telegram

Sebuah bot Telegram berbasis Python untuk mengelola dan memonitor konfigurasi MikroTik RouterOS secara interaktif. Dikembangkan untuk mempermudah tugas *Network Engineer* dalam melakukan konfigurasi *Firewall, NAT, Mangle,* dan *Address List* langsung dari genggaman tanpa harus membuka Winbox.

Proyek ini adalah bagian dari inisiatif eksplorasi otomatisasi jaringan oleh **Ngoprek Jaringan**.

---

## ✨ Fitur Utama

Bot ini menggunakan sistem **Inline Keyboard** dan **State Machine** untuk alur kerja yang rapi dan terstruktur:

* 🛡️ **Firewall Filter:** * **Template Cepat:** Eksekusi mitigasi instan seperti *Drop Invalid Packets* atau *Block Ping/ICMP*.
    * **Custom Rule:** Pembuatan *rule* bertahap (*Chain, Action, IP Target, Protocol & Port*).
* 🌐 **NAT (Network Address Translation):**
    * Setup *Masquerade (SrcNAT)* dengan mudah.
    * Setup *Port Forwarding (DstNAT)* yang presisi.
* 🔀 **Mangle:**
    * Konfigurasi *Mark Connection, Mark Packet,* dan *Mark Routing* secara interaktif sesuai *Chain* (*Prerouting, Forward, Postrouting*).
* 📋 **Address List:**
    * Menarik data *Address List* yang sudah ada (*existing*) di router secara *real-time*.
    * Menambahkan IP baru ke *list* yang sudah ada atau membuat *list* baru.

---

## 🛠️ Persyaratan Sistem

Sebelum menjalankan bot ini, pastikan Anda memiliki:
1. **Python 3.7+** terinstal di PC/Server/VPS Anda.
2. **MikroTik RouterOS** (Telah dites dan direkomendasikan untuk RouterOS v7) dengan layanan API yang sudah diaktifkan.
3. **Telegram Bot Token** yang didapatkan dari [@BotFather](https://t.me/botfather).
4. **Chat ID Telegram** Anda sebagai Admin (untuk keamanan).

---

## 🚀 Instalasi & Konfigurasi

### 1. Kloning Repositori
```bash
git clone https://github.com/aleaengineer/MikroTik-NetOps-Bot-Telegram/
cd MikroTik-NetOps-Bot-Telegram
```

### 2. Instalasi Dependensi (Library)
Bot ini menggunakan library `pyTelegramBotAPI` untuk *handling* Telegram dan `RouterOS-api` untuk komunikasi dengan MikroTik.
```bash
pip install pyTelegramBotAPI RouterOS-api
```

### 3. Aktifkan API di MikroTik
Buka terminal MikroTik (via Winbox/SSH) dan jalankan perintah berikut:
```routeros
/ip service enable api
```
*(Direkomendasikan: Buat user khusus di MikroTik hanya untuk bot ini dengan kredensial yang kuat).*

### 4. Konfigurasi Script
Buka file `main.py` menggunakan teks editor pilihan Anda dan ubah variabel berikut dengan data riil Anda:

```python
# --- KONFIGURASI ---
TELEGRAM_TOKEN = 'MASUKKAN_TOKEN_BOT_ANDA'
ADMIN_CHAT_ID = 123456789  # Chat ID Telegram Anda (Sangat penting!)

MIKROTIK_IP = '10.10.10.1'
MIKROTIK_USER = 'user_bot'
MIKROTIK_PASS = 'password_bot'
# -------------------
```

### 5. Jalankan Bot
```bash
python bot_mikrotik.py
```

---

## 🎮 Cara Penggunaan

1. Buka aplikasi Telegram dan cari bot Anda.
2. Ketik perintah `/start` atau `/menu`.
3. Bot akan memunculkan **Panel Kontrol MikroTik** berbasis tombol (Inline Keyboard).
4. Klik salah satu menu (Misal: *Address List*) dan ikuti instruksi yang diberikan oleh bot.
5. Bot secara otomatis akan mengamankan eksekusi dengan memvalidasi `ADMIN_CHAT_ID`. Orang lain yang menemukan bot ini tidak akan bisa menekan tombol atau menjalankan perintah apa pun.

---

## 👨‍💻 Penulis

* **Aleaengineer** - *NOC Engineer* | [farhanale.my.id](https://farhanale.my.id/)

## 📜 Lisensi

Proyek ini menggunakan lisensi MIT. Silakan dimodifikasi dan dikembangkan lebih lanjut sesuai kebutuhan operasional jaringan Anda.
