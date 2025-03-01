CREATE DATABASE FinalProjectDB;

use FinalProjectDB;
CREATE TABLE BasicUser(
	email varchar(25) primary key,
    Uname varchar(20) not null,
    Upassword varchar(20) not null
);
use FinalProjectDB;
CREATE TABLE Users(
	email varchar(25) primary key,
    address varchar(20) not null,
    credit int,
    foreign key (email) references BasicUser(email)
);
use FinalProjectDB;
CREATE TABLE Managers(
  email varchar(25) PRIMARY KEY,
  FOREIGN KEY (email) REFERENCES BasicUser(email)
);

use FinalProjectDB;
CREATE TABLE Inventory (
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
    quantity INT NOT NULL DEFAULT 0
);
 use FinalProjectDB;
CREATE TABLE CouponsCodes (
    idCouponsCodes INT PRIMARY KEY,
    CouponValue VARCHAR(48) UNIQUE NOT NULL,
    Discount INT NOT NULL
);
use FinalProjectDB;
CREATE TABLE Orders (
	id INT AUTO_INCREMENT PRIMARY KEY,
    Ostatus varchar(20) NOT NULL,
    UserEmail varchar(25) NOT NULL,
    idCouponsCodes INT,
    foreign key(UserEmail) references BasicUser(email),
    foreign key(idCouponsCodes) references CouponsCodes(idCouponsCodes)
);


-------------------------------
-- insert furniture in inventory
-------------------------------
INSERT INTO Inventory 
  (furniture_type, color, f_name, f_desc, price, high, depth, width, is_adjustable, has_armrest, material, quantity)
VALUES
  (1, 'brown', 'brown dining table', 'A high quality dining table in brown.', 120.00, 100, 50, 60, NULL, NULL, 'wood', 0),
  (1, 'brown', 'brown dining table', 'A high quality dining table in brown.', 99.99, 100, 50, 60, NULL, NULL, 'metal', 10),
  (1, 'gray',  'gray dining table',  'A high quality dining table in gray.',  120.00, 100, 50, 60, NULL, NULL, 'wood', 5),
  (1, 'gray',  'gray dining table',  'A high quality dining table in gray.',  99.99, 100, 50, 60, NULL, NULL, 'metal', 0);

INSERT INTO Inventory 
  (furniture_type, color, f_name, f_desc, price, high, depth, width, is_adjustable, has_armrest, material, quantity)
VALUES
  (2, 'black', 'black work desk', 'A high quality work desk in black.', 149.99, 120, 55, 65, NULL, NULL, 'wood', 1),
  (2, 'black', 'black work desk', 'A high quality work desk in black.', 199.99, 120, 55, 65, NULL, NULL, 'glass', 7),
  (2, 'white', 'white work desk', 'A high quality work desk in white.', 149.99, 120, 55, 65, NULL, NULL, 'wood', 5),
  (2, 'white', 'white work desk', 'A high quality work desk in white.', 199.99, 120, 55, 65, NULL, NULL, 'glass', 10);

INSERT INTO Inventory 
  (furniture_type, color, f_name, f_desc, price, high, depth, width, is_adjustable, has_armrest, material, quantity)
VALUES
  (3, 'gray', 'gray coffee table', 'A high quality coffee table in gray.', 199.99, 130, 60, 70, NULL, NULL, 'glass', 1),
  (3, 'gray', 'gray coffee table', 'A high quality coffee table in gray.', 99.99, 130, 60, 70, NULL, NULL, 'plastic', 10),
  (3, 'red',  'red coffee table',  'A high quality coffee table in red.',  199.99, 130, 60, 70, NULL, NULL, 'glass', 5),
  (3, 'red',  'red coffee table',  'A high quality coffee table in red.',  99.99, 130, 60, 70, NULL, NULL, 'plastic', 0);

INSERT INTO Inventory 
  (furniture_type, color, f_name, f_desc, price, high, depth, width, is_adjustable, has_armrest, material, quantity)
