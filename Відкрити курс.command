#!/bin/bash
# Подвійний клік — сайт курсу відкриється у браузері.
# Інтернет не потрібен: сервер локальний, усі схеми, шрифти й формули лежать поруч.
# Щоб зупинити — закрийте це вікно Терміналу або натисніть Ctrl+C.

cd "$(dirname "$0")" || exit 1
export npm_config_cache="$HOME/.npm-cache-course"
PORT=4173

echo "Курс «Інтелектуальні системи аналізу медичних зображень та комп’ютерної діагностики»"
echo "Піднімаю локальний сервер…"

if ! command -v npm >/dev/null 2>&1; then
  echo
  echo "Не знайдено Node.js. Встановіть його з https://nodejs.org (LTS) і запустіть цей файл знову."
  read -r
  exit 1
fi

if [ ! -d node_modules ]; then
  echo "Перший запуск: встановлюю залежності (одноразово, кілька хвилин)…"
  npm install --silent || { echo "Не вдалося встановити залежності"; read -r; exit 1; }
fi

# Пересобираємо, якщо збірки немає або вона старіша за сторінки чи тему.
NEEDS_BUILD=0
[ -f .vitepress/dist/index.html ] || NEEDS_BUILD=1
if [ -f .vitepress/dist/index.html ]; then
  NEWER=$(find lectures .vitepress/theme .vitepress/data ./*.md -newer .vitepress/dist/index.html 2>/dev/null | head -1)
  [ -n "$NEWER" ] && NEEDS_BUILD=1
fi

if [ "$NEEDS_BUILD" = "1" ]; then
  echo "Збираю сайт…"
  unset BASE                      # інакше збірка ляже під підкаталог і віддасть 404
  npm run build --silent || { echo "Не вдалося зібрати"; read -r; exit 1; }
fi

npx vitepress preview . --port "$PORT" &
SERVER=$!
trap 'kill $SERVER 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  if curl -s -o /dev/null "http://localhost:$PORT/"; then break; fi
  sleep 0.4
done

echo "Готово: http://localhost:$PORT"
open "http://localhost:$PORT/"
echo
echo "Вікно можна згорнути. Закриття вікна зупиняє сервер."
wait $SERVER
