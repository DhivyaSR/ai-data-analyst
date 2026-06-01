DROP TABLE IF EXISTS sales;

CREATE TABLE sales (
  id INT AUTO_INCREMENT PRIMARY KEY,
  product VARCHAR(100) NOT NULL,
  category VARCHAR(100) NOT NULL,
  region VARCHAR(100) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  sold_at DATE NOT NULL
);

INSERT INTO sales (product, category, region, amount, sold_at)
WITH RECURSIVE seq AS (
  SELECT 1 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 1000
)
SELECT
  ELT((n % 5) + 1, 'Widget', 'Gadget', 'Tool', 'Item', 'Accessory') AS product,
  ELT((n % 3) + 1, 'Electronics', 'Furniture', 'Clothing') AS category,
  ELT((n % 4) + 1, 'North', 'South', 'East', 'West') AS region,
  ROUND(100 + (n * 3.21), 2) AS amount,
  DATE_SUB(CURDATE(), INTERVAL n DAY) AS sold_at
FROM seq;
