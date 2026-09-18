-- Minimal fictional warehouse rows for public demos.
USE dw;
INSERT IGNORE INTO dim_region VALUES
(1, '浙江省', '华东', '中国'), (2, '四川省', '西南', '中国');
INSERT IGNORE INTO dim_customer VALUES
(1, '林舟', '女', '金卡'), (2, '苏禾', '男', '银卡');
INSERT IGNORE INTO dim_product VALUES
(10, '云墨水杯', '家居', '青禾'), (20, '星河耳机', '数码', '蓝舟');
INSERT IGNORE INTO dim_date VALUES
(20250105, 2025, 'Q1', 1, 5), (20250118, 2025, 'Q1', 1, 18),
(20250212, 2025, 'Q1', 2, 12), (20250220, 2025, 'Q1', 2, 20);
INSERT IGNORE INTO fact_order VALUES
(1001, 1, 10, 20250105, 1, 2, 399.80),
(1002, 2, 20, 20250118, 2, 1, 599.00),
(1003, 1, 20, 20250212, 1, 3, 1797.00),
(1004, 2, 10, 20250220, 2, 1, 199.90);
