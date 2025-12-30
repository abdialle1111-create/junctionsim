-- JunctionSim Database Schema
-- Run this in your Supabase SQL Editor to set up user and transaction tables

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  credits INTEGER DEFAULT 5,
  subscription_tier TEXT DEFAULT 'free',
  subscription_id TEXT,
  subscription_active BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_purchase TIMESTAMP WITH TIME ZONE,
  last_payment TIMESTAMP WITH TIME ZONE,
  total_spent DECIMAL DEFAULT 0,
  subscription_cancelled TIMESTAMP WITH TIME ZONE
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_email TEXT NOT NULL,
  session_id TEXT,
  subscription_id TEXT,
  amount DECIMAL NOT NULL,
  credits_added INTEGER,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  type TEXT NOT NULL,
  status TEXT DEFAULT 'completed'
);

-- Analytics table
CREATE TABLE IF NOT EXISTS analytics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  date DATE NOT NULL,
  daily_revenue DECIMAL DEFAULT 0,
  new_users INTEGER DEFAULT 0,
  active_subscriptions INTEGER DEFAULT 0,
  credits_purchased INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable row level security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;

-- RLS policies for users table
CREATE POLICY "Users can read own data" ON users
  FOR SELECT USING (email = CURRENT_USER);

CREATE POLICY "Service role can manage all users" ON users
  USING (auth.role() = 'service_role');

-- RLS policies for transactions table
CREATE POLICY "Users can read own transactions" ON transactions
  FOR SELECT USING (user_email = CURRENT_USER);

CREATE POLICY "Service role can manage all transactions" ON transactions
  USING (auth.role() = 'service_role');

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_transactions_user_email ON transactions(user_email);
CREATE INDEX IF NOT EXISTS idx_transactions_session_id ON transactions(session_id);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);
