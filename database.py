from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://{insta_user}:{qwe123}@localhost/{insta}", ech=True)

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)
