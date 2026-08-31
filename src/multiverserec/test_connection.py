from multiverserec.core.database import SessionLocal
from multiverserec.models import Book


def main():
    test_connection()

def test_connection():
    session = SessionLocal()
    book = Book(title="Test Book", author="Test Author", description="Test Description", genres=["Test Genre"], pages=100, rating=5.0)
    session.add(book)
    session.commit()
    session.close()
    print("Всё ок")
    
if __name__ == "__main__":
    main()