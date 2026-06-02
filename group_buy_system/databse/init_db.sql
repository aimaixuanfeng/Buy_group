CREATE DATABASE IF NOT EXISTS campus_group_buy DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campus_group_buy;

-- 用户表
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    avatar VARCHAR(200) DEFAULT '/static/images/default_avatar.png',
    role VARCHAR(20) DEFAULT 'user',
    status INT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 分类表
CREATE TABLE category (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- 拼单表
CREATE TABLE group_buy (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INT NOT NULL,
    creator_id INT NOT NULL,
    pickup_location VARCHAR(200) NOT NULL,
    deadline DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    cancel_reason VARCHAR(200),
    cancel_time DATETIME,
    image VARCHAR(200),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES category(id),
    FOREIGN KEY (creator_id) REFERENCES user(id)
);

-- 商品项表
CREATE TABLE group_item (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_buy_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    remain_stock INT NOT NULL DEFAULT 0,
    image VARCHAR(200),
    FOREIGN KEY (group_buy_id) REFERENCES group_buy(id) ON DELETE CASCADE
);

-- 订单表
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_buy_id INT NOT NULL,
    user_id INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    cancel_time DATETIME,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_buy_id) REFERENCES group_buy(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 订单详情表
CREATE TABLE order_item (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    group_item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (group_item_id) REFERENCES group_item(id)
);

-- 公告表
CREATE TABLE notice (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认分类
INSERT INTO category (name) VALUES
('奶茶饮品'), ('外卖美食'), ('水果生鲜'), ('日用品'), ('学习用品'), ('其他');