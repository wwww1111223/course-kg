# -*- coding: utf-8 -*-
"""
数据模型定义 - 增强版
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(100), default='')
    avatar = db.Column(db.Text, default='')
    title = db.Column(db.String(50), default='学徒')  # 学分段位：学徒/学士/硕士/博士
    total_credits = db.Column(db.Float, default=0.0)   # 已修学分
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ratings = db.relationship('Rating', backref='user', lazy='dynamic')
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    annotations = db.relationship('Annotation', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'avatar': self.avatar,
            'title': self.title,
            'total_credits': self.total_credits,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }


class Course(db.Model):
    """课程模型"""
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200), default='')
    credit = db.Column(db.Float, default=0.0)
    clc_number = db.Column(db.String(50), default='')
    category = db.Column(db.String(50), default='')
    department = db.Column(db.String(100), default='')
    description = db.Column(db.Text, default='')
    teacher = db.Column(db.String(100), default='')
    exam_difficulty = db.Column(db.Float, default=0.0)    # 考试难度均分
    workload = db.Column(db.Float, default=0.0)           # 作业量均分
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ratings = db.relationship('Rating', backref='course', lazy='dynamic')
    reviews = db.relationship('Review', backref='course', lazy='dynamic')

    def to_dict(self):
        avg_score = db.session.query(db.func.avg(Rating.score)).filter(
            Rating.course_id == self.id
        ).scalar()
        rating_count = Rating.query.filter_by(course_id=self.id).count()

        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'credit': self.credit,
            'clc_number': self.clc_number,
            'category': self.category,
            'department': self.department,
            'description': self.description,
            'teacher': self.teacher,
            'avg_score': round(avg_score, 1) if avg_score else 0,
            'rating_count': rating_count,
            'exam_difficulty': round(self.exam_difficulty, 1),
            'workload': round(self.workload, 1)
        }


class KnowledgePoint(db.Model):
    """知识点模型"""
    __tablename__ = 'knowledge_points'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    subject_category = db.Column(db.String(100), default='')
    dimension = db.Column(db.String(50), default='')
    difficulty = db.Column(db.Integer, default=1)  # 1-5 难度等级
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    annotations = db.relationship('Annotation', backref='knowledge_point', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'subject_category': self.subject_category,
            'dimension': self.dimension,
            'difficulty': self.difficulty
        }


class CourseKnowledge(db.Model):
    """课程-知识点关联"""
    __tablename__ = 'course_knowledge'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    kp_id = db.Column(db.Integer, db.ForeignKey('knowledge_points.id'), nullable=False)
    importance = db.Column(db.String(20), default='medium')


class CoursePrerequisite(db.Model):
    """课程前置依赖关系"""
    __tablename__ = 'course_prerequisites'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    prereq_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    reason = db.Column(db.String(255), default='')


class CourseTag(db.Model):
    """课程标签（考研推荐、水课、硬核等）"""
    __tablename__ = 'course_tags'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    tag = db.Column(db.String(50), nullable=False)  # 考研推荐, 硬核专业核心, 水课, 论文多
    count = db.Column(db.Integer, default=1)


class Rating(db.Model):
    """评分模型（基础星评）"""
    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MultiDimRating(db.Model):
    """多维度评分（考试难度、作业量、实用性、就业帮助）"""
    __tablename__ = 'multi_dim_ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    exam_difficulty = db.Column(db.Integer, default=3)   # 1-5
    workload = db.Column(db.Integer, default=3)           # 1-5
    practicality = db.Column(db.Integer, default=3)       # 1-5
    career_help = db.Column(db.Integer, default=3)        # 1-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'exam_difficulty': self.exam_difficulty,
            'workload': self.workload,
            'practicality': self.practicality,
            'career_help': self.career_help
        }


class Review(db.Model):
    """点评模型"""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)     # 置顶
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '',
            'display_name': self.user.display_name if self.user else '',
            'course_id': self.course_id,
            'content': self.content,
            'is_pinned': self.is_pinned,
            'like_count': self.like_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''
        }


class Annotation(db.Model):
    """知识点标注模型"""
    __tablename__ = 'annotations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    kp_id = db.Column(db.Integer, db.ForeignKey('knowledge_points.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '',
            'display_name': self.user.display_name if self.user else '',
            'kp_id': self.kp_id,
            'kp_name': self.knowledge_point.name if self.knowledge_point else '',
            'content': self.content,
            'is_private': self.is_private,
            'like_count': self.like_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''
        }


class Question(db.Model):
    """问答区问题"""
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    kp_id = db.Column(db.Integer, db.ForeignKey('knowledge_points.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    qtype = db.Column(db.String(20), default='选课咨询')  # 选课咨询 / 知识点答疑
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='questions')
    answers = db.relationship('Answer', backref='question', lazy='dynamic', order_by='Answer.created_at.desc()')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '',
            'display_name': self.user.display_name if self.user else '',
            'course_id': self.course_id,
            'kp_id': self.kp_id,
            'title': self.title,
            'content': self.content,
            'qtype': self.qtype,
            'answers': [a.to_dict() for a in self.answers.limit(5)] if self.answers else [],
            'answer_count': self.answers.count() if self.answers else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Answer(db.Model):
    """问答区回答"""
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='answers')

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '',
            'display_name': self.user.display_name if self.user else '',
            'content': self.content,
            'like_count': self.like_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Achievement(db.Model):
    """成就定义"""
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), default='')
    icon = db.Column(db.String(50), default='book')  # emoji or icon class
    condition_type = db.Column(db.String(50))  # annotations_count, reviews_count, etc.
    condition_value = db.Column(db.Integer, default=1)


class UserAchievement(db.Model):
    """用户获得的成就"""
    __tablename__ = 'user_achievements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudyPlan(db.Model):
    """学习计划"""
    __tablename__ = 'study_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), default='默认方案')
    semester = db.Column(db.String(20))  # 2025-秋
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudyPlanCourse(db.Model):
    """学习计划中的课程"""
    __tablename__ = 'study_plan_courses'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plans.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)


class QuizAttempt(db.Model):
    """答题记录"""
    __tablename__ = 'quiz_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    kp_id = db.Column(db.Integer, db.ForeignKey('knowledge_points.id'), nullable=False)
    correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    """社区留言"""
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(100), default='游客')
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'content': self.content,
            'likes': self.likes,
            'created_at': self.created_at.strftime('%m-%d %H:%M') if self.created_at else ''
        }


class ReviewLike(db.Model):
    """点评点赞"""
    __tablename__ = 'review_likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AnnotationLike(db.Model):
    """标注点赞"""
    __tablename__ = 'annotation_likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    annotation_id = db.Column(db.Integer, db.ForeignKey('annotations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
