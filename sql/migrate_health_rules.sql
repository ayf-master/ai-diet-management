-- 疾病管理健康判定：为已有数据库升级 disease 表
-- 项目用 db.create_all() 启动，它只建缺失的表、不会修改已存在的表，
-- 所以老库需要手动执行以下 ALTER 来新增两列（只需跑一次）。

ALTER TABLE disease
  ADD COLUMN forbid_keywords TEXT DEFAULT NULL COMMENT '禁忌关键词(逗号分隔)',
  ADD COLUMN forbid_rules  TEXT DEFAULT NULL COMMENT '营养阈值JSON,如{"max_sugar":5,"max_sodium":200}';

-- 给已存在的示例疾病补上结构化规则（与 seed.sql 保持一致）
UPDATE disease SET forbid_keywords='糖,蜂蜜,蔗糖,葡萄糖,精制碳水,白米饭,白面包,甜点',
                   forbid_rules='{"max_sugar":5,"max_carbohydrate":30}' WHERE disease_name='糖尿病';
UPDATE disease SET forbid_keywords='盐,咸菜,腌制,酱菜,榨菜,火腿,培根',
                   forbid_rules='{"max_sodium":200}' WHERE disease_name='高血压';
UPDATE disease SET forbid_keywords='油炸,动物内脏,肥肉,猪油,黄油,奶油',
                   forbid_rules='{"max_fat":15}' WHERE disease_name='高血脂';
UPDATE disease SET forbid_keywords='动物内脏,海鲜,浓汤,啤酒,肉汤,沙丁鱼',
                   forbid_rules=NULL WHERE disease_name='痛风';
UPDATE disease SET forbid_keywords='辣椒,花椒,生冷,冰,辛辣,酒精',
                   forbid_rules=NULL WHERE disease_name='胃病';
