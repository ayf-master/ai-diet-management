from app import db


class UserGoal(db.Model):
    __tablename__ = 'user_goal'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    goal = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal': self.goal,
            'created_at': str(self.created_at) if self.created_at else None,
        }
