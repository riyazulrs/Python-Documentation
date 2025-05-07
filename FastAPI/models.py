from sqlalchemy import Column, Integer, String, Float, Date
from Database import Base

# Employee table (from Sheet 1)
class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(150), unique=True)
    department = Column(String(100))
    salary = Column(Float)
    doj = Column(Date)
    address = Column(String(255))

# Experience or Post table (from Sheet 2)
class Post(Base):  # Renamed to `Post`, assuming this is for sheet 2
    __tablename__ = "posts"  # Corrected spelling and casing

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(150))
    start_date = Column(Date)
    end_date = Column(Date)


