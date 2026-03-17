#!/bin/bash
echo "================================================"
echo "   Space Coin Bot - O'rnatish"
echo "================================================"

# Python tekshirish
if ! command -v python3 &> /dev/null; then
    echo "Python3 topilmadi. O'rnatilmoqda..."
    sudo apt-get update -y
    sudo apt-get install python3 python3-pip -y
fi

echo "Python versiyasi: $(python3 --version)"

# Pip tekshirish
if ! command -v pip3 &> /dev/null; then
    echo "pip o'rnatilmoqda..."
    sudo apt-get install python3-pip -y
fi

# Kerakli paketlarni o'rnatish
echo ""
echo "Paketlar o'rnatilmoqda..."
pip3 install -r requirements.txt

# Papkalar yaratish
mkdir -p logs database

echo ""
echo "================================================"
echo "   O'rnatish tugadi!"
echo "   Botni ishga tushirish uchun:"
echo "   python3 bot.py"
echo "   Yoki: bash start.sh"
echo "================================================"
