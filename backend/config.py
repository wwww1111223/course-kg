# -*- coding: utf-8 -*-
"""
配置文件
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """应用配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'course-kg-secret-key-2024')

    # 数据库类型: 'mysql' 或 'sqlite'（sqlite 用于开发测试）
    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')

    # MySQL 数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'password')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'course_kg')

    if DB_TYPE == 'mysql':
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            'DATABASE_URL',
            f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4'
        )
    else:
        # SQLite 用于开发测试
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            'DATABASE_URL',
            f'sqlite:///{os.path.join(BASE_DIR, "course_kg.db")}'
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Neo4j 图数据库配置（可选，不可用时自动降级为 MySQL/SQLite 图谱）
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password')
