-- AI辅助减脂饮食管理系统 - 数据库建表脚本 (MySQL 8.0+)

CREATE DATABASE IF NOT EXISTS diet_management
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE diet_management;

-- 0.数字辅助表（用于存储过程生成日期序列等）
DROP TABLE IF EXISTS numbers;
CREATE TABLE numbers (
    n INT PRIMARY KEY COMMENT '数字'
) ENGINE=InnoDB;

-- 插入 0~9999
SET @@cte_max_recursion_depth = 10000;
INSERT INTO numbers (n)
WITH RECURSIVE cte AS (
    SELECT 0 AS n
    UNION ALL
    SELECT n + 1 FROM cte WHERE n < 9999
)
SELECT n FROM cte;

-- 1.用户表
DROP TABLE IF EXISTS user;
CREATE TABLE user (
    user_id          INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '用户主键',
    account          VARCHAR(50)   NOT NULL UNIQUE              COMMENT '登录账号',
    password         VARCHAR(255)  NOT NULL                     COMMENT '登录密码（加密存储）',
    nickname         VARCHAR(50)   NOT NULL                     COMMENT '用户昵称',
    email            VARCHAR(100)  DEFAULT NULL                 COMMENT '联系邮箱',
    age              INT           NOT NULL                     COMMENT '年龄',
    gender           TINYINT       NOT NULL                     COMMENT '性别：0=女，1=男',
    height           FLOAT         NOT NULL                     COMMENT '身高（cm）',
    current_weight   FLOAT         NOT NULL                     COMMENT '当前体重（kg）',
    target_weight    FLOAT         NOT NULL                     COMMENT '目标体重（kg）',
    activity_level   TINYINT       NOT NULL                     COMMENT '活动等级：1=静坐，2=轻度，3=中度，4=重度',
    diet_goal        VARCHAR(20)   NOT NULL DEFAULT 'healthy'   COMMENT '饮食目标：healthy=健康饮食, lose_weight=减肥, gain_muscle=健身',
    custom_target_cal INT         DEFAULT NULL                  COMMENT '用户自定义每日目标热量',
    recommend_cal    INT           NOT NULL                     COMMENT '系统推荐每日摄入热量',
    bmr              FLOAT         DEFAULT NULL                 COMMENT '基础代谢率',
    bmi              FLOAT         GENERATED ALWAYS AS (ROUND(current_weight / POW(height/100, 2), 1)) STORED COMMENT 'BMI = 体重/身高²',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_account (account)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 2.管理员表
DROP TABLE IF EXISTS admin;
CREATE TABLE admin (
    admin_id         INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '管理员主键',
    account          VARCHAR(50)   NOT NULL UNIQUE              COMMENT '管理员账号',
    password         VARCHAR(255)  NOT NULL                     COMMENT '登录密码',
    nickname         VARCHAR(50)   NOT NULL                     COMMENT '管理员名称',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表';

-- 3.原生食材表
DROP TABLE IF EXISTS food_category;
CREATE TABLE food_category (
    category_id      INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '分类主键',
    category_name    VARCHAR(50)   NOT NULL UNIQUE              COMMENT '分类名称',
    sort_order       INT           DEFAULT 0                    COMMENT '排序号'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='食材分类表';

DROP TABLE IF EXISTS food;
CREATE TABLE food (
    food_id          INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '食材主键',
    food_name        VARCHAR(100)  NOT NULL                     COMMENT '食材名称',
    category_id      INT           NOT NULL                     COMMENT '食材分类',
    unit             VARCHAR(20)   NOT NULL DEFAULT '100g'      COMMENT '计量单位',
    img_path         VARCHAR(255)  DEFAULT NULL                 COMMENT '食材图片路径',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES food_category(category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='原生食材表';

-- 4.营养详情表（与food一对一）
DROP TABLE IF EXISTS nutrition;
CREATE TABLE nutrition (
    nutri_id         INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '营养主键',
    food_id          INT           NOT NULL UNIQUE              COMMENT '关联食材',
    calorie          INT           NOT NULL                     COMMENT '热量（kcal/100g）',
    protein          FLOAT         NOT NULL                     COMMENT '蛋白质（g）',
    fat              FLOAT         NOT NULL                     COMMENT '脂肪（g）',
    carbohydrate     FLOAT         NOT NULL                     COMMENT '碳水化合物（g）',
    fiber            FLOAT         NOT NULL DEFAULT 0           COMMENT '膳食纤维（g）',
    sugar            FLOAT         NOT NULL DEFAULT 0           COMMENT '糖分（g）',
    sodium           FLOAT         NOT NULL DEFAULT 0           COMMENT '钠（mg）',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES food(food_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='营养详情表';

-- 5.成品食谱表
DROP TABLE IF EXISTS recipe;
CREATE TABLE recipe (
    recipe_id        INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '食谱主键',
    admin_id         INT           NOT NULL                     COMMENT '维护管理员',
    recipe_name      VARCHAR(100)  NOT NULL                     COMMENT '菜品名称',
    type             VARCHAR(20)   NOT NULL                     COMMENT '餐次分类：早餐/午餐/晚餐/加餐',
    suitable_goals   VARCHAR(50)   NOT NULL DEFAULT 'healthy'   COMMENT '适合专区：healthy/lose_weight/gain_muscle',
    intro            TEXT          DEFAULT NULL                 COMMENT '菜品简介',
    img_path         VARCHAR(255)  DEFAULT NULL                 COMMENT '菜品图片路径',
    cook_method      VARCHAR(50)   NOT NULL                     COMMENT '烹饪方式',
    forbid_tips      TEXT          DEFAULT NULL                 COMMENT '禁忌人群提示',
    total_calorie    INT           NOT NULL DEFAULT 0           COMMENT '总热量（触发器自动计算）',
    total_weight     FLOAT         NOT NULL DEFAULT 0           COMMENT '总重量（g）',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admin(admin_id),
    INDEX idx_recipe_type (type),
    INDEX idx_recipe_name (recipe_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成品食谱表';

-- 6.食谱-食材中间表（多对多）
DROP TABLE IF EXISTS recipe_food;
CREATE TABLE recipe_food (
    id               INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '主键',
    recipe_id        INT           NOT NULL                     COMMENT '关联食谱',
    food_id          INT           NOT NULL                     COMMENT '关联食材',
    weight           FLOAT         NOT NULL                     COMMENT '食材克数',
    UNIQUE KEY uk_recipe_food (recipe_id, food_id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES food(food_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='食谱食材关联表';

-- 7.饮食打卡主表
DROP TABLE IF EXISTS meal_type_def;
CREATE TABLE meal_type_def (
    type_id          INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '餐次主键',
    type_name        VARCHAR(20)   NOT NULL UNIQUE              COMMENT '餐次名称',
    sort_order       INT           DEFAULT 0                    COMMENT '排序号'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='餐次定义表';

DROP TABLE IF EXISTS diet_record;
CREATE TABLE diet_record (
    record_id        INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '打卡主键',
    user_id          INT           NOT NULL                     COMMENT '关联用户',
    meal_type_id     INT           NOT NULL                     COMMENT '用餐时段',
    eat_date         DATE          NOT NULL                     COMMENT '进食日期',
    eat_time         TIME          DEFAULT NULL                 COMMENT '具体用餐时间',
    total_cal        INT           NOT NULL DEFAULT 0           COMMENT '本餐总热量（触发器自动汇总）',
    note             TEXT          DEFAULT NULL                 COMMENT '备注',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (meal_type_id) REFERENCES meal_type_def(type_id),
    INDEX idx_diet_user_date (user_id, eat_date),
    INDEX idx_diet_date (eat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='饮食打卡主表';

-- 8.饮食打卡明细表
DROP TABLE IF EXISTS diet_record_detail;
CREATE TABLE diet_record_detail (
    detail_id        INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '明细主键',
    record_id        INT           NOT NULL                     COMMENT '关联打卡主表',
    recipe_id        INT           NOT NULL                     COMMENT '关联菜品',
    eat_weight       FLOAT         NOT NULL                     COMMENT '食用克数',
    single_cal       INT           NOT NULL DEFAULT 0           COMMENT '摄入热量（自动计算）',
    UNIQUE KEY uk_record_recipe (record_id, recipe_id),
    FOREIGN KEY (record_id) REFERENCES diet_record(record_id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='饮食打卡明细表';

-- 9.疾病表
DROP TABLE IF EXISTS disease;
CREATE TABLE disease (
    disease_id       INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '疾病主键',
    disease_name     VARCHAR(100)  NOT NULL                     COMMENT '疾病名称',
    forbid_desc      TEXT          NOT NULL                     COMMENT '饮食禁忌描述',
    forbid_keywords  TEXT          DEFAULT NULL                 COMMENT '禁忌关键词(逗号分隔)，如 糖,蜂蜜,精制碳水',
    forbid_rules     TEXT          DEFAULT NULL                 COMMENT '营养阈值JSON，如 {"max_sugar":5,"max_sodium":200}',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='疾病表';

-- 10.用户-疾病中间表（多对多）
DROP TABLE IF EXISTS user_disease;
CREATE TABLE user_disease (
    id               INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '主键',
    user_id          INT           NOT NULL                     COMMENT '关联用户',
    disease_id       INT           NOT NULL                     COMMENT '关联疾病',
    remark           TEXT          DEFAULT NULL                 COMMENT '确诊备注',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_disease (user_id, disease_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (disease_id) REFERENCES disease(disease_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户疾病关联表';

-- 11.体重记录表
DROP TABLE IF EXISTS weight_record;
CREATE TABLE weight_record (
    record_id        INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '记录主键',
    user_id          INT           NOT NULL                     COMMENT '关联用户',
    weight           FLOAT         NOT NULL                     COMMENT '体重（kg）',
    body_fat_rate    FLOAT         DEFAULT NULL                 COMMENT '体脂率%',
    measure_date     DATE          NOT NULL                     COMMENT '测量日期',
    note             TEXT          DEFAULT NULL                 COMMENT '备注',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    INDEX idx_weight_user_date (user_id, measure_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='体重记录表';

-- 12.AI减脂方案表
DROP TABLE IF EXISTS ai_diet_plan;
CREATE TABLE ai_diet_plan (
    plan_id          INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '方案主键',
    user_id          INT           NOT NULL                     COMMENT '归属用户',
    create_date      DATE          NOT NULL                     COMMENT '生成日期',
    plan_content     TEXT          NOT NULL                     COMMENT 'AI原始完整回复',
    breakfast_ids    VARCHAR(255)  DEFAULT NULL                 COMMENT '关联早餐recipe_id列表',
    lunch_ids        VARCHAR(255)  DEFAULT NULL                 COMMENT '关联午餐recipe_id列表',
    dinner_ids       VARCHAR(255)  DEFAULT NULL                 COMMENT '关联晚餐recipe_id列表',
    snack_ids        VARCHAR(255)  DEFAULT NULL                 COMMENT '关联加餐recipe_id列表',
    forbid_food      TEXT          DEFAULT NULL                 COMMENT '禁止食材',
    total_cal        INT           DEFAULT NULL                 COMMENT '方案日总热量',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    INDEX idx_plan_user_date (user_id, create_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI减脂方案表';

-- 13.AI健康周报表
DROP TABLE IF EXISTS ai_report;
CREATE TABLE ai_report (
    report_id        INT           PRIMARY KEY AUTO_INCREMENT  COMMENT '报告主键',
    user_id          INT           NOT NULL                     COMMENT '归属用户',
    start_date       DATE          NOT NULL                     COMMENT '周期起始日',
    end_date         DATE          NOT NULL                     COMMENT '周期结束日',
    total_cal        INT           NOT NULL                     COMMENT '周期总摄入热量',
    avg_daily_cal    INT           DEFAULT NULL                 COMMENT '日均摄入热量',
    weight_diff      FLOAT         NOT NULL                     COMMENT '周期体重变化（kg）',
    ai_comment       TEXT          NOT NULL                     COMMENT 'AI健康评价',
    suggest          TEXT          NOT NULL                     COMMENT '饮食调整建议',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    INDEX idx_report_user_date (user_id, start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI健康周报表';

-- 初始化基础数据
INSERT INTO food_category (category_name, sort_order) VALUES
('主食', 1), ('肉类', 2), ('蔬菜', 3), ('水果', 4),
('乳制品', 5), ('坚果', 6), ('调味品', 7),
('豆制品', 8), ('海鲜', 9), ('蛋类', 10);

INSERT INTO meal_type_def (type_name, sort_order) VALUES
('早餐', 1), ('午餐', 2), ('晚餐', 3), ('加餐', 4);
