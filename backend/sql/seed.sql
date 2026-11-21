-- 1. EMPLOYEES (25 RECORDS)

INSERT INTO employees
(name, email, department, role, manager_id, status)
VALUES
('Arun Kumar','arun@company.com','IT','Employee',NULL,'active'),
('Priya Sharma','priya@company.com','HR','HR Staff',NULL,'active'),
('Rahul Raj','rahul@company.com','Finance','Employee',NULL,'active'),
('Admin User','admin@company.com','IT','Admin',NULL,'active'),
('Karthik Kumar','karthik@company.com','IT','Employee',1,'active'),
('Sneha Reddy','sneha@company.com','HR','Employee',2,'active'),
('Vijay Anand','vijay@company.com','Finance','Employee',3,'active'),
('Divya Nair','divya@company.com','Marketing','Employee',NULL,'active'),
('Sanjay Kumar','sanjay@company.com','IT','Manager',1,'active'),
('Meena Devi','meena@company.com','HR','Manager',2,'active'),
('Ajith Raj','ajith@company.com','Sales','Employee',NULL,'active'),
('Keerthana S','keerthana@company.com','IT','Employee',9,'active'),
('Vignesh M','vignesh@company.com','Finance','Employee',3,'active'),
('Anitha R','anitha@company.com','Marketing','Employee',8,'active'),
('Surya Prakash','surya@company.com','Sales','Manager',11,'active'),
('Deepika P','deepika@company.com','IT','Employee',9,'active'),
('Manoj Kumar','manoj@company.com','Support','Employee',NULL,'active'),
('Nithya R','nithya@company.com','HR','Employee',10,'active'),
('Praveen S','praveen@company.com','IT','Employee',9,'active'),
('Swathi K','swathi@company.com','Finance','Manager',3,'active'),
('Dinesh B','dinesh@company.com','Support','Employee',17,'active'),
('Lavanya M','lavanya@company.com','Marketing','Manager',8,'active'),
('Gokul R','gokul@company.com','Sales','Employee',15,'active'),
('Harish V','harish@company.com','IT','Employee',9,'active'),
('Pavithra S','pavithra@company.com','Support','Employee',17,'active');


-- 2. LEAVE BALANCES (50 RECORDS)

INSERT INTO leave_balances
(employee_id, leave_type, balance, as_of_date)
VALUES
(1,'Casual',8,CURRENT_DATE),(1,'Sick',5,CURRENT_DATE),
(2,'Casual',10,CURRENT_DATE),(2,'Sick',6,CURRENT_DATE),
(3,'Casual',7,CURRENT_DATE),(3,'Sick',5,CURRENT_DATE),
(4,'Casual',12,CURRENT_DATE),(4,'Sick',8,CURRENT_DATE),
(5,'Casual',9,CURRENT_DATE),(5,'Sick',6,CURRENT_DATE),
(6,'Casual',8,CURRENT_DATE),(6,'Sick',5,CURRENT_DATE),
(7,'Casual',6,CURRENT_DATE),(7,'Sick',4,CURRENT_DATE),
(8,'Casual',10,CURRENT_DATE),(8,'Sick',7,CURRENT_DATE),
(9,'Casual',12,CURRENT_DATE),(9,'Sick',8,CURRENT_DATE),
(10,'Casual',9,CURRENT_DATE),(10,'Sick',6,CURRENT_DATE),
(11,'Casual',7,CURRENT_DATE),(11,'Sick',5,CURRENT_DATE),
(12,'Casual',11,CURRENT_DATE),(12,'Sick',8,CURRENT_DATE),
(13,'Casual',6,CURRENT_DATE),(13,'Sick',4,CURRENT_DATE),
(14,'Casual',8,CURRENT_DATE),(14,'Sick',5,CURRENT_DATE),
(15,'Casual',10,CURRENT_DATE),(15,'Sick',7,CURRENT_DATE),
(16,'Casual',9,CURRENT_DATE),(16,'Sick',6,CURRENT_DATE),
(17,'Casual',7,CURRENT_DATE),(17,'Sick',5,CURRENT_DATE),
(18,'Casual',12,CURRENT_DATE),(18,'Sick',8,CURRENT_DATE),
(19,'Casual',8,CURRENT_DATE),(19,'Sick',5,CURRENT_DATE),
(20,'Casual',10,CURRENT_DATE),(20,'Sick',7,CURRENT_DATE),
(21,'Casual',6,CURRENT_DATE),(21,'Sick',4,CURRENT_DATE),
(22,'Casual',11,CURRENT_DATE),(22,'Sick',8,CURRENT_DATE),
(23,'Casual',9,CURRENT_DATE),(23,'Sick',6,CURRENT_DATE),
(24,'Casual',7,CURRENT_DATE),(24,'Sick',5,CURRENT_DATE),
(25,'Casual',10,CURRENT_DATE),(25,'Sick',7,CURRENT_DATE);


