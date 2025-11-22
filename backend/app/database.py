from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/mailmind.db")

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    email_accounts = relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="user", cascade="all, delete-orphan")

class EmailAccount(Base):
    __tablename__ = "email_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # 'gmail' or 'yahoo'
    email = Column(String, nullable=False)
    encrypted_credentials = Column(Text, nullable=False)  # Encrypted OAuth tokens/credentials
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="email_accounts")
    emails = relationship("EmailMetadata", back_populates="account", cascade="all, delete-orphan")

class EmailMetadata(Base):
    __tablename__ = "email_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    message_id = Column(String, unique=True, index=True, nullable=False)
    sender_email = Column(String, index=True, nullable=False)
    sender_name = Column(String)
    subject = Column(String, index=True)
    date_received = Column(DateTime, index=True, nullable=False)
    date_analyzed = Column(DateTime, default=datetime.utcnow)
    encrypted_metadata = Column(Text)  # Additional encrypted metadata if needed
    
    account = relationship("EmailAccount", back_populates="emails")
    analysis_results = relationship("AnalysisResult", back_populates="email", cascade="all, delete-orphan")

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    emails_processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    user = relationship("User", back_populates="analysis_runs")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("email_metadata.id"), nullable=False)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    
    # Analysis data (encrypted JSON)
    encrypted_analysis = Column(Text, nullable=False)
    
    # Indexed fields for quick queries (non-sensitive)
    sender_cluster = Column(String, index=True)
    subject_cluster = Column(String, index=True)
    category = Column(String, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    email = relationship("EmailMetadata", back_populates="analysis_results")

class ProcessedDateRange(Base):
    __tablename__ = "processed_date_ranges"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    emails_count = Column(Integer, default=0)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Ensure no overlapping ranges for same account
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

