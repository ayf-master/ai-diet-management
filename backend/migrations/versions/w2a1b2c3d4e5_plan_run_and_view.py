"""W2 数据表与视图迁移：closed-set 规划所需的可观测指标 + 食谱营养视图。"""
from alembic import op
import sqlalchemy as sa


revision = 'w2a1b2c3d4e5'
down_revision = 'bf1357b46304'
branch_labels = None
depends_on = None

_RECIPE_NUTRITION_VIEW_SQL = """
CREATE OR REPLACE VIEW v_recipe_nutrition AS
SELECT
    r.recipe_id,
    r.recipe_name,
    r.type,
    r.suitable_goals,
    r.user_id,
    r.cook_method,
    r.total_weight,
    r.total_calorie,
    r.base_calorie,
    r.added_calorie,
    r.oil_g,
    r.sauce_g,
    COALESCE(SUM(n.calorie * rf.weight / 100.0), 0) AS ingredient_calorie,
    COALESCE(SUM(n.protein * rf.weight / 100.0), 0) AS protein_g,
    COALESCE(SUM(n.fat * rf.weight / 100.0), 0) AS fat_g,
    COALESCE(SUM(n.carbohydrate * rf.weight / 100.0), 0) AS carbohydrate_g,
    COALESCE(SUM(n.fiber * rf.weight / 100.0), 0) AS fiber_g,
    COALESCE(SUM(n.sugar * rf.weight / 100.0), 0) AS sugar_g,
    COALESCE(SUM(n.sodium * rf.weight / 100.0), 0) AS sodium_mg,
    COUNT(rf.food_id) AS ingredient_count,
    CASE WHEN r.total_weight > 0
         THEN ROUND(r.total_calorie * 100.0 / r.total_weight, 1)
         ELSE 0 END AS calorie_per_100g,
    CASE WHEN r.total_weight > 0
         THEN ROUND(COALESCE(SUM(n.protein * rf.weight / 100.0), 0) * 100.0 / r.total_weight, 1)
         ELSE 0 END AS protein_per_100g
FROM recipe r
LEFT JOIN recipe_food rf ON rf.recipe_id = r.recipe_id
LEFT JOIN nutrition n ON n.food_id = rf.food_id
GROUP BY
    r.recipe_id, r.recipe_name, r.type, r.suitable_goals, r.user_id,
    r.cook_method, r.total_weight, r.total_calorie, r.base_calorie,
    r.added_calorie, r.oil_g, r.sauce_g
"""


def upgrade():
    op.create_table(
        'ai_plan_run',
        sa.Column('run_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=True),
        sa.Column('candidate_count', sa.Integer(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('parse_ok', sa.Boolean(), nullable=False),
        sa.Column('schema_ok', sa.Boolean(), nullable=False),
        sa.Column('invalid_id_count', sa.Integer(), nullable=False),
        sa.Column('repaired_count', sa.Integer(), nullable=False),
        sa.Column('danger_count', sa.Integer(), nullable=False),
        sa.Column('target_cal', sa.Integer(), nullable=True),
        sa.Column('verified_cal', sa.Integer(), nullable=True),
        sa.Column('calorie_error_pct', sa.Float(), nullable=True),
        sa.Column('protein_g', sa.Float(), nullable=True),
        sa.Column('fallback_used', sa.Boolean(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['ai_diet_plan.plan_id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id']),
        sa.PrimaryKeyConstraint('run_id'),
    )
    op.execute('DROP VIEW IF EXISTS v_recipe_nutrition')
    op.execute(_RECIPE_NUTRITION_VIEW_SQL)


def downgrade():
    op.execute('DROP VIEW IF EXISTS v_recipe_nutrition')
    op.drop_table('ai_plan_run')
