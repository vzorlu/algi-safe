#!/bin/bash

# Kullanıcı bilgileri ve hedef sunucu
SSH_USER="$(whoami)"
TARGET_IP="$(hostname -I | awk '{print $1}')"
POST_URL_REGISTER="http://127.0.0.1:8000//api/register_device/"
POST_URL_DATA="http://127.0.0.1:8000/api/post_device_data/"


# Lisans anahtarını kullanıcıdan al
read -p "Lisans anahtarını girin: " LICENSE_KEY

# Cihaz bilgilerini al (MacOS için MAC adresi)
MAC_ADDRESS="$(ifconfig en0 | grep ether | awk '{print $2}')"

# Cihazı MAC adresiyle sorgulamak için JSON verisi oluştur
GET_DEVICE_JSON=$(cat <<EOF
{
  "mac_address": "$MAC_ADDRESS"
}
EOF
)

# Cihazı sorgulama isteği yap
GET_DEVICE_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$GET_DEVICE_JSON" $POST_URL_GET_DEVICE)

# Cihaz ID'sini sorgulama yanıtından al
DEVICE_ID=$(echo "$GET_DEVICE_RESPONSE" | grep -o '"device_id":[^,]*' | cut -d':' -f2 | tr -d '"' | tr -d ' ')

# Eğer cihaz ID'si alınamadıysa, işlemi durdur
if [ -z "$DEVICE_ID" ]; then
  echo "Cihaz ID'si alınamadı, lütfen cihazın kayıtlı olduğundan emin olun."
  exit 1
fi

# CPU kullanımı (macOS'ta `ps` komutuyla alınır)
CPU_USAGE=$(ps -A -o %cpu | awk '{s+=$1} END {print s}')

# Bellek kullanımı (macOS'ta `vm_stat` komutuyla hesaplanır)
MEMORY_USAGE=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
MEMORY_TOTAL=$(sysctl hw.memsize | awk '{print $2}')
MEMORY_USAGE=$(echo "scale=2; ($MEMORY_USAGE * 4096) / $MEMORY_TOTAL * 100" | bc)

# Disk kullanımını al
DISK_SPACE="$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')"

# JSON veri oluştur (cihaz verilerini göndermek için)
DATA_JSON=$(cat <<EOF
{
  "mac_address": "$MAC_ADDRESS",
  "license_key": "$LICENSE_KEY",
  "cpu_usage": "$CPU_USAGE",
  "memory_usage": "$MEMORY_USAGE",
  "disk_space": "$DISK_SPACE",
  "device": "$DEVICE_ID"
}
EOF
)

# Gönderilen JSON veriyi ekrana yazdır (debugging için)
echo "Gönderilen JSON veri: $DATA_JSON"

# Verileri HTTP POST isteği ile gönder
RESPONSE=$(curl -s -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$DATA_JSON" $POST_URL_DATA)

# Sunucudan alınan HTTP yanıt kodu ve gönderilen JSON veriyi yazdır
echo "Sunucudan alınan HTTP yanıt kodu: $RESPONSE"

# Sonuçları kontrol et
if [ "$RESPONSE" -eq 200 ]; then
  echo "Veri başarıyla gönderildi!"
else
  echo "Veri gönderimi başarısız oldu, HTTP kodu: $RESPONSE"
fi
