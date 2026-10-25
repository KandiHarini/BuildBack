PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(30) NOT NULL DEFAULT 'user',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS materials (
  material_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title VARCHAR(150) NOT NULL,
  category VARCHAR(100) NOT NULL,
  description TEXT,
  quantity FLOAT NOT NULL,
  unit VARCHAR(30) NOT NULL,
  condition VARCHAR(50) NOT NULL,
  location VARCHAR(200) NOT NULL,
  price NUMERIC(10,2) DEFAULT 0,
  is_free BOOLEAN DEFAULT 0,
  image_path VARCHAR(255),
  availability_status VARCHAR(30) DEFAULT 'available',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS requests (
  request_id INTEGER PRIMARY KEY AUTOINCREMENT,
  material_id INTEGER NOT NULL,
  seeker_id INTEGER NOT NULL,
  message TEXT,
  requested_quantity FLOAT NOT NULL,
  status VARCHAR(30) DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(material_id) REFERENCES materials(material_id),
  FOREIGN KEY(seeker_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS transactions (
  transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL UNIQUE,
  status VARCHAR(30) DEFAULT 'pending',
  collection_date DATE,
  confirmed_at DATETIME,
  FOREIGN KEY(request_id) REFERENCES requests(request_id)
);

CREATE TABLE IF NOT EXISTS impact_records (
  record_id INTEGER PRIMARY KEY AUTOINCREMENT,
  transaction_id INTEGER NOT NULL UNIQUE,
  quantity_reused FLOAT NOT NULL,
  unit VARCHAR(30) NOT NULL,
  calculation_note TEXT,
  recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(transaction_id) REFERENCES transactions(transaction_id)
);

CREATE TABLE IF NOT EXISTS notifications (
  notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(user_id)
);
