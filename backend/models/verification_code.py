"""验证码模型"""
from datetime import datetime, timedelta
from app import db


class VerificationCode(db.Model):
    __tablename__ = 'verification_code'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    @staticmethod
    def generate(email, minutes=10):
        """生成6位验证码并保存"""
        import random
        code = f'{random.randint(100000, 999999)}'
        now = datetime.utcnow()
        vc = VerificationCode(
            email=email,
            code=code,
            created_at=now,
            expires_at=now + timedelta(minutes=minutes),
        )
        db.session.add(vc)
        db.session.commit()
        return code

    @staticmethod
    def verify(email, code):
        """验证验证码（只验证最近10分钟内未使用的）"""
        vc = VerificationCode.query.filter_by(
            email=email, code=code, used=False
        ).order_by(VerificationCode.created_at.desc()).first()
        if not vc:
            return False
        if datetime.utcnow() > vc.expires_at:
            return False
        vc.used = True
        db.session.commit()
        return True
