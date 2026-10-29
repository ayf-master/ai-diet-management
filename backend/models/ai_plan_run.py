from app import db


class AiPlanRun(db.Model):
    """每次可信 AI 规划的可观测指标；失败也留痕，便于对比和排查。"""

    __tablename__ = 'ai_plan_run'

    run_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('ai_diet_plan.plan_id'))
    status = db.Column(db.String(20), nullable=False, default='failed')
    model = db.Column(db.String(50))
    source = db.Column(db.String(20))           # model / mock / fallback
    candidate_count = db.Column(db.Integer, nullable=False, default=0)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    parse_ok = db.Column(db.Boolean, nullable=False, default=False)
    schema_ok = db.Column(db.Boolean, nullable=False, default=False)
    invalid_id_count = db.Column(db.Integer, nullable=False, default=0)
    repaired_count = db.Column(db.Integer, nullable=False, default=0)
    danger_count = db.Column(db.Integer, nullable=False, default=0)
    target_cal = db.Column(db.Integer)
    verified_cal = db.Column(db.Integer)
    calorie_error_pct = db.Column(db.Float)
    protein_g = db.Column(db.Float)
    fallback_used = db.Column(db.Boolean, nullable=False, default=False)
    latency_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'run_id': self.run_id,
            'user_id': self.user_id,
            'plan_id': self.plan_id,
            'status': self.status,
            'model': self.model,
            'source': self.source,
            'candidate_count': self.candidate_count,
            'attempts': self.attempts,
            'parse_ok': self.parse_ok,
            'schema_ok': self.schema_ok,
            'invalid_id_count': self.invalid_id_count,
            'repaired_count': self.repaired_count,
            'danger_count': self.danger_count,
            'target_cal': self.target_cal,
            'verified_cal': self.verified_cal,
            'calorie_error_pct': self.calorie_error_pct,
            'protein_g': self.protein_g,
            'fallback_used': self.fallback_used,
            'latency_ms': self.latency_ms,
            'created_at': str(self.created_at) if self.created_at else None,
        }
