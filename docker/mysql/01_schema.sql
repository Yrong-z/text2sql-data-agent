-- Public demo schema only. All identifiers and rows are fictional.
CREATE DATABASE IF NOT EXISTS meta CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE DATABASE IF NOT EXISTS dw CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
-- Compose defaults to MYSQL_USER=app; grant the application user access to
-- the separately configured metadata database as well as dw.
GRANT ALL PRIVILEGES ON meta.* TO 'app'@'%';
FLUSH PRIVILEGES;

USE meta;
CREATE TABLE IF NOT EXISTS table_info (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  role VARCHAR(32) NOT NULL,
  description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS column_info (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  type VARCHAR(64) NOT NULL,
  role VARCHAR(32) NOT NULL,
  examples JSON NULL,
  description TEXT NOT NULL,
  alias JSON NULL,
  table_id VARCHAR(64) NOT NULL,
  sync BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS metric_info (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description TEXT NOT NULL,
  relevant_columns JSON NOT NULL,
  alias JSON NULL
);
CREATE TABLE IF NOT EXISTS column_metric (
  column_id VARCHAR(64) NOT NULL,
  metric_id VARCHAR(64) NOT NULL,
  PRIMARY KEY (column_id, metric_id)
);

USE dw;
CREATE TABLE IF NOT EXISTS dim_region (
  region_id INT PRIMARY KEY,
  province VARCHAR(64) NOT NULL,
  region_name VARCHAR(64) NOT NULL,
  country VARCHAR(64) NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_customer (
  customer_id INT PRIMARY KEY,
  customer_name VARCHAR(128) NOT NULL,
  gender VARCHAR(16) NOT NULL,
  member_level VARCHAR(32) NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_product (
  product_id INT PRIMARY KEY,
  product_name VARCHAR(128) NOT NULL,
  category VARCHAR(64) NOT NULL,
  brand VARCHAR(64) NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_date (
  date_id INT PRIMARY KEY,
  year INT NOT NULL,
  quarter VARCHAR(8) NOT NULL,
  month INT NOT NULL,
  day INT NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_order (
  order_id INT PRIMARY KEY,
  customer_id INT NOT NULL,
  product_id INT NOT NULL,
  date_id INT NOT NULL,
  region_id INT NOT NULL,
  order_quantity INT NOT NULL,
  order_amount DECIMAL(12, 2) NOT NULL,
  CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
  CONSTRAINT fk_order_product FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
  CONSTRAINT fk_order_date FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
  CONSTRAINT fk_order_region FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
);
