CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(80) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role VARCHAR(10) NOT NULL CHECK (role IN ('USER','ADMIN')),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS microdata_files (
  id SERIAL PRIMARY KEY,
  guid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  description TEXT,
  file_path TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS submissions (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(100),
  file_path TEXT NOT NULL,
  microdata_guid UUID REFERENCES microdata_files(guid) ON DELETE SET NULL,
  status VARCHAR(10) NOT NULL CHECK (status IN ('PENDING','APPROVED','REJECTED','RUNNING','FINISHED','FAILED')),
  stdout TEXT,
  stderr TEXT,
  exit_code INT,
  logs TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);