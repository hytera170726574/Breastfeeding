# 哺乳期母亲喂养记录系统 - 后端API

这是一个基于Flask的后端API系统，用于记录哺乳期母亲的喂养过程，包括婴儿信息、喂养记录、大小便记录、睡眠记录和数据统计功能。

## 功能特性

1. **用户认证**：注册、登录功能
2. **婴儿管理**：创建、更新、删除婴儿信息（限制免费用户最多2个婴儿）
3. **喂养记录**：支持母乳喂养和奶粉喂养记录
4. **大小便记录**：记录婴儿大小便情况
5. **睡眠记录**：记录婴儿睡眠开始和结束时间
6. **生长发育**：记录婴儿体重和身长
7. **数据统计**：提供图表数据用于可视化展示

## 技术栈

- Flask
- SQLAlchemy (ORM)
- JWT (认证)
- SQLite (默认数据库)

## 安装步骤

1. 克隆项目：
   ```
   git clone <项目地址>
   cd newRecord
   ```

2. 创建虚拟环境：
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

4. 设置环境变量（可选）：
   ```
   cp .env.example .env
   # 编辑 .env 文件中的配置
   ```

5. 运行应用：
   ```
   python run.py
   ```

## API接口说明

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录

### 婴儿管理接口
- `POST /api/baby/` - 创建婴儿
- `GET /api/baby/` - 获取所有婴儿
- `GET /api/baby/<baby_id>` - 获取指定婴儿
- `PUT /api/baby/<baby_id>` - 更新婴儿信息
- `DELETE /api/baby/<baby_id>` - 删除婴儿
- `POST /api/baby/<baby_id>/set-default` - 设置默认婴儿
- `GET /api/baby/default` - 获取默认婴儿

### 喂养记录接口
- `POST /api/feeding/` - 创建喂养记录
- `POST /api/feeding/bottle` - 创建奶粉喂养记录
- `POST /api/feeding/breast/start` - 开始母乳喂养
- `PUT /api/feeding/breast/<feeding_id>/end` - 结束母乳喂养
- `GET /api/feeding/<baby_id>` - 获取婴儿喂养记录
- `GET /api/feeding/default-baby` - 获取默认婴儿喂养记录

### 大小便记录接口
- `POST /api/diaper/` - 创建大小便记录
- `GET /api/diaper/<baby_id>` - 获取婴儿大小便记录
- `GET /api/diaper/default-baby` - 获取默认婴儿大小便记录

### 睡眠记录接口
- `POST /api/sleep/start` - 开始睡眠记录
- `PUT /api/sleep/<sleep_id>/end` - 结束睡眠记录
- `GET /api/sleep/<baby_id>` - 获取婴儿睡眠记录
- `GET /api/sleep/default-baby` - 获取默认婴儿睡眠记录

### 生长发育记录接口
- `POST /api/measurement/` - 创建测量记录
- `GET /api/measurement/<baby_id>` - 获取婴儿测量记录
- `GET /api/measurement/default-baby` - 获取默认婴儿测量记录

### 统计接口
- `POST /api/stats/feeding/daily` - 获取每日喂养统计
- `POST /api/stats/feeding/detail` - 获取喂养详细记录
- `POST /api/stats/diaper/daily` - 获取每日大小便统计
- `POST /api/stats/sleep/daily` - 获取每日睡眠统计
- `POST /api/stats/sleep/detail` - 获取睡眠详细记录
- `POST /api/stats/growth` - 获取生长发育统计

## 数据模型

### User（用户）
- id: Integer (主键)
- username: String (用户名)
- email: String (邮箱)
- password_hash: String (密码哈希)
- default_baby_id: Integer (默认婴儿ID)

### Baby（婴儿）
- id: Integer (主键)
- name: String (姓名)
- birth_date: Date (出生日期)
- gender: String (性别)
- user_id: Integer (外键，关联User)

### Feeding（喂养记录）
- id: Integer (主键)
- feeding_type: String (喂养类型：'breast'或'bottle')
- start_time: DateTime (开始时间)
- end_time: DateTime (结束时间)
- bottle_ml: Integer (奶粉量ml)
- breast_ml: Integer (母乳量ml)
- baby_id: Integer (外键，关联Baby)

### Diaper（大小便记录）
- id: Integer (主键)
- diaper_type: String (类型：'wet'或'dirty')
- timestamp: DateTime (时间戳)
- baby_id: Integer (外键，关联Baby)

### Sleep（睡眠记录）
- id: Integer (主键)
- start_time: DateTime (开始时间)
- end_time: DateTime (结束时间)
- baby_id: Integer (外键，关联Baby)

### Measurement（生长发育记录）
- id: Integer (主键)
- weight_kg: Float (体重kg)
- height_cm: Float (身长cm)
- measurement_date: Date (测量日期)
- baby_id: Integer (外键，关联Baby)

## 开发说明

1. 项目结构：
   ```
   app/
   ├── __init__.py          # 应用工厂
   ├── models/              # 数据模型
   ├── routes/              # API路由
   ├── schemas/             # 数据验证模式
   ├── utils/               # 工具函数
   ├── config.py           # 配置文件
   run.py                  # 应用入口
   requirements.txt        # 依赖列表
   ```

2. 数据库迁移：
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

## 测试

运行测试脚本：
```
python test_api.py
```

## 许可证

MIT License