-- 3. LEAVE REQUESTS (20 RECORDS)

INSERT INTO leave_requests
(employee_id,start_date,end_date,leave_type,status,approver_id)
VALUES
(1,CURRENT_DATE+5,CURRENT_DATE+6,'Casual','pending',9),
(2,CURRENT_DATE+10,CURRENT_DATE+10,'Sick','approved',10),
(3,CURRENT_DATE+12,CURRENT_DATE+13,'Casual','pending',20),
(5,CURRENT_DATE+15,CURRENT_DATE+16,'Annual','approved',9),
(6,CURRENT_DATE+3,CURRENT_DATE+3,'Sick','rejected',10),
(7,CURRENT_DATE+20,CURRENT_DATE+22,'Casual','pending',20),
(8,CURRENT_DATE+8,CURRENT_DATE+9,'Annual','approved',22),
(9,CURRENT_DATE+25,CURRENT_DATE+26,'Casual','pending',4),
(10,CURRENT_DATE+7,CURRENT_DATE+7,'Sick','approved',4),
(11,CURRENT_DATE+14,CURRENT_DATE+15,'Casual','pending',15),
(12,CURRENT_DATE+9,CURRENT_DATE+10,'Annual','approved',9),
(13,CURRENT_DATE+18,CURRENT_DATE+18,'Sick','rejected',20),
(14,CURRENT_DATE+11,CURRENT_DATE+12,'Casual','pending',22),
(15,CURRENT_DATE+30,CURRENT_DATE+32,'Annual','approved',4),
(16,CURRENT_DATE+4,CURRENT_DATE+4,'Sick','pending',9),
(17,CURRENT_DATE+16,CURRENT_DATE+17,'Casual','approved',4),
(18,CURRENT_DATE+21,CURRENT_DATE+21,'Sick','pending',10),
(19,CURRENT_DATE+13,CURRENT_DATE+14,'Annual','rejected',9),
(20,CURRENT_DATE+28,CURRENT_DATE+29,'Casual','pending',4),
(21,CURRENT_DATE+6,CURRENT_DATE+6,'Sick','approved',4);


-- 4. AUDIT EVENTS (25 RECORDS)

INSERT INTO audit_events
(actor_id,action,result,trace_id)
VALUES
(1,'LOGIN','SUCCESS','TRACE001'),
(2,'LOGIN','SUCCESS','TRACE002'),
(3,'LOGIN','SUCCESS','TRACE003'),
(4,'ADMIN_LOGIN','SUCCESS','TRACE004'),
(5,'LOGIN','SUCCESS','TRACE005'),
(6,'VIEW_PROFILE','SUCCESS','TRACE006'),
(7,'VIEW_LEAVE_BALANCE','SUCCESS','TRACE007'),
(8,'LOGIN','SUCCESS','TRACE008'),
(9,'APPROVE_LEAVE','SUCCESS','TRACE009'),
(10,'REJECT_LEAVE','SUCCESS','TRACE010'),
(11,'LOGIN','SUCCESS','TRACE011'),
(12,'VIEW_PROFILE','SUCCESS','TRACE012'),
(13,'VIEW_LEAVE_BALANCE','SUCCESS','TRACE013'),
(14,'LOGIN','SUCCESS','TRACE014'),
(15,'APPROVE_LEAVE','SUCCESS','TRACE015'),
(16,'LOGIN','SUCCESS','TRACE016'),
(17,'VIEW_PROFILE','SUCCESS','TRACE017'),
(18,'CREATE_LEAVE_REQUEST','SUCCESS','TRACE018'),
(19,'LOGIN','SUCCESS','TRACE019'),
(20,'APPROVE_LEAVE','SUCCESS','TRACE020'),
(21,'LOGIN','SUCCESS','TRACE021'),
(22,'VIEW_PROFILE','SUCCESS','TRACE022'),
(23,'CREATE_LEAVE_REQUEST','SUCCESS','TRACE023'),
(24,'LOGIN','SUCCESS','TRACE024'),
(25,'VIEW_LEAVE_BALANCE','SUCCESS','TRACE025');