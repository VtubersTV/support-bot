def db_start(cursor):
    cursor.execute('''
CREATE TABLE IF NOT EXISTS LofiMusic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    video_id TEXT DEFAULT NULL,
    thumbnail TEXT DEFAULT NULL,
    duration INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER NOT NULL
)
''')