#!/usr/bin/env bash
set -e

echo "=== Запуск автотестов iqData Bot ==="

# Функция проверки HTTP статуса
check_status() {
    local url=\$1
    local expected_code=\$2
    local test_name=\$3
    
    # Получаем код ответа
    local code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    # Проверка на успешность curl и совпадение кода
    if [ "$code" -eq "$expected_code" ] 2>/dev/null; then
        echo "✅ PASS: $test_name (HTTP $code)"
        return 0
    else
        echo "❌ FAIL: $test_name (Expected $expected_code, got \$code)"
        return 1
    fi
}

# 1. Проверка Health
check_status "http://localhost:8000/health" 200 "Health Check"

# 2. Проверка UI (HTML)
HTML_CHECK=\$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/")
if [ "\$HTML_CHECK" -eq 200 ]; then
    echo "✅ PASS: UI доступен"
else
    echo "❌ FAIL: UI недоступен (HTTP \$HTML_CHECK)"
    exit 1
fi

# 3. Проверка списка файлов (должен вернуть пустой JSON список)
check_status "http://localhost:8000/files" 200 "Files List API"

# 4. Тест загрузки файла
echo "📥 Тестирование загрузки файла..."
# Создаем временный тестовый файл прямо в текущей папке проекта, чтобы curl мог его найти
echo "test content for upload" > ./test_upload.txt

# Используем form-data для загрузки
UPLOAD_RESPONSE=\$(curl -s -F "file=@./test_upload.txt" -F "task_type=analyze" http://localhost:8000/upload)

# Проверяем, что в ответе есть признаки успеха (status или analysis)
if echo "$UPLOAD_RESPONSE" | grep -q '"status": "success"' || echo "$UPLOAD_RESPONSE" | grep -q '"analysis"'; then
    echo "✅ PASS: Загрузка и анализ файла"
else
    echo "❌ FAIL: Загрузка файла не удалась"
    echo "Response: \$UPLOAD_RESPONSE"
    rm ./test_upload.txt
    exit 1
fi

# 5. Тест эмбеддинга
echo "🧠 Тестирование эмбеддинга..."
echo "test content for embed" > ./test_embed.txt
EMBED_RESPONSE=\$(curl -s -F "file=@./test_embed.txt" -F "task_type=embed" http://localhost:8000/upload)

if echo "\$EMBED_RESPONSE" | grep -q '"embedding_length"'; then
    echo "✅ PASS: Эмбеддинг работает"
else
    echo "❌ FAIL: Эмбеддинг не работает"
    echo "Response: \$EMBED_RESPONSE"
    rm ./test_upload.txt ./test_embed.txt
    exit 1
fi

# 6. Тест диалога
echo "💬 Тестирование чата..."
CHAT_RESPONSE=\$(curl -s -d "prompt=Hello, are you ready?" http://localhost:8000/chat)

if echo "\$CHAT_RESPONSE" | grep -q '"response"'; then
    echo "✅ PASS: Чат работает"
else
    echo "❌ FAIL: Чат не работает"
    echo "Response: \$CHAT_RESPONSE"
    rm ./test_upload.txt ./test_embed.txt
    exit 1
fi

# 7. Финальная уборка
rm ./test_upload.txt ./test_embed.txt

echo "=== Все тесты пройдены! 🎉 ==="
