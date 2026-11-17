-- KainGo database for XAMPP (MySQL). Run it once with: python init_db.py (or import it with the XAMPP database page)
CREATE DATABASE IF NOT EXISTS kaingo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE kaingo_db;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  firstname VARCHAR(30) NOT NULL,
  lastname VARCHAR(30) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  contact VARCHAR(11) NOT NULL,
  username VARCHAR(20) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  address VARCHAR(255) DEFAULT '',
  photo VARCHAR(100) DEFAULT NULL,
  role ENUM('customer','admin') NOT NULL DEFAULT 'customer',
  created_at DATETIME NOT NULL,
  last_login DATETIME DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS menu_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL,
  category VARCHAR(40) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  emoji VARCHAR(8) DEFAULT '🍽️',
  image VARCHAR(100) DEFAULT '',
  description VARCHAR(200) DEFAULT '',
  choices VARCHAR(500) DEFAULT '',
  available TINYINT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS promos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(20) NOT NULL UNIQUE,
  title VARCHAR(80) NOT NULL,
  description VARCHAR(200) DEFAULT '',
  discount_type ENUM('percent','fixed') NOT NULL,
  discount_value DECIMAL(10,2) NOT NULL,
  min_spend DECIMAL(10,2) NOT NULL DEFAULT 0,
  start_date DATE DEFAULT NULL,
  end_date DATE DEFAULT NULL,
  active TINYINT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  order_type ENUM('Delivery','Pickup') NOT NULL,
  payment_method ENUM('COD','Cash') NOT NULL,
  contact VARCHAR(11) NOT NULL,
  address VARCHAR(255) DEFAULT '',
  subtotal DECIMAL(10,2) NOT NULL,
  discount DECIMAL(10,2) NOT NULL DEFAULT 0,
  total DECIMAL(10,2) NOT NULL,
  promo_code VARCHAR(20) DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Pending Call',
  call_status VARCHAR(20) NOT NULL DEFAULT 'Pending',
  call_attempts INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  item_id INT DEFAULT NULL,
  name VARCHAR(80) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  qty INT NOT NULL,
  note VARCHAR(255) DEFAULT '',
  FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS status_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  status VARCHAR(20) NOT NULL,
  note VARCHAR(200) DEFAULT '',
  created_at DATETIME NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Admin account (email: admin@kaingo.org / password: Admin@123). Change the password after your first login.
INSERT IGNORE INTO users (firstname, lastname, email, contact, username, password_hash, role, created_at)
VALUES ('Store', 'Admin', 'admin@kaingo.org', '09171234568', 'kaingoadmin', 'scrypt:32768:8:1$oZHR4yq0Ct1uqUi7$38499b2d89c9c841d42e91cf05c647315a4979c02c0f3dcfdbda69df5dc199ddad40175d70120907271c0798a23df5bfda75c17f2456b2a32d21dae79cd3f114', 'admin', NOW());

