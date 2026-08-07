from app import db


class UserDisease(db.Model):
    __tablename__ = 'user_disease'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.disease_id'), nullable=False)
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('user_id', 'disease_id', name='uk_user_disease'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'disease_id': self.disease_id,
            'remark': self.remark,
            'created_at': str(self.created_at) if self.created_at else None,
        }
