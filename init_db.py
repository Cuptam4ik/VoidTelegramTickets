import asyncio
import aiosqlite

db_path = 'tickets.db'

async def init_db():
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                nickname TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                description TEXT NOT NULL,
                evidence_file_id TEXT,
                status TEXT DEFAULT 'open',
                admin_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Добавляем assigned_admin, если его нет
        try:
            await db.execute('ALTER TABLE tickets ADD COLUMN assigned_admin INTEGER')
        except Exception:
            pass  # Столбец уже существует
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ticket_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_name TEXT,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ticket_threads (
                ticket_id INTEGER NOT NULL,
                message_thread_id INTEGER NOT NULL,
                PRIMARY KEY (ticket_id),
                FOREIGN KEY (ticket_id) REFERENCES tickets (id)
            )
        ''')
        await db.commit()
        print('База данных инициализирована!')

if __name__ == '__main__':
    asyncio.run(init_db()) 