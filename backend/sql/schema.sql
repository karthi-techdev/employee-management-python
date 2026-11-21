-- 1. EMPLOYEES
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    department VARCHAR(100),
    role VARCHAR(50),
    password VARCHAR(255),
    manager_id INTEGER REFERENCES employees(employee_id),
    status VARCHAR(20) DEFAULT 'active'
);

-- 2. HR DOCUMENT METADATA (RAG)
CREATE TABLE hr_documents (
    document_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    version VARCHAR(20),
    section VARCHAR(100),
    effective_date DATE,
    access_level VARCHAR(50),
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. LEAVE BALANCES
CREATE TABLE leave_balances (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id),
    leave_type VARCHAR(50),
    balance INTEGER DEFAULT 0,
    as_of_date DATE,
    UNIQUE(employee_id, leave_type)
);

-- 4. LEAVE REQUESTS
CREATE TABLE leave_requests (
    request_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id),
    start_date DATE,
    end_date DATE,
    leave_type VARCHAR(50),
    status VARCHAR(30) DEFAULT 'pending',
    approver_id INTEGER REFERENCES employees(employee_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. AUDIT EVENTS
CREATE TABLE audit_events (
    event_id SERIAL PRIMARY KEY,
    actor_id INTEGER REFERENCES employees(employee_id),
    action VARCHAR(255),
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result TEXT,
    trace_id VARCHAR(255)
);
