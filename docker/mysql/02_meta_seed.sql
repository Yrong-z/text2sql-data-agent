-- Fictional metadata matching the demo warehouse schema.
USE meta;
INSERT IGNORE INTO table_info (id, name, role, description) VALUES
('fact_order', 'fact_order', 'fact', '虚构订单事实表，记录数量和金额。'),
('dim_region', 'dim_region', 'dim', '虚构地区维度表。'),
('dim_customer', 'dim_customer', 'dim', '虚构客户维度表。'),
('dim_product', 'dim_product', 'dim', '虚构商品维度表。'),
('dim_date', 'dim_date', 'dim', '虚构日期维度表。');

INSERT IGNORE INTO column_info (id, name, type, role, examples, description, alias, table_id, sync) VALUES
('fact_order.order_id', 'order_id', 'int', 'primary_key', JSON_ARRAY(1001,1002), '订单唯一标识。', JSON_ARRAY('订单ID'), 'fact_order', FALSE),
('fact_order.customer_id', 'customer_id', 'int', 'foreign_key', JSON_ARRAY(1,2), '关联客户。', JSON_ARRAY('客户ID','用户ID'), 'fact_order', FALSE),
('fact_order.product_id', 'product_id', 'int', 'foreign_key', JSON_ARRAY(10,20), '关联商品。', JSON_ARRAY('商品ID'), 'fact_order', FALSE),
('fact_order.date_id', 'date_id', 'int', 'foreign_key', JSON_ARRAY(20250105,20250212), '关联日期。', JSON_ARRAY('日期','下单日期'), 'fact_order', FALSE),
('fact_order.region_id', 'region_id', 'int', 'foreign_key', JSON_ARRAY(1,2), '关联地区。', JSON_ARRAY('地区ID','区域ID'), 'fact_order', FALSE),
('fact_order.order_quantity', 'order_quantity', 'int', 'measure', JSON_ARRAY(1,3), '订单购买数量。', JSON_ARRAY('销量','购买数量','件数'), 'fact_order', FALSE),
('fact_order.order_amount', 'order_amount', 'decimal(12,2)', 'measure', JSON_ARRAY(199.90,899.00), '订单金额。', JSON_ARRAY('销售额','订单金额','收入'), 'fact_order', FALSE),
('dim_region.region_id', 'region_id', 'int', 'primary_key', JSON_ARRAY(1,2), '地区唯一标识。', JSON_ARRAY('地区ID'), 'dim_region', FALSE),
('dim_region.province', 'province', 'varchar(64)', 'dimension', JSON_ARRAY('浙江省','四川省'), '省份名称。', JSON_ARRAY('省份','省'), 'dim_region', TRUE),
('dim_region.region_name', 'region_name', 'varchar(64)', 'dimension', JSON_ARRAY('华东','西南'), '大区名称。', JSON_ARRAY('地区','区域','大区'), 'dim_region', TRUE),
('dim_region.country', 'country', 'varchar(64)', 'dimension', JSON_ARRAY('中国'), '国家名称。', JSON_ARRAY('国家'), 'dim_region', TRUE),
('dim_product.product_id', 'product_id', 'int', 'primary_key', JSON_ARRAY(10,20), '商品唯一标识。', JSON_ARRAY('商品ID'), 'dim_product', FALSE),
('dim_product.product_name', 'product_name', 'varchar(128)', 'dimension', JSON_ARRAY('云墨水杯','星河耳机'), '商品名称。', JSON_ARRAY('商品名称','产品名称'), 'dim_product', TRUE),
('dim_product.category', 'category', 'varchar(64)', 'dimension', JSON_ARRAY('家居','数码'), '商品品类。', JSON_ARRAY('品类','分类'), 'dim_product', TRUE),
('dim_product.brand', 'brand', 'varchar(64)', 'dimension', JSON_ARRAY('青禾','蓝舟'), '商品品牌。', JSON_ARRAY('品牌'), 'dim_product', TRUE),
('dim_date.date_id', 'date_id', 'int', 'primary_key', JSON_ARRAY(20250105,20250212), '日期唯一标识。', JSON_ARRAY('日期ID'), 'dim_date', FALSE),
('dim_date.year', 'year', 'int', 'dimension', JSON_ARRAY(2025), '年份。', JSON_ARRAY('年','年份'), 'dim_date', FALSE),
('dim_date.quarter', 'quarter', 'varchar(8)', 'dimension', JSON_ARRAY('Q1'), '季度。', JSON_ARRAY('季度'), 'dim_date', TRUE),
('dim_date.month', 'month', 'int', 'dimension', JSON_ARRAY(1,2), '月份。', JSON_ARRAY('月','月份'), 'dim_date', FALSE),
('dim_date.day', 'day', 'int', 'dimension', JSON_ARRAY(5,12), '日期中的日。', JSON_ARRAY('日'), 'dim_date', FALSE),
('dim_customer.customer_id', 'customer_id', 'int', 'primary_key', JSON_ARRAY(1,2), '客户唯一标识。', JSON_ARRAY('客户ID'), 'dim_customer', FALSE),
('dim_customer.customer_name', 'customer_name', 'varchar(128)', 'dimension', JSON_ARRAY('林舟','苏禾'), '客户名称。', JSON_ARRAY('客户名称'), 'dim_customer', TRUE),
('dim_customer.gender', 'gender', 'varchar(16)', 'dimension', JSON_ARRAY('女','男'), '客户性别。', JSON_ARRAY('性别'), 'dim_customer', TRUE),
('dim_customer.member_level', 'member_level', 'varchar(32)', 'dimension', JSON_ARRAY('银卡','金卡'), '会员等级。', JSON_ARRAY('会员等级','用户等级'), 'dim_customer', TRUE);

INSERT IGNORE INTO metric_info (id, name, description, relevant_columns, alias) VALUES
('GMV', 'GMV', '所有订单的成交金额总和。', JSON_ARRAY('fact_order.order_amount'), JSON_ARRAY('成交总额','销售额','订单总额')),
('AOV', 'AOV', '订单金额的平均值。', JSON_ARRAY('fact_order.order_amount'), JSON_ARRAY('平均订单金额','客单价'));
INSERT IGNORE INTO column_metric (column_id, metric_id) VALUES
('fact_order.order_amount', 'GMV'), ('fact_order.order_amount', 'AOV');