INSERT INTO menu_items (name, category, price, emoji, image, description, choices) VALUES
('Tapa Silog', 'Silog Meals', 99, '🍳', '', 'Silog meal with free unli sabaw', ''),
('Tocino Silog', 'Silog Meals', 99, '🥓', '', 'Silog meal with free unli sabaw', ''),
('Hungarian Silog', 'Silog Meals', 99, '🌭', 'hungarian.jpg', 'Silog meal with free unli sabaw', ''),
('Chicken Silog', 'Silog Meals', 110, '🍗', '', 'Silog meal with free unli sabaw', ''),
('Porkchop Silog', 'Silog Meals', 99, '🍖', '', 'Silog meal with free unli sabaw', ''),
('Hotdog Silog', 'Silog Meals', 75, '🌭', '', 'Silog meal with free unli sabaw', ''),
('Bangus Silog', 'Silog Meals', 99, '🐟', 'bangus.jpg', 'Silog meal with free unli sabaw', ''),
('Pares', 'Pares & Laga-laga', 70, '🍲', 'pares.jpg', 'Panyeros Pares with rice', ''),
('Pares Overload', 'Pares & Laga-laga', 200, '🍲', 'pares-overload.jpg', 'Pares loaded with extra toppings', ''),
('Laga-laga Regular', 'Pares & Laga-laga', 60, '🍜', 'laga-laga.jpg', 'Regular laga-laga', ''),
('Laga-laga Special', 'Pares & Laga-laga', 100, '🍜', 'laga-laga.jpg', 'Special laga-laga', ''),
('Laga-laga Laman', 'Pares & Laga-laga', 120, '🍜', 'laga-laga.jpg', 'Laga-laga with extra laman', ''),
('3pcs Pork BBQ', 'Ihaw-Ihaw', 110, '🍢', 'pork-bbq.jpg', 'Three sticks of grilled pork BBQ', ''),
('Chicken Inasal', 'Ihaw-Ihaw', 110, '🍗', 'chicken-inasal.jpg', 'Grilled chicken inasal', ''),
('Chicken BBQ', 'Ihaw-Ihaw', 110, '🍗', 'chicken-bbq.jpg', 'Grilled chicken BBQ', ''),
('Grilled Liempo', 'Ihaw-Ihaw', 75, '🥩', 'grilled-liempo.jpg', 'Grilled pork belly', ''),
('Pancit Canton Bihon', 'Pancit', 155, '🍝', '', 'Canton and bihon noodles mixed', ''),
('Pancit Mike Bihon', 'Pancit', 155, '🍝', '', 'Mike and bihon noodles mixed', ''),
('Pancit Bihon Special', 'Pancit', 155, '🍝', '', 'Special pancit bihon', ''),
('Pancit Mike', 'Pancit', 155, '🍝', '', 'Pancit mike noodles', ''),
('Pancit Canton Special', 'Pancit', 155, '🍝', '', 'Special pancit canton', ''),
('Sweet & Spicy Pancit Canton', 'Pancit', 160, '🌶️', 'pancit-sweet-spicy.jpg', 'Pancit canton, sweet and spicy', ''),
('Lumpiang Shanghai', 'Sides & Pulutan', 70, '🥟', 'lumpiang-shanghai.jpg', 'Crispy lumpiang shanghai', ''),
('Lumpiang Toge (3pcs)', 'Sides & Pulutan', 35, '🥟', 'lumpiang-toge.jpg', 'Three pieces of lumpiang toge', ''),
('Chicharon Bulaklak', 'Sides & Pulutan', 150, '🍖', '', 'Crispy chicharon bulaklak', ''),
('Tokwa at Baboy', 'Sides & Pulutan', 130, '🍢', '', 'Tofu and pork in sauce', ''),
('Lechon Kawali', 'Ulam', 230, '🍖', '', 'Crispy fried pork belly', ''),
('Dinakdakan', 'Ulam', 170, '🥗', '', 'Dinakdakan', ''),
('Sisig (Sharing)', 'Ulam', 200, '🍳', 'sisig.jpg', 'Sizzling sisig for sharing', ''),
('Sisig (with Rice)', 'Ulam', 120, '🍳', 'sisig.jpg', 'Sizzling sisig with rice', ''),
('Pork Steak', 'Ulam', 130, '🥩', 'pork-steak.jpg', 'Pork steak with rice', ''),
('Chicken Steak', 'Ulam', 140, '🍗', 'chicken-steak.jpg', 'Chicken steak with rice', ''),
('Torta', 'Ulam', 150, '🍳', 'torta.jpg', 'Torta', ''),
('Chopsuey', 'Ulam', 160, '🥬', 'chopsuey.jpg', 'Mixed vegetable chopsuey', ''),
('Fried Chicken (Whole)', 'Ulam', 420, '🍗', 'fried-chicken.jpg', 'Whole fried chicken', ''),
('Fried Chicken (Half)', 'Ulam', 220, '🍗', 'fried-chicken.jpg', 'Half fried chicken', ''),
('Buko Juice', 'Refreshments', 12, '🥥', '', 'Cold buko juice', ''),
('Scramble', 'Refreshments', 50, '🍧', '', 'Shaved ice scramble', ''),
('Snow Ball', 'Refreshments', 35, '🍨', '', 'Snow ball', ''),
('Banana Con Leche', 'Refreshments', 55, '🍌', '', 'Banana con leche', ''),
('Fresh Fruit Smoothie', 'Refreshments', 60, '🥤', 'smoothie.jpg', 'Fresh fruit smoothie. Pick your flavor', 'Flavor:Mixed Fruits|Mango|Melon|Banana|Strawberry|Orange|Watermelon|Avocado|Green Apple'),
('Fresh Fruit Shake', 'Refreshments', 70, '🥛', 'shake.jpg', 'Fresh fruit shake. Pick your flavor', 'Flavor:Mixed Fruits|Mango|Melon|Banana|Strawberry|Orange|Watermelon|Avocado|Green Apple');

INSERT INTO promos (code, title, description, discount_type, discount_value, min_spend, start_date, end_date, active) VALUES
('WELCOME10', 'Welcome Treat', '10% off your order when you spend ₱200 or more', 'percent', 10, 200, NULL, NULL, 1),
('PARES50', 'Pares Night', '₱50 off when you spend ₱300 or more', 'fixed', 50, 300, NULL, NULL, 1);
