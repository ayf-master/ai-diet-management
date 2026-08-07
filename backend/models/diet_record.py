from app import db


class DietRecord(db.Model):
    __tablename__ = 'diet_record'

    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    meal_type_id = db.Column(db.Integer, db.ForeignKey('meal_type_def.type_id'), nullable=False)
    eat_date = db.Column(db.Date, nullable=False)
    eat_time = db.Column(db.Time)
    total_cal = db.Column(db.Integer, nullable=False, default=0)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    meal_type = db.relationship('MealTypeDef', lazy='joined')
    details = db.relationship('DietRecordDetail', backref='diet_record', lazy='joined',
                              cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'record_id': self.record_id,
            'user_id': self.user_id,
            'meal_type': self.meal_type.type_name if self.meal_type else None,
            'eat_date': str(self.eat_date),
            'eat_time': str(self.eat_time) if self.eat_time else None,
            'total_cal': self.total_cal,
            'note': self.note,
            'details': [d.to_dict() for d in self.details],
            'created_at': str(self.created_at) if self.created_at else None,
        }
