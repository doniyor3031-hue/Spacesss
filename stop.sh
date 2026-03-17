#!/bin/bash
if [ -f bot.pid ]; then
    PID=$(cat bot.pid)
    kill $PID 2>/dev/null
    rm bot.pid
    echo "Bot to'xtatildi (PID: $PID)"
else
    echo "Bot ishlamayapti yoki PID fayli topilmadi."
    pkill -f "python3 bot.py" && echo "Bot to'xtatildi." || echo "Bot topilmadi."
fi
