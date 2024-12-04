import sqlite3

# Create a database file
conn = sqlite3.connect('subscriptions.db')
cursor = conn.cursor()

# Create a table for subscriptions
cursor.execute('''
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    time TEXT NOT NULL,
    zip_code TEXT NOT NULL
)
''')

conn.commit()
conn.close()

print("Database and table initialized.")