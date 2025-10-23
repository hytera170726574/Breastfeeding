from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    default_baby_id = db.Column(db.Integer, nullable=True)  # 默认婴儿ID

    # 关系
    babies = db.relationship('Baby', backref='parent', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Baby(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 设置为自增主键
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=True)  # 性别: 'male', 'female', 'other'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # 关系
    feedings = db.relationship('Feeding', backref='baby', lazy=True)
    diapers = db.relationship('Diaper', backref='baby', lazy=True)
    sleeps = db.relationship('Sleep', backref='baby', lazy=True)
    measurements = db.relationship('Measurement', backref='baby', lazy=True, cascade='all, delete-orphan')

    # def to_dict(self):
    #     return {
    #         'id': self.id,
    #         'name': self.name,
    #         'user_id':self.user_id,
    #         'gender':self.gender,
    #         'birth_date':self.birth_date,
    #         # ... 其他字段 ...
    #     }
    def __repr__(self):
        return f'<Baby {self.name}>'

class Measurement(db.Model):
    """婴儿体重和身长记录"""
    id = db.Column(db.Integer, primary_key=True)
    weight_kg = db.Column(db.Float, nullable=True)  # 体重(kg)
    height_cm = db.Column(db.Float, nullable=True)  # 身长(cm)
    measurement_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键
    baby_id = db.Column(db.Integer, db.ForeignKey('baby.id'), nullable=False)

    def __repr__(self):
        return f'<Measurement Baby:{self.baby_id} Date:{self.measurement_date}>'

class Feeding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feeding_type = db.Column(db.String(20), nullable=False)  # 'breast' 或 'bottle'
    start_time = db.Column(db.DateTime, nullable=True)  # 母乳喂养开始时间
    end_time = db.Column(db.DateTime, nullable=True)    # 母乳喂养结束时间
    bottle_ml = db.Column(db.Integer, default=0)        # 奶瓶喂养量(ml)
    breast_ml = db.Column(db.Integer, default=0)        # 估算的母乳喂养量(ml)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键
    baby_id = db.Column(db.Integer, db.ForeignKey('baby.id'), nullable=False)

    @property
    def duration_minutes(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0

    @property
    def total_ml(self):
        """总喂养量（母乳估算量 + 奶瓶量）"""
        return self.breast_ml + self.bottle_ml

    def estimate_breast_ml(self):
        """根据喂养时长估算母乳喂养量（假设每分钟约10ml）"""
        if self.feeding_type == 'breast' and self.duration_minutes > 0:
            # 简单估算：每分钟10ml
            self.breast_ml = int(self.duration_minutes * 10)
        return self.breast_ml

    def __repr__(self):
        return f'<Feeding {self.id}>'

class Diaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    diaper_type = db.Column(db.String(20), nullable=False)  # 'wet' 或 'dirty'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键
    baby_id = db.Column(db.Integer, db.ForeignKey('baby.id'), nullable=False)

    def __repr__(self):
        return f'<Diaper {self.diaper_type}>'

class Sleep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键
    baby_id = db.Column(db.Integer, db.ForeignKey('baby.id'), nullable=False)

    @property
    def duration_minutes(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0

    def __repr__(self):
        return f'<Sleep {self.id}>'

class MilkInventory(db.Model):
    """每个婴儿的母乳余量（毫升）"""
    id = db.Column(db.Integer, primary_key=True)
    baby_id = db.Column(db.Integer, db.ForeignKey('baby.id'), nullable=False, unique=True)
    remaining_ml = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MilkInventory baby={self.baby_id} remaining={self.remaining_ml}ml>'

class MilkPump(db.Model):
    """吸奶记录（泵奶）"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    volume_ml = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    baby_id = db.Column(db.Integer, db.ForeignKey('baby.id'), nullable=False)

    def __repr__(self):
        return f'<MilkPump {self.id} {self.volume_ml}ml>'

class DirectBreastfeeding(db.Model):
    """亲喂记录（开始/结束）"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)
    side = db.Column(db.String(10))  # 可选: left/right/both
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    baby_id = db.Column(db.Integer, db.ForeignKey('baby.id'), nullable=False)

    @property
    def duration_minutes(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0

    def __repr__(self):
        return f'<DirectBreastfeeding {self.id}>'

class BottleBreastFeeding(db.Model):
    """瓶喂母乳记录"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    volume_ml = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    baby_id = db.Column(db.Integer, db.ForeignKey('baby.id'), nullable=False)

    def __repr__(self):
        return f'<BottleBreastFeeding {self.id} {self.volume_ml}ml>'

class FormulaFeeding(db.Model):
    """配方奶粉喂养记录"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    volume_ml = db.Column(db.Integer, nullable=False)
    brand = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    baby_id = db.Column(db.Integer, db.ForeignKey('baby.id'), nullable=False)

    def __repr__(self):
        return f'<FormulaFeeding {self.id} {self.volume_ml}ml>'