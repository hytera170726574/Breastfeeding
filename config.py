import os
from datetime import timedelta


def _normalize_database_url(url: str) -> str:
    """确保 DATABASE_URL 使用 SQLAlchemy 支持的 Postgres 前缀。"""
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql+psycopg://', 1)
    if url.startswith('postgresql://') and '+psycopg' not in url:
        return url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEFAULT_POSTGRES_URL = 'postgresql+psycopg://breastfeeding_app:breastfeeding_pass@localhost:5432/breastfeeding'
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get('DATABASE_URL', DEFAULT_POSTGRES_URL))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)