import psycopg2

def main():
    test_connection()

def test_connection():
    dsn = "postgresql://admin:secret@localhost:5432/recommender"
    try:
        conn = psycopg2.connect(dsn)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print("Успешное подключение!")
        print(f"Версия PostgreSQL: {version[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        
if __name__ == "__main__":
    main()


        