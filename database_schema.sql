-- Run this entirely in the Supabase SQL Editor

-- 1. Create Tables
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT UNIQUE NOT NULL,
    telegram_chat_id TEXT UNIQUE,
    wallet_balance_inr NUMERIC DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.workers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    upi_id TEXT,
    status TEXT DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED, SUSPENDED
    rating NUMERIC DEFAULT 5.0,
    tasks_completed INTEGER DEFAULT 0,
    balance_inr NUMERIC DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id),
    worker_id UUID REFERENCES public.workers(id),
    query TEXT NOT NULL,
    tier TEXT,
    quote_inr NUMERIC,
    turnaround_mins INTEGER,
    status TEXT DEFAULT 'QUOTE_PREPARED', -- QUOTE_PREPARED, ESCROW_LOCKED, CLAIMED, DELIVERED, APPROVED_PAID_OUT
    target_worker_name TEXT,
    ai_reasoning TEXT,
    deliverable JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id),
    worker_id UUID REFERENCES public.workers(id),
    task_id UUID REFERENCES public.tasks(id),
    type TEXT NOT NULL, -- TOP_UP, ESCROW_LOCK, ESCROW_RELEASE, ESCROW_REFUND
    amount_inr NUMERIC NOT NULL,
    stripe_payment_id TEXT,
    status TEXT DEFAULT 'COMPLETED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Disable Row Level Security (RLS) for Prototype Backend Access
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.workers DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions DISABLE ROW LEVEL SECURITY;

-- 3. Insert the default Admin User
INSERT INTO public.users (phone_number, wallet_balance_inr) 
VALUES ('+917015960679', 5000) 
ON CONFLICT (phone_number) DO NOTHING;
