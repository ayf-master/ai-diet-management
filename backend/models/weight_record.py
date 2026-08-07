from app import db


class WeightRecord(db.Model):
    __tablename__ = 'weight_record'

    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    body_fat_rate = db.Column(db.Float)
    measure_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'record_id': self.record_id,
            'user_id': self.user_id,
            'weight': self.weight,
            'body_fat_rate': self.body_fat_rate,
            'measure_date': str(self.measure_date) if self.measure_date else None,
            'note': self.note,
            'created_at': str(self.created_at) if self.created_at else None,
        }
