CREATE DATABASE IF NOT EXISTS FinalProjectDB;

USE FinalProjectDB;

CREATE TABLE IF NOT EXISTS BasicUser(
    email VARCHAR(25) PRIMARY KEY,
    Uname VARCHAR(20) NOT NULL,
    Upassword VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS Users(
    email VARCHAR(25) PRIMARY KEY,
    address VARCHAR(20) NOT NULL,
    credit INT,
    FOREIGN KEY (email) REFERENCES BasicUser(email)
);

CREATE TABLE IF NOT EXISTS Managers(
    email VARCHAR(25) PRIMARY KEY,
    FOREIGN KEY (email) REFERENCES BasicUser(email)
);

CREATE TABLE IF NOT EXISTS Inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    furniture_type INT NOT NULL,
    color VARCHAR(50) NOT NULL,
    f_name VARCHAR(500) NOT NULL,
    f_desc VARCHAR(1000) NOT NULL,
    price FLOAT NOT NULL,
    high INT NOT NULL,
    depth INT NOT NULL,
    width INT NOT NULL,
    is_adjustable BOOLEAN DEFAULT FALSE,
    has_armrest BOOLEAN DEFAULT FALSE,
    material VARCHAR(50),
    quntity INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS CouponsCodes (
    idCouponsCodes INT PRIMARY KEY,
    CouponValue VARCHAR(48) UNIQUE NOT NULL,
    Discount INT NOT NULL
);

CREATE TABLE IF NOT EXISTS Orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Ostatus VARCHAR(20) NOT NULL,
    UserEmail VARCHAR(25) NOT NULL,
    idCouponsCodes INT,
    FOREIGN KEY (UserEmail) REFERENCES Users(email),
    FOREIGN KEY (idCouponsCodes) REFERENCES CouponsCodes(idCouponsCodes)
);

INSERT INTO Inventory 
  (furniture_type, color, f_name, f_desc, price, high, depth, width, is_adjustable, has_armrest, material, quntity)
VALUES
  (1, 'brown', 'brown dining table', 'A high quality dining table in brown.', 120.00, 100, 50, 60, NULL, NULL, 'wood', 0),
  (1, 'brown', 'brown dining table', 'A high quality dining table in brown.', 99.99, 100, 50, 60, NULL, NULL, 'metal', 10),
  (1, 'gray',  'gray dining table',  'A high quality dining table in gray.',  120.00, 100, 50, 60, NULL, NULL, 'wood', 5),
  (1, 'gray',  'gray dining table',  'A high quality dining table in gray.',  99.99, 100, 50, 60, NULL, NULL, 'metal', 0);

INSERT INTO Inventory 
  (furniture_type, color, f_name, f_desc, price, high, depth, width, is_adjustable, has_armrest, material, quntity)
VALUES
  (2, 'black', 'black work desk', 'A high quality work desk in black.', 149.99, 120, 55, 65, NULL, NULL, 'wood', 1),
  (2, 'black', 'black work desk', 'A high quality work desk in black.', 199.99, 120, 55, 65, NULL, NULL, 'glass', 7),
  (2, 'white', 'white work desk', 'A high quality work desk in white.', 149.99, 120, 55, 65, NULL, NULL, 'wood', 5),
  (2, 'white', 'white work desk', 'A high quality work desk in white.', 199.99, 120, 55, 65, NULL, NULL, 'glass', 10);

INSERT INTO BasicUser (email, Uname, Upassword) VALUES
  ('raz@example.com', 'Raz', 'pass1'),
  ('ron@example.com', 'Ron', 'pass2'),
  ('amit@example.com', 'Amit', 'pass3'),
  ('hili@example.com', 'Hili', 'pass4'),
  ('tal@example.com', 'Tal', 'pass5');

INSERT INTO Users (email, address, credit) VALUES
  ('raz@example.com', 'Address1', 0),
  ('ron@example.com', 'Address2', 50),
  ('amit@example.com', 'Address3', 100);

INSERT INTO Managers (email) VALUES
  ('hili@example.com'),
  ('tal@example.com');

INSERT INTO CouponsCodes (idCouponsCodes, CouponValue, Discount) VALUES
  (1, 'SAVE10', 10),
  (2, 'DISCOUNT20', 20),
  (3, 'PROMO30', 30),
  (4, 'COUPON40', 40),
  (5, 'OFFER50', 50);
