# -*- coding: utf-8 -*-
"""信息组织大作业2 - 增强版 Flask 后端"""
import os, json, random
from flask import Flask, jsonify, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from config import Config
from models import db, User, Course, KnowledgePoint, CourseKnowledge, Rating, Review, Annotation
from models import MultiDimRating, CourseTag, Question, Answer, Achievement, UserAchievement
from models import StudyPlan, StudyPlanCourse, QuizAttempt, CoursePrerequisite, ReviewLike, AnnotationLike, Message
from sqlalchemy import func, text
from neo4j import GraphDatabase


def create_app():
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    app.config.from_object(Config)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['TEMPLATE_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../frontend')
    db.init_app(app)
    CORS(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login_page'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    neo4j_driver = None
    def get_neo4j():
        nonlocal neo4j_driver
        if neo4j_driver is None:
            try:
                neo4j_driver = GraphDatabase.driver(Config.NEO4J_URI, auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD))
            except:
                neo4j_driver = None
        return neo4j_driver

    # ===================== 页面路由 =====================
    @app.route('/')
    def index_page(): return app.send_static_file('index.html')
    @app.route('/login')
    def login_page(): return app.send_static_file('login.html')
    @app.route('/register')
    def register_page(): return app.send_static_file('register.html')
    @app.route('/profile')
    def profile_page(): return app.send_static_file('profile.html')
    @app.route('/course')
    def course_list_page(): return app.send_static_file('index.html')
    @app.route('/course/<int:course_id>')
    def course_page(course_id): return app.send_static_file('course.html')
    @app.route('/visualization')
    def visualization_page(): return app.send_static_file('visualization.html')
    @app.route('/analysis')
    def analysis_page(): return app.send_static_file('analysis.html')
    @app.route('/leaderboard')
    def leaderboard_page(): return app.send_static_file('leaderboard.html')
    @app.route('/planner')
    def planner_page(): return app.send_static_file('planner.html')
    @app.route('/quiz')
    def quiz_page(): return app.send_static_file('quiz.html')
    @app.route('/library')
    def library_page(): return app.send_static_file('library.html')

    # ===================== 用户认证 =====================
    @app.route('/api/auth/register', methods=['POST'])
    def api_register():
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        display_name = data.get('display_name', '').strip()
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        user = User(username=username, display_name=display_name or username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': '注册成功', 'user': user.to_dict()})

    @app.route('/api/auth/login', methods=['POST'])
    def api_login():
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        login_user(user, remember=True)
        return jsonify({'success': True, 'message': '登录成功', 'user': user.to_dict()})

    @app.route('/api/auth/logout', methods=['POST'])
    @login_required
    def api_logout():
        logout_user()
        return jsonify({'success': True, 'message': '已退出登录'})

    @app.route('/api/auth/status')
    def api_auth_status():
        if current_user.is_authenticated:
            return jsonify({'authenticated': True, 'user': current_user.to_dict()})
        return jsonify({'authenticated': False, 'user': None})

    # ===================== 课程 API =====================
    @app.route('/api/courses')
    def api_courses():
        courses = Course.query.all()
        result = []
        for course in courses:
            cd = course.to_dict()
            ck_list = CourseKnowledge.query.filter_by(course_id=course.id).all()
            kp_ids = [ck.kp_id for ck in ck_list]
            if kp_ids:
                kps = KnowledgePoint.query.filter(KnowledgePoint.id.in_(kp_ids)).all()
                dims = list(set(kp.dimension for kp in kps if kp.dimension))
                cd['dimensions'] = dims
            else:
                cd['dimensions'] = []
            # 获取标签
            tags = CourseTag.query.filter_by(course_id=course.id).all()
            cd['tags'] = [t.tag for t in tags]
            # 获取多维评分
            dim_ratings = MultiDimRating.query.filter_by(course_id=course.id).all()
            if dim_ratings:
                cd['avg_exam_diff'] = round(sum(r.exam_difficulty for r in dim_ratings)/len(dim_ratings), 1)
                cd['avg_workload'] = round(sum(r.workload for r in dim_ratings)/len(dim_ratings), 1)
                cd['avg_practicality'] = round(sum(r.practicality for r in dim_ratings)/len(dim_ratings), 1)
                cd['avg_career_help'] = round(sum(r.career_help for r in dim_ratings)/len(dim_ratings), 1)
            else:
                cd['avg_exam_diff'] = cd['avg_workload'] = cd['avg_practicality'] = cd['avg_career_help'] = 0
            # 前置课程
            prereqs = CoursePrerequisite.query.filter_by(course_id=course.id).all()
            cd['prerequisites'] = [{'id': p.prereq_id, 'name': Course.query.get(p.prereq_id).name if Course.query.get(p.prereq_id) else ''} for p in prereqs]
            result.append(cd)
        return jsonify({'success': True, 'courses': result})

    @app.route('/api/courses/<int:course_id>')
    def api_course_detail(course_id):
        course = Course.query.get_or_404(course_id)
        result = course.to_dict()
        ck_list = CourseKnowledge.query.filter_by(course_id=course_id).all()
        kp_ids = [ck.kp_id for ck in ck_list]
        kps = KnowledgePoint.query.filter(KnowledgePoint.id.in_(kp_ids)).all() if kp_ids else []
        result['knowledge_points'] = [kp.to_dict() for kp in kps]
        if current_user.is_authenticated:
            user_rating = Rating.query.filter_by(user_id=current_user.id, course_id=course_id).first()
            result['user_rating'] = user_rating.score if user_rating else None
            user_dim = MultiDimRating.query.filter_by(user_id=current_user.id, course_id=course_id).first()
            result['user_dim_rating'] = user_dim.to_dict() if user_dim else None
        else:
            result['user_rating'] = None
            result['user_dim_rating'] = None
        reviews = Review.query.filter_by(course_id=course_id).order_by(Review.is_pinned.desc(), Review.created_at.desc()).all()[:20]
        result['reviews'] = [r.to_dict() for r in reviews]
        # 多维评分聚合
        dim_ratings = MultiDimRating.query.filter_by(course_id=course_id).all()
        if dim_ratings:
            n = len(dim_ratings)
            result['avg_exam_diff'] = round(sum(r.exam_difficulty for r in dim_ratings)/n, 1)
            result['avg_workload'] = round(sum(r.workload for r in dim_ratings)/n, 1)
            result['avg_practicality'] = round(sum(r.practicality for r in dim_ratings)/n, 1)
            result['avg_career_help'] = round(sum(r.career_help for r in dim_ratings)/n, 1)
            result['dim_rating_count'] = n
        else:
            result['avg_exam_diff'] = result['avg_workload'] = result['avg_practicality'] = result['avg_career_help'] = 0
            result['dim_rating_count'] = 0
        # 标签
        tags = CourseTag.query.filter_by(course_id=course_id).all()
        result['tags'] = [t.tag for t in tags]
        # 前置课程
        prereqs = CoursePrerequisite.query.filter_by(course_id=course_id).all()
        result['prerequisites'] = [{'id': p.prereq_id, 'name': Course.query.get(p.prereq_id).name if Course.query.get(p.prereq_id) else ''} for p in prereqs]
        # 后置课程（哪些课依赖本课）
        postreqs = CoursePrerequisite.query.filter_by(prereq_id=course_id).all()
        result['postrequisites'] = [{'id': p.course_id, 'name': Course.query.get(p.course_id).name if Course.query.get(p.course_id) else ''} for p in postreqs]
        # 问答
        questions = Question.query.filter_by(course_id=course_id).order_by(Question.created_at.desc()).all()[:10]
        result['questions'] = [q.to_dict() for q in questions]
        return jsonify({'success': True, 'course': result})

    # ===================== 多维评分 =====================
    @app.route('/api/courses/<int:course_id>/dim-rate', methods=['POST'])
    @login_required
    def api_dim_rate(course_id):
        data = request.get_json()
        existing = MultiDimRating.query.filter_by(user_id=current_user.id, course_id=course_id).first()
        if existing:
            existing.exam_difficulty = data.get('exam_difficulty', existing.exam_difficulty)
            existing.workload = data.get('workload', existing.workload)
            existing.practicality = data.get('practicality', existing.practicality)
            existing.career_help = data.get('career_help', existing.career_help)
        else:
            r = MultiDimRating(user_id=current_user.id, course_id=course_id,
                               exam_difficulty=data.get('exam_difficulty', 3),
                               workload=data.get('workload', 3),
                               practicality=data.get('practicality', 3),
                               career_help=data.get('career_help', 3))
            db.session.add(r)
        db.session.commit()
        return jsonify({'success': True, 'message': '多维评分成功'})

    # ===================== 课程标签 =====================
    @app.route('/api/courses/<int:course_id>/tags', methods=['POST'])
    @login_required
    def api_tag_course(course_id):
        data = request.get_json()
        tag = data.get('tag', '').strip()
        if tag not in ['考研推荐', '硬核专业核心', '水课', '论文多']:
            return jsonify({'success': False, 'message': '无效标签'}), 400
        existing = CourseTag.query.filter_by(course_id=course_id, tag=tag).first()
        if existing:
            existing.count += 1
        else:
            db.session.add(CourseTag(course_id=course_id, tag=tag, count=1))
        db.session.commit()
        return jsonify({'success': True, 'message': '标签投票成功'})

    # ===================== 评分/点评 =====================
    @app.route('/api/courses/<int:course_id>/rate', methods=['POST'])
    @login_required
    def api_rate_course(course_id):
        data = request.get_json()
        score = data.get('score')
        if not score or not isinstance(score, int) or score < 1 or score > 5:
            return jsonify({'success': False, 'message': '评分必须在1-5之间'}), 400
        existing = Rating.query.filter_by(user_id=current_user.id, course_id=course_id).first()
        if existing:
            existing.score = score
        else:
            db.session.add(Rating(user_id=current_user.id, course_id=course_id, score=score))
        db.session.commit()
        return jsonify({'success': True, 'message': '评分成功'})

    @app.route('/api/courses/<int:course_id>/review', methods=['POST'])
    @login_required
    def api_review_course(course_id):
        data = request.get_json()
        content = data.get('content', '').strip()
        if not content:
            return jsonify({'success': False, 'message': '点评内容不能为空'}), 400
        existing = Review.query.filter_by(user_id=current_user.id, course_id=course_id).first()
        if existing:
            existing.content = content
        else:
            db.session.add(Review(user_id=current_user.id, course_id=course_id, content=content))
        db.session.commit()
        return jsonify({'success': True, 'message': '点评提交成功'})

    # ===================== 知识点与标注 =====================
    @app.route('/api/knowledge-points')
    def api_knowledge_points():
        kps = KnowledgePoint.query.all()
        return jsonify({'success': True, 'knowledge_points': [kp.to_dict() for kp in kps]})

    @app.route('/api/knowledge-points/<int:kp_id>')
    def api_kp_detail(kp_id):
        kp = KnowledgePoint.query.get_or_404(kp_id)
        result = kp.to_dict()
        annotations = Annotation.query.filter_by(kp_id=kp_id, is_private=False).order_by(Annotation.created_at.desc()).all()[:20]
        result['annotations'] = [a.to_dict() for a in annotations]
        if current_user.is_authenticated:
            user_ann = Annotation.query.filter_by(user_id=current_user.id, kp_id=kp_id).first()
            result['user_annotation'] = user_ann.to_dict() if user_ann else None
        else:
            result['user_annotation'] = None
        return jsonify({'success': True, 'knowledge_point': result})

    @app.route('/api/knowledge-points/<int:kp_id>/annotate', methods=['POST'])
    @login_required
    def api_annotate_kp(kp_id):
        data = request.get_json()
        content = data.get('content', '').strip()
        if not content:
            return jsonify({'success': False, 'message': '标注内容不能为空'}), 400
        is_private = data.get('is_private', False)
        existing = Annotation.query.filter_by(user_id=current_user.id, kp_id=kp_id).first()
        if existing:
            existing.content = content
            existing.is_private = is_private
        else:
            db.session.add(Annotation(user_id=current_user.id, kp_id=kp_id, content=content, is_private=is_private))
        db.session.commit()
        return jsonify({'success': True, 'message': '标注保存成功'})

    @app.route('/api/knowledge-points/<int:kp_id>/annotate', methods=['DELETE'])
    @login_required
    def api_delete_annotation(kp_id):
        ann = Annotation.query.filter_by(user_id=current_user.id, kp_id=kp_id).first()
        if not ann:
            return jsonify({'success': False, 'message': '标注不存在'}), 404
        db.session.delete(ann)
        db.session.commit()
        return jsonify({'success': True, 'message': '标注已删除'})

    @app.route('/api/knowledge-points/<int:kp_id>/annotations')
    def api_kp_annotations(kp_id):
        annotations = Annotation.query.filter_by(kp_id=kp_id, is_private=False).order_by(Annotation.created_at.desc()).all()[:30]
        return jsonify({'success': True, 'annotations': [a.to_dict() for a in annotations]})

    # ===================== 问答 API =====================
    @app.route('/api/courses/<int:course_id>/questions', methods=['GET', 'POST'])
    def api_course_questions(course_id):
        if request.method == 'GET':
            qs = Question.query.filter_by(course_id=course_id).order_by(Question.created_at.desc()).all()
            result = []
            for q in qs:
                d = q.to_dict()
                answers = Answer.query.filter_by(question_id=q.id).order_by(Answer.created_at.desc()).all()[:5]
                d['answers'] = [a.to_dict() for a in answers]
                d['answer_count'] = Answer.query.filter_by(question_id=q.id).count()
                result.append(d)
            return jsonify({'success': True, 'questions': result})
        else:
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            data = request.get_json()
            q = Question(user_id=current_user.id, course_id=course_id,
                         title=data.get('title', ''), content=data.get('content', ''),
                         qtype=data.get('qtype', '选课咨询'),
                         kp_id=data.get('kp_id'))
            db.session.add(q)
            db.session.commit()
            return jsonify({'success': True, 'question': q.to_dict()})

    @app.route('/api/questions/<int:question_id>/answer', methods=['POST'])
    @login_required
    def api_answer_question(question_id):
        data = request.get_json()
        content = data.get('content', '').strip()
        if not content:
            return jsonify({'success': False, 'message': '回答内容不能为空'}), 400
        a = Answer(question_id=question_id, user_id=current_user.id, content=content)
        db.session.add(a)
        db.session.commit()
        return jsonify({'success': True, 'answer': a.to_dict()})

    @app.route('/api/questions/<int:question_id>', methods=['DELETE'])
    @login_required
    def api_delete_question(question_id):
        question = Question.query.get_or_404(question_id)
        if question.user_id != current_user.id:
            return jsonify({'success': False, 'message': '只能删除自己的提问'}), 403
        Answer.query.filter_by(question_id=question_id).delete()
        db.session.delete(question)
        db.session.commit()
        return jsonify({'success': True, 'message': '提问已删除'})

    @app.route('/api/answers/<int:answer_id>', methods=['DELETE'])
    @login_required
    def api_delete_answer(answer_id):
        answer = Answer.query.get_or_404(answer_id)
        if answer.user_id != current_user.id:
            return jsonify({'success': False, 'message': '只能删除自己的回答'}), 403
        db.session.delete(answer)
        db.session.commit()
        return jsonify({'success': True, 'message': '回答已删除'})

    # ===================== 成就 API =====================
    @app.route('/api/achievements')
    def api_achievements():
        achievements = Achievement.query.all()
        return jsonify({'success': True, 'achievements': [{'id': a.id, 'name': a.name, 'description': a.description, 'icon': a.icon} for a in achievements]})

    @app.route('/api/user/achievements')
    @login_required
    def api_user_achievements():
        ua = UserAchievement.query.filter_by(user_id=current_user.id).all()
        ids = [a.achievement_id for a in ua]
        all_ach = Achievement.query.all()
        result = []
        for a in all_ach:
            result.append({
                'id': a.id, 'name': a.name, 'description': a.description, 'icon': a.icon,
                'unlocked': a.id in ids
            })
        # 自动检查成就
        _check_achievements(current_user.id)
        return jsonify({'success': True, 'achievements': result})

    def _check_achievements(user_id):
        """自动检查和发放成就"""
        checks = [
            ('first_annotation', 'annotations_count', 1, '批注新手'),
            ('five_annotations', 'annotations_count', 5, '批注达人'),
            ('first_review', 'reviews_count', 1, '点评新手'),
            ('ten_reviews', 'reviews_count', 10, '点评达人'),
            ('first_rating', 'ratings_count', 1, '评分新手'),
            ('explorer', 'courses_rated', 10, '课程探索者'),
        ]
        for key, ctype, cval, aname in checks:
            ach = Achievement.query.filter_by(name=aname).first()
            if not ach:
                ach = Achievement(name=aname, description=f'达成条件：{ctype} >= {cval}', icon='star', condition_type=ctype, condition_value=cval)
                db.session.add(ach)
                db.session.commit()
            if UserAchievement.query.filter_by(user_id=user_id, achievement_id=ach.id).first():
                continue
            if ctype == 'annotations_count':
                cnt = Annotation.query.filter_by(user_id=user_id).count()
            elif ctype == 'reviews_count':
                cnt = Review.query.filter_by(user_id=user_id).count()
            elif ctype == 'ratings_count':
                cnt = Rating.query.filter_by(user_id=user_id).count()
            elif ctype == 'courses_rated':
                cnt = db.session.query(Rating.course_id).filter_by(user_id=user_id).distinct().count()
            else:
                cnt = 0
            if cnt >= cval:
                db.session.add(UserAchievement(user_id=user_id, achievement_id=ach.id))
                db.session.commit()

    # ===================== 用户信息 =====================
    @app.route('/api/user/profile')
    @login_required
    def api_user_profile():
        user = current_user
        result = user.to_dict()
        ratings = Rating.query.filter_by(user_id=user.id).all()
        result['ratings'] = []
        for r in ratings:
            course = Course.query.get(r.course_id)
            result['ratings'].append({'course_id': r.course_id, 'course_name': course.name if course else '', 'score': r.score})
        reviews = Review.query.filter_by(user_id=user.id).order_by(Review.created_at.desc()).all()
        result['reviews'] = [r.to_dict() for r in reviews]
        annotations = Annotation.query.filter_by(user_id=user.id).order_by(Annotation.created_at.desc()).all()
        result['annotations'] = [a.to_dict() for a in annotations]
        # 成就
        ua = UserAchievement.query.filter_by(user_id=user.id).all()
        result['achievements'] = [{'id': a.achievement_id, 'name': Achievement.query.get(a.achievement_id).name if Achievement.query.get(a.achievement_id) else ''} for a in ua]
        return jsonify({'success': True, 'profile': result})

    # ===================== 学习计划 API =====================
    @app.route('/api/study-plans', methods=['GET', 'POST'])
    @login_required
    def api_study_plans():
        if request.method == 'GET':
            plans = StudyPlan.query.filter_by(user_id=current_user.id).all()
            result = []
            for p in plans:
                d = {'id': p.id, 'name': p.name, 'semester': p.semester, 'courses': []}
                spcs = StudyPlanCourse.query.filter_by(plan_id=p.id).all()
                total_credits = 0
                for spc in spcs:
                    c = Course.query.get(spc.course_id)
                    if c:
                        d['courses'].append({'course_id': c.id, 'name': c.name, 'credit': c.credit, 'is_completed': spc.is_completed})
                        if spc.is_completed:
                            total_credits += c.credit
                d['total_credits'] = round(total_credits, 1)
                result.append(d)
            return jsonify({'success': True, 'plans': result})
        else:
            data = request.get_json()
            p = StudyPlan(user_id=current_user.id, name=data.get('name', '新方案'), semester=data.get('semester', ''))
            db.session.add(p)
            db.session.commit()
            return jsonify({'success': True, 'plan': {'id': p.id, 'name': p.name, 'semester': p.semester, 'courses': [], 'total_credits': 0}})

    @app.route('/api/study-plans/<int:plan_id>/courses', methods=['POST'])
    @login_required
    def api_add_plan_course(plan_id):
        plan = StudyPlan.query.get_or_404(plan_id)
        if plan.user_id != current_user.id:
            return jsonify({'success': False, 'message': '无权限'}), 403
        data = request.get_json()
        course_id = data.get('course_id')
        if StudyPlanCourse.query.filter_by(plan_id=plan_id, course_id=course_id).first():
            return jsonify({'success': False, 'message': '课程已在计划中'}), 400
        spc = StudyPlanCourse(plan_id=plan_id, course_id=course_id)
        db.session.add(spc)
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/api/study-plans/<int:plan_id>/courses/<int:course_id>/toggle', methods=['POST'])
    @login_required
    def api_toggle_course(plan_id, course_id):
        spc = StudyPlanCourse.query.filter_by(plan_id=plan_id, course_id=course_id).first_or_404()
        spc.is_completed = not spc.is_completed
        db.session.commit()
        return jsonify({'success': True, 'is_completed': spc.is_completed})

    @app.route('/api/study-plans/<int:plan_id>', methods=['PUT', 'DELETE'])
    @login_required
    def api_manage_plan(plan_id):
        plan = StudyPlan.query.get_or_404(plan_id)
        if plan.user_id != current_user.id:
            return jsonify({'success': False, 'message': '无权限'}), 403
        if request.method == 'PUT':
            data = request.get_json()
            if data.get('name'): plan.name = data['name']
            if data.get('semester'): plan.semester = data['semester']
            db.session.commit()
            return jsonify({'success': True, 'message': '计划已更新'})
        else:  # DELETE
            StudyPlanCourse.query.filter_by(plan_id=plan_id).delete()
            db.session.delete(plan)
            db.session.commit()
            return jsonify({'success': True, 'message': '计划已删除'})

    @app.route('/api/study-plans/<int:plan_id>/courses/<int:course_id>', methods=['DELETE'])
    @login_required
    def api_remove_plan_course(plan_id, course_id):
        plan = StudyPlan.query.get_or_404(plan_id)
        if plan.user_id != current_user.id:
            return jsonify({'success': False, 'message': '无权限'}), 403
        spc = StudyPlanCourse.query.filter_by(plan_id=plan_id, course_id=course_id).first_or_404()
        db.session.delete(spc)
        db.session.commit()
        return jsonify({'success': True, 'message': '课程已移除'})

    # ===================== 通关答题 =====================
    @app.route('/api/quiz/question')
    def api_random_quiz():
        count = request.args.get('count', 1, type=int)
        kps = KnowledgePoint.query.all()
        selected = random.sample(kps, min(count, len(kps)))
        items = []
        for kp in selected:
            # 生成干扰项
            wrongs = KnowledgePoint.query.filter(KnowledgePoint.id != kp.id).all()
            if len(wrongs) > 3:
                wrongs = random.sample(wrongs, 3)
            options = [kp.name] + [w.name for w in wrongs]
            random.shuffle(options)
            items.append({
                'kp_id': kp.id,
                'question': f'以下哪项属于「{kp.dimension or "未知"}」维度的知识点？',
                'answer': kp.name,
                'options': options,
                'dimension': kp.dimension,
                'description': kp.description
            })
        return jsonify({'success': True, 'questions': items})

    @app.route('/api/quiz/submit', methods=['POST'])
    @login_required
    def api_quiz_submit():
        data = request.get_json()
        results = data.get('results', [])
        correct_count = 0
        for r in results:
            is_correct = r.get('is_correct', False)
            if is_correct:
                correct_count += 1
            db.session.add(QuizAttempt(user_id=current_user.id, kp_id=r.get('kp_id'), correct=is_correct))
        db.session.commit()
        return jsonify({'success': True, 'correct': correct_count, 'total': len(results)})

    # ===================== 知识图谱 API =====================
    @app.route('/api/graph')
    def api_graph():
        driver = get_neo4j()
        if not driver:
            return _graph_from_mysql()
        try:
            with driver.session() as session:
                nodes_result = session.run("MATCH (n) RETURN id(n) AS id, labels(n) AS labels, n.name AS name, n.description AS description, n.credit AS credit, n.clc_number AS clc_number, n.department AS department, n.subject_category AS subject_category ORDER BY id(n)")
                nodes = []
                for record in nodes_result:
                    node_id = record['id']
                    labels = record['labels']
                    node_type = labels[0] if labels else 'Unknown'
                    name = record['name'] or ''
                    node_data = {'id': node_id, 'label': name, 'type': node_type, 'description': record['description'] or ''}
                    if node_type == 'Course':
                        node_data['credit'] = record['credit']
                        node_data['clc_number'] = record['clc_number']
                        node_data['department'] = record['department']
                    if node_type == 'KnowledgePoint':
                        node_data['subject_category'] = record['subject_category'] or ''
                    nodes.append(node_data)
                rels_result = session.run("MATCH ()-[r]->() RETURN id(r) AS id, type(r) AS type, id(startNode(r)) AS source, id(endNode(r)) AS target, r.importance AS importance, r.reason AS reason")
                links = [{'id': record['id'], 'source': record['source'], 'target': record['target'], 'type': record['type'], 'importance': record['importance'] or '', 'reason': record['reason'] or ''} for record in rels_result]
                return jsonify({'success': True, 'nodes': nodes, 'links': links})
        except:
            return _graph_from_mysql()

    def _graph_from_mysql():
        courses = Course.query.all()
        kps = KnowledgePoint.query.all()
        ck_list = CourseKnowledge.query.all()
        nodes, links = [], []
        node_id = 0
        course_node_ids = {}
        for c in courses:
            node_id += 1
            course_node_ids[c.id] = node_id
            nodes.append({'id': node_id, 'label': c.name, 'type': 'Course', 'description': c.description or '', 'credit': c.credit, 'clc_number': c.clc_number, 'department': c.department or ''})
        kp_node_ids = {}
        for kp in kps:
            node_id += 1
            kp_node_ids[kp.id] = node_id
            nodes.append({'id': node_id, 'label': kp.name, 'type': 'KnowledgePoint', 'description': kp.description or '', 'subject_category': kp.subject_category or '', 'dimension': kp.dimension or '', 'db_id': kp.id})
        for ck in ck_list:
            source = course_node_ids.get(ck.course_id)
            target = kp_node_ids.get(ck.kp_id)
            if source and target:
                links.append({'source': source, 'target': target, 'type': 'HAS_KNOWLEDGE', 'importance': ck.importance})
        return jsonify({'success': True, 'nodes': nodes, 'links': links})

    # ===================== 分析 API =====================
    @app.route('/api/analysis/degree')
    def api_analysis_degree():
        result = db.session.query(KnowledgePoint.id, KnowledgePoint.name, KnowledgePoint.description, func.count(CourseKnowledge.course_id).label('degree'))\
            .join(CourseKnowledge, KnowledgePoint.id == CourseKnowledge.kp_id)\
            .group_by(KnowledgePoint.id).order_by(func.count(CourseKnowledge.course_id).desc()).limit(10).all()
        return jsonify({'success': True, 'data': [{'id': r.id, 'name': r.name, 'description': r.description, 'degree': r.degree} for r in result]})

    @app.route('/api/analysis/shared-kp')
    def api_analysis_shared_kp():
        sql = text("SELECT a.course_id AS course_id_a, b.course_id AS course_id_b, COUNT(*) AS shared_count FROM course_knowledge a JOIN course_knowledge b ON a.kp_id = b.kp_id AND a.course_id < b.course_id GROUP BY a.course_id, b.course_id ORDER BY shared_count DESC LIMIT 10")
        result = db.session.execute(sql).fetchall()
        items = []
        for r in result:
            ca, cb = Course.query.get(r.course_id_a), Course.query.get(r.course_id_b)
            items.append({'course_a': ca.name if ca else '', 'course_b': cb.name if cb else '', 'shared_count': r.shared_count})
        return jsonify({'success': True, 'data': items})

    @app.route('/api/analysis/rating-stats')
    def api_analysis_rating_stats():
        result = db.session.query(Course.id, Course.name, func.avg(Rating.score).label('avg_score'), func.count(Rating.id).label('rating_count'))\
            .join(Rating, Course.id == Rating.course_id).group_by(Course.id).order_by(func.avg(Rating.score).desc()).all()
        return jsonify({'success': True, 'data': [{'id': r.id, 'name': r.name, 'avg_score': round(r.avg_score, 2) if r.avg_score else 0, 'rating_count': r.rating_count} for r in result]})

    @app.route('/api/analysis/dimension-distribution')
    def api_analysis_dimension_distribution():
        result = db.session.query(KnowledgePoint.dimension, func.count(KnowledgePoint.id).label('count')).filter(KnowledgePoint.dimension != '').group_by(KnowledgePoint.dimension).all()
        return jsonify({'success': True, 'data': [{'dimension': r.dimension, 'count': r.count} for r in result]})

    @app.route('/api/analysis/difficulty-ranking')
    def api_difficulty_ranking():
        """课程难度综合排行（考试难度+作业量）"""
        courses = MultiDimRating.query.with_entities(MultiDimRating.course_id,
            func.avg(MultiDimRating.exam_difficulty + MultiDimRating.workload).label('difficulty_score'),
            func.avg(MultiDimRating.exam_difficulty).label('exam'),
            func.avg(MultiDimRating.workload).label('work'),
            func.count(MultiDimRating.id).label('cnt'))\
            .group_by(MultiDimRating.course_id).order_by(func.avg(MultiDimRating.exam_difficulty + MultiDimRating.workload).desc()).all()
        items = []
        for r in courses:
            c = Course.query.get(r.course_id)
            items.append({'id': r.course_id, 'name': c.name if c else '', 'difficulty_score': round(r.difficulty_score, 1), 'exam_difficulty': round(r.exam, 1), 'workload': round(r.work, 1), 'rating_count': r.cnt})
        return jsonify({'success': True, 'data': items})

    @app.route('/api/analysis/summary-stats')
    def api_summary_stats():
        return jsonify({'success': True, 'data': {
            'total_courses': Course.query.count(), 'total_knowledge_points': KnowledgePoint.query.count(),
            'total_relations': CourseKnowledge.query.count(), 'total_reviews': Review.query.count() + Annotation.query.count(),
            'total_ratings': Rating.query.count(), 'total_users': User.query.count()
        }})

    @app.route('/api/analysis/hot-knowledge-points')
    def api_hot_knowledge_points():
        """本周热门知识点（按标注数排序）"""
        result = db.session.query(KnowledgePoint.id, KnowledgePoint.name, KnowledgePoint.dimension, KnowledgePoint.description,
            func.count(Annotation.id).label('ann_count'))\
            .outerjoin(Annotation, KnowledgePoint.id == Annotation.kp_id)\
            .group_by(KnowledgePoint.id).order_by(func.count(Annotation.id).desc()).limit(6).all()
        return jsonify({'success': True, 'data': [{'id': r.id, 'name': r.name, 'dimension': r.dimension, 'description': r.description, 'count': r.ann_count} for r in result]})

    @app.route('/api/community/feed')
    def api_community_feed():
        """社区动态流"""
        items = []
        reviews = Review.query.order_by(Review.created_at.desc()).limit(5).all()
        for r in reviews:
            c = Course.query.get(r.course_id)
            items.append({'type': 'review', 'user': r.user.display_name if r.user else '', 'content': r.content[:80]+'...', 'course': c.name if c else '', 'time': r.created_at.strftime('%m-%d %H:%M') if r.created_at else ''})
        annotations = Annotation.query.filter_by(is_private=False).order_by(Annotation.created_at.desc()).limit(5).all()
        for a in annotations:
            kp = KnowledgePoint.query.get(a.kp_id)
            items.append({'type': 'annotation', 'user': a.user.display_name if a.user else '', 'content': a.content[:80]+'...', 'kp': kp.name if kp else '', 'time': a.created_at.strftime('%m-%d %H:%M') if a.created_at else ''})
        items.sort(key=lambda x: x.get('time', ''), reverse=True)
        return jsonify({'success': True, 'feed': items[:10]})

    # ===================== 社交功能 API =====================
    @app.route('/api/user/avatar', methods=['POST'])
    @login_required
    def api_upload_avatar():
        data = request.get_json()
        avatar_data = data.get('avatar', '')
        if not avatar_data:
            return jsonify({'success': False, 'message': '请选择头像图片'}), 400
        current_user.avatar = avatar_data[:500000]  # 限制大小
        db.session.commit()
        return jsonify({'success': True, 'message': '头像更新成功', 'avatar': current_user.avatar})

    @app.route('/api/review/<int:review_id>/like', methods=['POST'])
    @login_required
    def api_toggle_review_like(review_id):
        existing = ReviewLike.query.filter_by(user_id=current_user.id, review_id=review_id).first()
        review = Review.query.get_or_404(review_id)
        if existing:
            db.session.delete(existing)
            review.like_count = max(0, review.like_count - 1)
            liked = False
        else:
            db.session.add(ReviewLike(user_id=current_user.id, review_id=review_id))
            review.like_count = (review.like_count or 0) + 1
            liked = True
        db.session.commit()
        return jsonify({'success': True, 'liked': liked, 'count': review.like_count})

    @app.route('/api/annotation/<int:annotation_id>/like', methods=['POST'])
    @login_required
    def api_toggle_annotation_like(annotation_id):
        existing = AnnotationLike.query.filter_by(user_id=current_user.id, annotation_id=annotation_id).first()
        ann = Annotation.query.get_or_404(annotation_id)
        if existing:
            db.session.delete(existing)
            ann.like_count = max(0, ann.like_count - 1)
            liked = False
        else:
            db.session.add(AnnotationLike(user_id=current_user.id, annotation_id=annotation_id))
            ann.like_count = (ann.like_count or 0) + 1
            liked = True
        db.session.commit()
        return jsonify({'success': True, 'liked': liked, 'count': ann.like_count})

    # ===================== 点评编辑/删除 =====================
    @app.route('/api/review/<int:review_id>', methods=['PUT'])
    @login_required
    def api_edit_review(review_id):
        review = Review.query.get_or_404(review_id)
        if review.user_id != current_user.id:
            return jsonify({'success': False, 'message': '只能编辑自己的点评'}), 403
        data = request.get_json()
        score = data.get('score')
        content = data.get('content', '').strip()
        if score:
            rating = Rating.query.filter_by(user_id=current_user.id, course_id=review.course_id).first()
            if rating:
                rating.score = int(score)
            else:
                db.session.add(Rating(user_id=current_user.id, course_id=review.course_id, score=int(score)))
        if content:
            review.content = content
        db.session.commit()
        return jsonify({'success': True, 'message': '点评已更新'})

    @app.route('/api/review/<int:review_id>', methods=['DELETE'])
    @login_required
    def api_delete_review(review_id):
        review = Review.query.get_or_404(review_id)
        if review.user_id != current_user.id:
            return jsonify({'success': False, 'message': '只能删除自己的点评'}), 403
        db.session.delete(review)
        db.session.commit()
        return jsonify({'success': True, 'message': '点评已删除'})

    # ===================== 图谱搜索 =====================
    @app.route('/api/graph/search')
    def api_graph_search():
        q = request.args.get('q', '').strip()
        if not q:
            return jsonify({'success': False, 'results': []})
        driver = get_neo4j()
        results = []
        if driver:
            try:
                with driver.session() as session:
                    r = session.run(
                        "MATCH (n) WHERE toLower(n.name) CONTAINS toLower($q) RETURN id(n) AS id, labels(n) AS labels, n.name AS name LIMIT 10",
                        q=q
                    )
                    for rec in r:
                        results.append({'id': rec['id'], 'label': rec['name'], 'type': rec['labels'][0] if rec['labels'] else ''})
                    return jsonify({'success': True, 'results': results})
            except:
                pass
        # MySQL fallback
        courses = Course.query.filter(Course.name.contains(q)).limit(5).all()
        kps = KnowledgePoint.query.filter(KnowledgePoint.name.contains(q)).limit(5).all()
        # 返回 node_id 需要与 _graph_from_mysql 的计算一致
        for c in courses:
            results.append({'id': c.id, 'label': c.name, 'type': 'Course'})
        for kp in kps:
            results.append({'id': Course.query.count() + kp.id, 'label': kp.name, 'type': 'KnowledgePoint'})
        return jsonify({'success': True, 'results': results[:10]})

    @app.route('/api/leaderboard')
    def api_leaderboard():
        """用户排行榜（按评分+点评+学分综合）"""
        users = User.query.all()
        result = []
        for u in users:
            rc = Rating.query.filter_by(user_id=u.id).count()
            rvc = Review.query.filter_by(user_id=u.id).count()
            ac = Annotation.query.filter_by(user_id=u.id).count()
            # 答题正确数
            qc = QuizAttempt.query.filter_by(user_id=u.id, correct=True).count()
            score = rc * 2 + rvc * 3 + ac * 5 + qc * 10
            result.append({
                'id': u.id, 'username': u.username, 'display_name': u.display_name,
                'avatar': u.avatar, 'title': u.title or '学徒',
                'ratings': rc, 'reviews': rvc, 'annotations': ac,
                'quiz_correct': qc, 'score': score
            })
        result.sort(key=lambda x: x['score'], reverse=True)
        return jsonify({'success': True, 'leaderboard': result})

    @app.route('/api/messages', methods=['GET', 'POST'])
    def api_messages():
        if request.method == 'GET':
            msgs = Message.query.order_by(Message.created_at.desc()).limit(50).all()
            return jsonify({'success': True, 'messages': [m.to_dict() for m in msgs]})
        else:
            data = request.get_json()
            content = data.get('content', '').strip()
            if not content:
                return jsonify({'success': False, 'message': '内容不能为空'}), 400
            username = '游客'
            user_id = None
            if current_user.is_authenticated:
                username = current_user.display_name or current_user.username
                user_id = current_user.id
            msg = Message(user_id=user_id, username=username, content=content)
            db.session.add(msg)
            db.session.commit()
            return jsonify({'success': True, 'message': msg.to_dict()})

    @app.route('/api/messages/<int:msg_id>', methods=['PUT', 'DELETE'])
    def api_message_crud(msg_id):
        msg = Message.query.get_or_404(msg_id)
        if not current_user.is_authenticated or (current_user.id != msg.user_id and current_user.username != msg.username):
            return jsonify({'success': False, 'message': '无权操作'}), 403
        if request.method == 'DELETE':
            db.session.delete(msg)
            db.session.commit()
            return jsonify({'success': True, 'message': '已删除'})
        data = request.get_json()
        content = data.get('content', '').strip()
        if content:
            msg.content = content
        db.session.commit()
        return jsonify({'success': True, 'message': msg.to_dict()})

    @app.route('/api/messages/<int:msg_id>/like', methods=['POST'])
    def api_message_like(msg_id):
        msg = Message.query.get_or_404(msg_id)
        msg.likes = (msg.likes or 0) + 1
        db.session.commit()
        return jsonify({'success': True, 'likes': msg.likes})

    @app.route('/api/quiz/best-score')
    @login_required
    def api_quiz_best_score():
        """用户最佳答题成绩"""
        from sqlalchemy import func
        # 按session分组统计（简单方案：按时间窗口分组）
        attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.created_at.desc()).all()
        # 计算总正确数
        total = len(attempts)
        correct = sum(1 for a in attempts if a.correct)
        return jsonify({'success': True, 'data': {'total': total, 'correct': correct, 'rate': round(correct/total*100,1) if total else 0}})

    @app.route('/api/user/compare/<int:user_id>')
    @login_required
    def api_compare_user(user_id):
        """与另一个用户比较学分"""
        other = User.query.get_or_404(user_id)
        # 本用户学分
        my_ratings = Rating.query.filter_by(user_id=current_user.id).count()
        my_reviews = Review.query.filter_by(user_id=current_user.id).count()
        my_annotations = Annotation.query.filter_by(user_id=current_user.id).count()
        my_credits = sum(c.credit for c in Course.query.all() if Rating.query.filter_by(user_id=current_user.id, course_id=c.id).first())
        # 对方学分
        other_ratings = Rating.query.filter_by(user_id=other.id).count()
        other_reviews = Review.query.filter_by(user_id=other.id).count()
        other_annotations = Annotation.query.filter_by(user_id=other.id).count()
        other_credits = sum(c.credit for c in Course.query.all() if Rating.query.filter_by(user_id=other.id, course_id=c.id).first())
        return jsonify({'success': True, 'data': {
            'me': {'name': current_user.display_name or current_user.username, 'ratings': my_ratings, 'reviews': my_reviews, 'annotations': my_annotations, 'credits': round(my_credits,1)},
            'other': {'id': other.id, 'name': other.display_name or other.username, 'ratings': other_ratings, 'reviews': other_reviews, 'annotations': other_annotations, 'credits': round(other_credits,1)}
        }})

    # ===================== 初始化 =====================
    with app.app_context():
        try:
            db.create_all()
            print("[OK] 数据库表已创建")
        except Exception as e:
            print(f"[WARN] 数据库初始化出错: {e}")

    return app


if __name__ == '__main__':
    application = create_app()
    application.run(host='0.0.0.0', port=5001, debug=True)