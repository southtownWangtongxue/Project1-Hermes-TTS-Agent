from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
from typing import Generator

# 创建数据库引擎（带连接池配置）
engine = create_engine(
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
    pool_size=5,  # 连接池大小
    max_overflow=10,  # 超出 pool_size 后最大连接数
    pool_pre_ping=True,  # 连接前检查可用性
    pool_recycle=3600,  # 1小时后回收连接
    pool_timeout=30,  # 获取连接超时时间（秒）
    connect_args={"connect_timeout": 10, "charset": "utf8mb4"}  # 连接参数
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 创建数据库表
def init_db():
    """初始化所有数据库表"""
    Base.metadata.create_all(bind=engine)

# FastAPI 标准数据库会话依赖注入
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 标准数据库会话依赖注入

    Yields:
        Session: SQLAlchemy 数据库会话

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
