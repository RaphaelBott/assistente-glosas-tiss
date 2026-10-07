import sqlite3

conn = sqlite3.connect("data/tiss.db")
cur = conn.cursor()

# Quantos registros na tabela procedimentos?
cur.execute("SELECT COUNT(*) FROM procedimentos")
print("Total de procedimentos:", cur.fetchone()[0])

# Ver os primeiros 5
print()
print("=== Primeiros 5 procedimentos ===")
cur.execute("SELECT * FROM procedimentos LIMIT 5")
for row in cur.fetchall():
    print(row)

# Ver a estrutura da tabela
print()
print("=== Estrutura da tabela ===")
cur.execute("PRAGMA table_info(procedimentos)")
for row in cur.fetchall():
    print(row)

# Ver os códigos que começam com 101
print()
print("=== Códigos que começam com 101 ===")
cur.execute("SELECT * FROM procedimentos WHERE codigo LIKE '101%' LIMIT 5")
for row in cur.fetchall():
    print(row)

conn.close()