#database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# app/models/*가 실제로 상속하는 Base와 동일한 인스턴스를 재사용해야
# main.py의 Base.metadata.create_all()이 테이블을 실제로 만든다.
# (과거엔 여기서 declarative_base()를 새로 만들어 메타데이터가 항상 비어 있었음)
from app.models.base import Base

# 환경변수에서 데이터베이스 URL 가져오기
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:1234@127.0.0.1:3306/tt"  # 기본값
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# DB 세션 DI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()