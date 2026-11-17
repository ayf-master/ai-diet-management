-- AI辅助减脂饮食管理系统 - 存储过程

USE diet_management;

-- 1.计算食谱总热量和总重量（根据食材配比）
DROP PROCEDURE IF EXISTS sp_calc_recipe_calorie;
DELIMITER $$
CREATE PROCEDURE sp_calc_recipe_calorie(IN p_recipe_id INT)
BEGIN
    DECLARE total_cal INT DEFAULT 0;
    DECLARE total_w FLOAT DEFAULT 0;

    SELECT COALESCE(SUM(n.calorie * rf.weight / 100), 0),
           COALESCE(SUM(rf.weight), 0)
    INTO total_cal, total_w
    FROM recipe_food rf
    JOIN nutrition n ON rf.food_id = n.food_id
    WHERE rf.recipe_id = p_recipe_id;

    UPDATE recipe
    SET total_calorie = total_cal, total_weight = total_w
    WHERE recipe_id = p_recipe_id;

    SELECT total_cal AS calorie, total_w AS weight;
END$$
DELIMITER ;

-- 2.统计用户某日摄入总热量
DROP PROCEDURE IF EXISTS sp_calc_user_daily_cal;
DELIMITER $$
CREATE PROCEDURE sp_calc_user_daily_cal(IN p_user_id INT, IN p_date DATE)
BEGIN
    SELECT p_date AS eat_date,
           COUNT(dr.record_id) AS meal_count,
           COALESCE(SUM(dr.total_cal), 0) AS daily_total
    FROM diet_record dr
    WHERE dr.user_id = p_user_id AND dr.eat_date = p_date;
END$$
DELIMITER ;

-- 3.统计用户周期摄入汇总（含体重变化）
DROP PROCEDURE IF EXISTS sp_calc_user_period_summary;
DELIMITER $$
CREATE PROCEDURE sp_calc_user_period_summary(
    IN p_user_id INT, IN p_start_date DATE, IN p_end_date DATE
)
BEGIN
    SELECT p_user_id AS user_id,
           p_start_date AS start_date,
           p_end_date AS end_date,
           COUNT(DISTINCT dr.eat_date) AS total_days,
           COALESCE(SUM(dr.total_cal), 0) AS period_total_cal,
           ROUND(COALESCE(SUM(dr.total_cal), 0) / NULLIF(DATEDIFF(p_end_date, p_start_date) + 1, 0), 0) AS avg_daily_cal,
           MIN(wr.weight) AS period_start_weight,
           MAX(wr.weight) AS period_end_weight,
           ROUND(COALESCE(MAX(wr.weight), 0) - COALESCE(MIN(wr.weight), 0), 1) AS weight_diff
    FROM (
        SELECT p_start_date + INTERVAL n DAY AS dt
        FROM numbers
        WHERE n BETWEEN 0 AND DATEDIFF(p_end_date, p_start_date)
    ) dates
    LEFT JOIN diet_record dr ON dr.user_id = p_user_id AND dr.eat_date = dates.dt
    LEFT JOIN weight_record wr ON wr.user_id = p_user_id
        AND wr.measure_date BETWEEN p_start_date AND p_end_date;
END$$
DELIMITER ;

-- 4.自动计算用户推荐热量（Mifflin-St Jeor公式 + BMI分级缺口）
DROP PROCEDURE IF EXISTS sp_recommend_daily_cal;
DELIMITER $$
CREATE PROCEDURE sp_recommend_daily_cal(IN p_user_id INT)
BEGIN
    DECLARE v_bmr FLOAT DEFAULT 0;
    DECLARE v_tdee FLOAT DEFAULT 0;
    DECLARE v_factor FLOAT DEFAULT 1.2;
    DECLARE v_gender TINYINT;
    DECLARE v_weight FLOAT;
    DECLARE v_height FLOAT;
    DECLARE v_age INT;
    DECLARE v_level TINYINT;
    DECLARE v_bmi FLOAT DEFAULT 0;
    DECLARE v_deficit INT DEFAULT 500;
    DECLARE v_min_cal INT DEFAULT 1200;
    DECLARE v_bmi_level VARCHAR(10) DEFAULT '';

    SELECT gender, current_weight, height, age, activity_level
    INTO v_gender, v_weight, v_height, v_age, v_level
    FROM user WHERE user_id = p_user_id;

    -- BMR Mifflin-St Jeor
    IF v_gender = 1 THEN
        SET v_bmr = 10 * v_weight + 6.25 * v_height - 5 * v_age + 5;
        SET v_min_cal = 1500;
    ELSE
        SET v_bmr = 10 * v_weight + 6.25 * v_height - 5 * v_age - 161;
        SET v_min_cal = 1200;
    END IF;

    -- 活动等级系数
    CASE v_level
        WHEN 1 THEN SET v_factor = 1.2;
        WHEN 2 THEN SET v_factor = 1.375;
        WHEN 3 THEN SET v_factor = 1.55;
        WHEN 4 THEN SET v_factor = 1.725;
    END CASE;

    SET v_tdee = v_bmr * v_factor;
    SET v_bmi = v_weight / POW(v_height / 100, 2);

    -- 根据BMI调整热量缺口/盈余（中国标准）
    CASE
        WHEN v_bmi < 18.5 THEN
            SET v_bmi_level = '偏瘦';
            SET v_deficit = -300;  -- 负缺口=盈余，增肌增重
        WHEN v_bmi < 24 THEN
            SET v_bmi_level = '正常';
            SET v_deficit = 300;
        WHEN v_bmi < 28 THEN
            SET v_bmi_level = '超重';
            SET v_deficit = 500;
        ELSE
            SET v_bmi_level = '肥胖';
            SET v_deficit = 700;
    END CASE;

    IF v_deficit < 0 THEN
        -- 偏瘦：TDEE + 盈余
        SET @v_recommend = ROUND(v_tdee - v_deficit, 0);  -- 减负数=加
    ELSE
        -- 正常/超重/肥胖：TDEE - 缺口，不低于安全下限
        SET @v_recommend = ROUND(GREATEST(v_tdee - v_deficit, v_min_cal), 0);
    END IF;

    UPDATE user
    SET bmr = ROUND(v_bmr, 1),
        recommend_cal = @v_recommend
    WHERE user_id = p_user_id;

    SELECT ROUND(v_bmi, 1) AS bmi,
           v_bmi_level AS bmi_level,
           ROUND(v_bmr, 1) AS bmr,
           v_factor AS activity_factor,
           ROUND(v_tdee, 0) AS tdee,
           IF(v_deficit < 0, CONCAT('盈余', -v_deficit), CONCAT('缺口', v_deficit)) AS adjust,
           @v_recommend AS recommend_cal;
END$$
DELIMITER ;

-- 5.记录体重并同步更新用户当前体重和推荐热量
DROP PROCEDURE IF EXISTS sp_record_weight;
DELIMITER $$
CREATE PROCEDURE sp_record_weight(
    IN p_user_id INT, IN p_weight FLOAT, IN p_body_fat FLOAT,
    IN p_measure_date DATE, IN p_note TEXT
)
BEGIN
    INSERT INTO weight_record (user_id, weight, body_fat_rate, measure_date, note)
    VALUES (p_user_id, p_weight, p_body_fat, p_measure_date, p_note);

    UPDATE user SET current_weight = p_weight WHERE user_id = p_user_id;

    CALL sp_recommend_daily_cal(p_user_id);
END$$
DELIMITER ;
