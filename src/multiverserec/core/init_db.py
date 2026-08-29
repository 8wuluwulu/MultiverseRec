from multiverserec.core.database import engine, Base
from multiverserec.models import Content

def init_database():
    Base.metadata.create_all(bind=engine)
    print("Всё отлично")


if __name__ == "__main__":
    init_database()