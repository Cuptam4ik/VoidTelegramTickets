# 🚀 Инструкции по развертыванию

## Быстрый старт

### 1. Подготовка окружения

```bash
# Клонируйте репозиторий
git clone <your-repo-url>
cd VoidTelegramTickets

# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка бота

1. Получите токен бота у [@BotFather](https://t.me/BotFather)
2. Отредактируйте `config.py`:
   ```python
   API_TOKEN = 'ваш_токен_бота'
   ADMINS = [ваш_telegram_id]  # ID администраторов
   ```

### 3. Запуск

```bash
# Простой запуск
python bot.py

# Или через скрипт запуска (с проверками)
python run.py
```

## Развертывание на сервере

### VPS/Хостинг

1. **Подготовка сервера:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git
   ```

2. **Клонирование и настройка:**
   ```bash
   git clone <your-repo-url>
   cd VoidTelegramTickets
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Настройка systemd сервиса:**
   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```

   Содержимое файла:
   ```ini
   [Unit]
   Description=Telegram Ticket Bot
   After=network.target

   [Service]
   Type=simple
   User=your_username
   WorkingDirectory=/path/to/VoidTelegramTickets
   Environment=PATH=/path/to/VoidTelegramTickets/venv/bin
   ExecStart=/path/to/VoidTelegramTickets/venv/bin/python bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. **Запуск сервиса:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   sudo systemctl status telegram-bot
   ```

### Docker развертывание

1. **Создайте Dockerfile:**
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   CMD ["python", "bot.py"]
   ```

2. **Создайте docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     telegram-bot:
       build: .
       restart: unless-stopped
       volumes:
         - ./tickets.db:/app/tickets.db
         - ./bot.log:/app/bot.log
       environment:
         - PYTHONUNBUFFERED=1
   ```

3. **Запуск:**
   ```bash
   docker-compose up -d
   ```

## Мониторинг и логи

### Просмотр логов

```bash
# Systemd
sudo journalctl -u telegram-bot -f

# Docker
docker-compose logs -f telegram-bot

# Файл логов
tail -f bot.log
```

### Мониторинг состояния

```bash
# Проверка статуса сервиса
sudo systemctl status telegram-bot

# Проверка процесса
ps aux | grep bot.py

# Проверка портов (если используется)
netstat -tlnp | grep python
```

## Обновление бота

### Автоматическое обновление

1. **Создайте скрипт обновления:**
   ```bash
   #!/bin/bash
   cd /path/to/VoidTelegramTickets
   git pull
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart telegram-bot
   ```

2. **Настройте cron для автоматических обновлений:**
   ```bash
   crontab -e
   # Добавьте строку для ежедневного обновления в 3:00
   0 3 * * * /path/to/update_script.sh
   ```

### Ручное обновление

```bash
# Остановите бота
sudo systemctl stop telegram-bot

# Обновите код
git pull

# Обновите зависимости
source venv/bin/activate
pip install -r requirements.txt

# Запустите бота
sudo systemctl start telegram-bot
```

## Резервное копирование

### Автоматическое резервное копирование

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/telegram-bot"
SOURCE_DIR="/path/to/VoidTelegramTickets"

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz -C $SOURCE_DIR tickets.db bot.log
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete
```

### Восстановление из резервной копии

```bash
# Остановите бота
sudo systemctl stop telegram-bot

# Восстановите базу данных
tar -xzf backup_20231201_120000.tar.gz
cp tickets.db /path/to/VoidTelegramTickets/

# Запустите бота
sudo systemctl start telegram-bot
```

## Безопасность

### Рекомендации

1. **Используйте отдельного пользователя для бота:**
   ```bash
   sudo useradd -r -s /bin/false telegram-bot
   sudo chown -R telegram-bot:telegram-bot /path/to/VoidTelegramTickets
   ```

2. **Настройте firewall:**
   ```bash
   sudo ufw allow ssh
   sudo ufw enable
   ```

3. **Регулярно обновляйте систему:**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

4. **Мониторьте логи на подозрительную активность:**
   ```bash
   grep -i "error\|exception" bot.log
   ```

## Устранение неполадок

### Частые проблемы

1. **Бот не отвечает:**
   - Проверьте токен в config.py
   - Убедитесь, что бот не заблокирован
   - Проверьте логи на ошибки

2. **Ошибки базы данных:**
   - Проверьте права доступа к tickets.db
   - Убедитесь, что SQLite установлен
   - Проверьте свободное место на диске

3. **Проблемы с зависимостями:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

4. **Проблемы с памятью:**
   - Увеличьте swap файл
   - Оптимизируйте запросы к БД
   - Добавьте больше RAM

### Контакты для поддержки

При возникновении проблем:
1. Проверьте логи: `tail -f bot.log`
2. Проверьте статус сервиса: `sudo systemctl status telegram-bot`
3. Создайте issue в репозитории с описанием проблемы

---

**Удачного развертывания!** 🚀 