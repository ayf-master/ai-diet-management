package com.diet.util;

import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.Timestamp;
import java.util.LinkedHashMap;
import java.util.Map;

// 通用行映射：按列名输出 snake_case Map，天然对齐前端字段；时间统一格式化
public class Rows {

    public static Map<String, Object> toMap(ResultSet rs) throws java.sql.SQLException {
        ResultSetMetaData meta = rs.getMetaData();
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 1; i <= meta.getColumnCount(); i++) {
            String label = meta.getColumnLabel(i);
            Object value = rs.getObject(i);
            if (value instanceof Timestamp ts) {
                String s = ts.toString();
                // Timestamp.toString() 是 "yyyy-MM-dd HH:mm:ss.fff"，去掉 .fff 对齐 Python str(datetime)
                int dot = s.indexOf('.');
                value = dot > 0 ? s.substring(0, dot) : s;
            } else if (value instanceof java.time.LocalDateTime dt) {
                value = dt.toLocalDate().toString() + " " + dt.toLocalTime().toString();
            } else if (value instanceof java.sql.Date d) {
                value = d.toString();
            } else if (value instanceof java.sql.Time t) {
                value = t.toString();
            } else if (value instanceof java.time.LocalTime t) {
                value = t.toString();
            }
            m.put(label, value);
        }
        return m;
    }
}
