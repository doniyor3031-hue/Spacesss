#!/bin/bash
echo "Space Coin Bot fonda ishga tushirilmoqda..."
mkdir -p logs database
nohup python3 bot.py > logs/console.log 2>&1 &
echo "Bot PID: $!"
echo "PID fayli saqlandi: bot.pid"
echo $! > bot.pid
echo ""
echo "To'xtatish uchun: bash stop.sh"
echo "Loglarni ko'rish uchun: tail -f logs/bot.log"