VALUES
  
  (4, 'red',   'red work chair',   'A high quality work chair in red.',   279.99, 140, 65, 75, TRUE,  TRUE,  NULL, 5),
  (4, 'red',   'red work chair',   'A high quality work chair in red.',   249.99, 140, 65, 75, TRUE,  FALSE, NULL, 0),
  (4, 'red',   'red work chair',   'A high quality work chair in red.',   259.99, 140, 65, 75, FALSE, TRUE,  NULL, 20),
  (4, 'red',   'red work chair',   'A high quality work chair in red.',   219.99, 140, 65, 75, FALSE, FALSE, NULL, 7),
  (4, 'white', 'white work chair', 'A high quality work chair in white.', 249.99, 140, 65, 75, TRUE,  TRUE,  NULL, 15),
  (4, 'white', 'white work chair', 'A high quality work chair in white.', 279.99, 140, 65, 75, TRUE,  FALSE, NULL, 2),
  (4, 'white', 'white work chair', 'A high quality work chair in white.', 249.99, 140, 65, 75, FALSE, TRUE,  NULL, 10),
  (4, 'white', 'white work chair', 'A high quality work chair in white.', 219.99, 140, 65, 75, FALSE, FALSE, NULL, 1);

INSERT INTO Inventory 
  (furniture_type, color, f_name, f_desc, price, high, depth, width, is_adjustable, has_armrest, material, quantity)
VALUES
  
  (5, 'black', 'black gaming chair', 'A high quality gaming chair in black.', 299.99, 150, 70, 80, TRUE,  TRUE,  NULL, 10),
  (5, 'black', 'black gaming chair', 'A high quality gaming chair in black.', 299.99, 150, 70, 80, TRUE,  FALSE, NULL, 5),
  (5, 'black', 'black gaming chair', 'A high quality gaming chair in black.', 299.99, 150, 70, 80, FALSE, TRUE,  NULL, 5),
  (5, 'black', 'black gaming chair', 'A high quality gaming chair in black.', 299.99, 150, 70, 80, FALSE, FALSE, NULL, 10),
  (5, 'blue', 'blue gaming chair', 'A high quality gaming chair in blue.', 299.99, 150, 70, 80, TRUE,  TRUE,  NULL, 0),
  (5, 'blue', 'blue gaming chair', 'A high quality gaming chair in blue.', 299.99, 150, 70, 80, TRUE,  FALSE, NULL, 1),
  (5, 'blue', 'blue gaming chair', 'A high quality gaming chair in blue.', 299.99, 150, 70, 80, FALSE, TRUE,  NULL, 10),
  (5, 'blue', 'blue gaming chair', 'A high quality gaming chair in blue.', 299.99, 150, 70, 80, FALSE, FALSE, NULL, 7);



-------------------------------
-- insert users in BasicUser
-------------------------------
INSERT INTO BasicUser (email, Uname, Upassword) VALUES
  ('raz@example.com', 'Raz', 'password1'),
  ('ron@example.com', 'Ron', 'password2'),
  ('amit@example.com', 'Amit', 'password3'),
  ('hili@example.com', 'Hili', 'password4'),
  ('tal@example.com', 'Tal', 'password5');

-------------------------------
-- Insert records into Users and manager tables
-------------------------------
INSERT INTO Users (email, address, credit) VALUES
  ('raz@example.com', 'Address1', 0),
  ('ron@example.com', 'Address2', 50),
  ('amit@example.com', 'Address3', 100);

INSERT INTO Managers (email) VALUES
  ('hili@example.com'),
  ('tal@example.com');
  
  -------------------------------
-- Insert coupons into CouponsCodes table
-------------------------------
  INSERT INTO CouponsCodes (idCouponsCodes, CouponValue, Discount) VALUES
  (1, 'SAVE10', 10),
  (2, 'DISCOUNT20', 20),
  (3, 'PROMO30', 30),
  (4, 'COUPON40', 40),
  (5, 'OFFER50', 50);

