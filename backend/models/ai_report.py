from app import db


class AiReport(db.Model):
    __tablename__ = 'ai_report'

    report_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_cal = db.Column(db.Integer, nullable=False)
    avg_daily_cal = db.Column(db.Integer)
    weight_diff = db.Column(db.Float, nullable=False)
    ai_comment = db.Column(db.Text, nullable=False)
    suggest = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'report_id': self.report_id,
            'user_id': self.user_id,
            'start_date': str(self.start_date) if self.start_date else None,
            'end_date': str(self.end_date) if self.end_date else None,
            'total_cal': self.total_cal,
            'avg_daily_cal': self.avg_daily_cal,
            'weight_diff': self.weight_diff,
            'ai_comment': self.ai_comment,
            'suggest': self.suggest,
            'created_at': str(self.created_at) if self.created_at else None,
        }
