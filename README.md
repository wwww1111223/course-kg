# 课程知识图谱社区系统

南京大学信息管理学院 · 信息组织大作业

## 小组成员
- 王娇（251820284）
- 张姝欣（251820085）

## 数据来源
- 29门课程：南京大学信息管理学院 2025 级教学计划
- 174个知识点：《汉语主题词表》主题词，覆盖文化、机构、个人、计算四维
- 分类号：依据《中国图书馆分类法》（中图法）

## 功能概览
| 页面 | 功能 |
|------|------|
| 首页 | 课程网格、四维筛选、热门知识点、社区动态 |
| 课程详情 | 知识点标注、多维评分、点评、问答区、课程前置关联、点赞 |
| 知识图谱 | vis-network 力导向图可视化、搜索 |
| 数据洞察 | Chart.js 图表（知识点度数、维度分布、评分排行、难度排行） |
| 学分计算器 | 勾选课程统计通修/学科/专业学分 |
| 答题闯关 | 随机知识点选择题、计分、连击 |
| 藏书阁 | 书本式课程陈列、收藏 |
| 排行榜 | 用户综合积分排名、学分PK |
| 个人主页 | 头像上传、成就徽章、评分/点评/标注管理 |

## 运行步骤

### 方式一：直接运行（SQLite，推荐）
```bash
cd backend
pip install flask flask-login flask-cors flask-sqlalchemy werkzeug
python3 app.py
```
浏览器打开 http://localhost:5001

### 方式二：使用 MySQL
1. 执行 `mysql/schema.sql` 创建数据库和表
2. 修改 `backend/config.py` 中 `DB_TYPE = 'mysql'` 并配置数据库连接
3. 运行 `python3 init_db.py` 初始化数据

### 方式三：使用 Neo4j（可选）
1. 启动 Neo4j 数据库
2. 执行 `neo4j/init.cypher` 创建图谱节点和关系
3. 修改 `backend/config.py` 中 Neo4j 连接配置
4. 系统会自动使用 Neo4j 查询，不可用时降级为 SQL 查询

### 测试账号
| 用户名 | 密码 | 说明 |
|--------|------|------|
| wangjiao | 123456 | 王娇 |
| zhangshuxin | 123456 | 张姝欣 |
| litongxue | 123456 | 李同学 |

## 技术栈
- 后端：Python Flask 3.1.3
- 数据库：SQLite（开发）/ MySQL（生产）+ Neo4j（图查询，可选）
- 前端：HTML + CSS + JavaScript（原生）
- 可视化：vis-network（知识图谱）、Chart.js（分析图表）
- 用户认证：Flask-Login

## 本体设计

### 类（Class）
1. **Course（课程）** — 属性：name, credit, clc_number, category, department
2. **KnowledgePoint（知识点）** — 属性：name, description, dimension, difficulty
3. **User（用户）** — 属性：username, display_name, title

### 关系（Relationship）
- Course —[:HAS_KNOWLEDGE]→ KnowledgePoint（课程包含知识点）
- Course —[:PREREQUISITE_OF]→ Course（课程前置依赖）
- Course —[:SHARED_WITH]→ Course（课程间共享知识点）

### 四维分类体系
- 文化维度：学术规范、信息伦理、文化传统等
- 机构维度：政策法规、组织管理、制度体系等
- 个人维度：思维能力、学习策略、实践技能等
- 计算维度：算法原理、数据结构、编程技术等

## 分工
- 王娇：需求分析、本体设计、后端开发、数据库设计
- 张姝欣：前端界面设计、知识图谱可视化、数据初始化
