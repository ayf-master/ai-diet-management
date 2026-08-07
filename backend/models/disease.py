from app import db


class Disease(db.Model):
    __tablename__ = 'disease'

    disease_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    disease_name = db.Column(db.String(100), nullable=False)
    forbid_desc = db.Column(db.Text, nullable=False)
    # 结构化禁忌规则：逗号分隔的关键词 + JSON 营养阈值，供健康判定服务使用
    forbid_keywords = db.Column(db.Text, nullable=True)
    forbid_rules = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'disease_id': self.disease_id,
            'disease_name': self.disease_name,
            'forbid_desc': self.forbid_desc,
            'forbid_keywords': self.forbid_keywords,
            'forbid_rules': self.forbid_rules,
            'created_at': str(self.created_at) if self.created_at else None,
        }
