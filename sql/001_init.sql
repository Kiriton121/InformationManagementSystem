-- 删除旧表（避免重复）
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS admin;

-- 员工表
CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT,
    city VARCHAR(100),
    portfolio_link VARCHAR(255),
    portfolio_file VARCHAR(255),
    department VARCHAR(100)
);

-- 管理员表
CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);
