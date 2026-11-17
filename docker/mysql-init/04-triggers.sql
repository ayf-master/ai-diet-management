-- AI辅助减脂饮食管理系统 - 触发器

USE diet_management;

-- 1.新增打卡明细→自动更新主表本餐总热量
DROP TRIGGER IF EXISTS trg_detail_after_insert;
DELIMITER $$
CREATE TRIGGER trg_detail_after_insert
AFTER INSERT ON diet_record_detail
FOR EACH ROW
BEGIN
    UPDATE diet_record
    SET total_cal = (
        SELECT COALESCE(SUM(single_cal), 0)
        FROM diet_record_detail
        WHERE record_id = NEW.record_id
    )
    WHERE record_id = NEW.record_id;
END$$
DELIMITER ;

-- 2.删除打卡明细→自动更新主表本餐总热量
DROP TRIGGER IF EXISTS trg_detail_after_delete;
DELIMITER $$
CREATE TRIGGER trg_detail_after_delete
AFTER DELETE ON diet_record_detail
FOR EACH ROW
BEGIN
    UPDATE diet_record
    SET total_cal = (
        SELECT COALESCE(SUM(single_cal), 0)
        FROM diet_record_detail
        WHERE record_id = OLD.record_id
    )
    WHERE record_id = OLD.record_id;
END$$
DELIMITER ;

-- 3.食材营养更新→自动同步关联食谱热量
DROP TRIGGER IF EXISTS trg_nutrition_after_update;
DELIMITER $$
CREATE TRIGGER trg_nutrition_after_update
AFTER UPDATE ON nutrition
FOR EACH ROW
BEGIN
    UPDATE recipe r
    SET r.total_calorie = (
        SELECT COALESCE(SUM(n.calorie * rf.weight / 100), 0)
        FROM recipe_food rf
        JOIN nutrition n ON rf.food_id = n.food_id
        WHERE rf.recipe_id = r.recipe_id
    )
    WHERE r.recipe_id IN (
        SELECT DISTINCT rf.recipe_id
        FROM recipe_food rf
        WHERE rf.food_id = NEW.food_id
    );
END$$
DELIMITER ;

-- 4.新增/删除食谱食材→自动计算食谱热量和重量
DROP TRIGGER IF EXISTS trg_recipe_food_after_insert;
DELIMITER $$
CREATE TRIGGER trg_recipe_food_after_insert
AFTER INSERT ON recipe_food
FOR EACH ROW
BEGIN
    UPDATE recipe r
    SET
        r.total_calorie = (
            SELECT COALESCE(SUM(n.calorie * rf.weight / 100), 0)
            FROM recipe_food rf
            JOIN nutrition n ON rf.food_id = n.food_id
            WHERE rf.recipe_id = NEW.recipe_id
        ),
        r.total_weight = (
            SELECT COALESCE(SUM(rf.weight), 0)
            FROM recipe_food rf
            WHERE rf.recipe_id = NEW.recipe_id
        )
    WHERE r.recipe_id = NEW.recipe_id;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_recipe_food_after_delete;
DELIMITER $$
CREATE TRIGGER trg_recipe_food_after_delete
AFTER DELETE ON recipe_food
FOR EACH ROW
BEGIN
    UPDATE recipe r
    SET
        r.total_calorie = (
            SELECT COALESCE(SUM(n.calorie * rf.weight / 100), 0)
            FROM recipe_food rf
            JOIN nutrition n ON rf.food_id = n.food_id
            WHERE rf.recipe_id = OLD.recipe_id
        ),
        r.total_weight = (
            SELECT COALESCE(SUM(rf.weight), 0)
            FROM recipe_food rf
            WHERE rf.recipe_id = OLD.recipe_id
        )
    WHERE r.recipe_id = OLD.recipe_id;
END$$
DELIMITER ;
