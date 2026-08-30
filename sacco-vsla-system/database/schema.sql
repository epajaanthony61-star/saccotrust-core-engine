-- SACCO & VSLA Management System Database Schema
-- Tailored for Ugandan Financial Ecosystem
-- Supports UGX currency, Mobile Money integration, and regulatory compliance

-- Enable UUID extension if using PostgreSQL
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- ENUMS AND TYPES
-- ============================================

CREATE TYPE member_status AS ENUM ('active', 'inactive', 'suspended', 'deceased');
CREATE TYPE loan_status AS ENUM ('pending', 'approved', 'disbursed', 'repaying', 'completed', 'defaulted', 'rejected');
CREATE TYPE transaction_type AS ENUM ('deposit', 'withdrawal', 'loan_disbursement', 'loan_repayment', 'fine', 'dividend', 'transfer');
CREATE_TYPE mobile_money_provider AS ENUM ('mtn_momo', 'airtel_money', 'humans_ux');
CREATE TYPE repayment_frequency AS ENUM ('weekly', 'bi_weekly', 'monthly');

-- ============================================
-- CORE TABLES
-- ============================================

-- Groups/SACCOs/VSLAs
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    registration_number VARCHAR(100) UNIQUE NOT NULL,
    group_type VARCHAR(50) NOT NULL CHECK (group_type IN ('sacco', 'vsla', 'cooperative')),
    district VARCHAR(100) NOT NULL,
    sub_county VARCHAR(100),
    village VARCHAR(100),
    contact_phone VARCHAR(20) NOT NULL,
    contact_email VARCHAR(255),
    registration_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status member_status DEFAULT 'active',
    total_members INTEGER DEFAULT 0,
    total_savings DECIMAL(20,2) DEFAULT 0.00,
    total_loans_outstanding DECIMAL(20,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Members
CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    membership_number VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'other')),
    national_id_number VARCHAR(50) UNIQUE,
    tin_number VARCHAR(50),
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    district VARCHAR(100),
    sub_county VARCHAR(100),
    village VARCHAR(100),
    next_of_kin_name VARCHAR(200),
    next_of_kin_phone VARCHAR(20),
    next_of_kin_relationship VARCHAR(50),
    join_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status member_status DEFAULT 'active',
    total_savings DECIMAL(20,2) DEFAULT 0.00,
    total_borrowed DECIMAL(20,2) DEFAULT 0.00,
    credit_score INTEGER DEFAULT 0,
    shares_owned INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, membership_number)
);

-- Member Savings/Shares
CREATE TABLE savings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount DECIMAL(20,2) NOT NULL CHECK (amount > 0),
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('weekly_contribution', 'share_purchase', 'voluntary_saving', 'withdrawal')),
    payment_method VARCHAR(50) DEFAULT 'cash' CHECK (payment_method IN ('cash', 'mtn_momo', 'airtel_money', 'bank_transfer')),
    mobile_money_reference VARCHAR(100),
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    notes TEXT,
    recorded_by UUID REFERENCES members(id),
    verified_by UUID REFERENCES members(id),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(member_id, week_number, year, transaction_type)
);

-- Loans
CREATE TABLE loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    loan_number VARCHAR(50) UNIQUE NOT NULL,
    principal_amount DECIMAL(20,2) NOT NULL CHECK (principal_amount > 0),
    interest_rate DECIMAL(5,2) NOT NULL DEFAULT 10.00,
    interest_amount DECIMAL(20,2) NOT NULL,
    total_repayable DECIMAL(20,2) NOT NULL,
    amount_paid DECIMAL(20,2) DEFAULT 0.00,
    outstanding_balance DECIMAL(20,2) NOT NULL,
    purpose TEXT,
    guarantors JSONB, -- Array of member IDs guaranteeing the loan
    collateral_description TEXT,
    application_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approval_date TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES members(id),
    disbursement_date TIMESTAMP WITH TIME ZONE,
    disbursement_method VARCHAR(50) DEFAULT 'cash' CHECK (disbursement_method IN ('cash', 'mtn_momo', 'airtel_money', 'bank_transfer')),
    mobile_money_reference VARCHAR(100),
    due_date DATE NOT NULL,
    status loan_status DEFAULT 'pending',
    repayment_frequency repayment_frequency DEFAULT 'monthly',
    number_of_installments INTEGER NOT NULL DEFAULT 12,
    penalty_rate DECIMAL(5,2) DEFAULT 2.00,
    total_penalties DECIMAL(20,2) DEFAULT 0.00,
    credit_score_at_approval INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Loan Repayments
CREATE TABLE loan_repayments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    repayment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount_paid DECIMAL(20,2) NOT NULL CHECK (amount_paid > 0),
    principal_portion DECIMAL(20,2) NOT NULL,
    interest_portion DECIMAL(20,2) NOT NULL,
    penalty_portion DECIMAL(20,2) DEFAULT 0.00,
    payment_method VARCHAR(50) DEFAULT 'cash' CHECK (payment_method IN ('cash', 'mtn_momo', 'airtel_money', 'bank_transfer')),
    mobile_money_reference VARCHAR(100),
    installment_number INTEGER NOT NULL,
    recorded_by UUID REFERENCES members(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transactions (General Ledger)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE SET NULL,
    transaction_type transaction_type NOT NULL,
    amount DECIMAL(20,2) NOT NULL,
    balance_after DECIMAL(20,2),
    reference_id UUID, -- Links to savings, loans, or loan_repayments
    reference_type VARCHAR(50), -- 'savings', 'loan', 'loan_repayment'
    payment_method VARCHAR(50) DEFAULT 'cash',
    mobile_money_provider mobile_money_provider,
    mobile_money_transaction_id VARCHAR(100),
    description TEXT,
    recorded_by UUID REFERENCES members(id),
    verified_by UUID REFERENCES members(id),
    is_verified BOOLEAN DEFAULT FALSE,
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- SMS Notifications Log
CREATE TABLE sms_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    message_type VARCHAR(50) NOT NULL CHECK (message_type IN ('contribution_reminder', 'loan_due_reminder', 'overdue_notice', 'disbursement_confirmation', 'repayment_confirmation', 'welcome_message')),
    message_content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed')),
    provider_response TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Credit Scores History
CREATE TABLE credit_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 1000),
    risk_category VARCHAR(20) NOT NULL CHECK (risk_category IN ('excellent', 'good', 'fair', 'poor', 'very_poor')),
    max_loan_eligible DECIMAL(20,2) NOT NULL,
    calculation_factors JSONB, -- Stores factors used in calculation
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Trail
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES members(id),
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Meeting Attendance (for VSLA weekly meetings)
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    meeting_date DATE NOT NULL,
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    location VARCHAR(255),
    agenda TEXT,
    total_attendance INTEGER DEFAULT 0,
    total_contributions DECIMAL(20,2) DEFAULT 0.00,
    notes TEXT,
    recorded_by UUID REFERENCES members(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, week_number, year)
);

CREATE TABLE meeting_attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    attendance_status VARCHAR(20) DEFAULT 'present' CHECK (attendance_status IN ('present', 'absent', 'late')),
    contribution_amount DECIMAL(20,2) DEFAULT 0.00,
    fines_amount DECIMAL(20,2) DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(meeting_id, member_id)
);

-- Users (for system access - treasurers, chairpersons, etc.)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID UNIQUE REFERENCES members(id) ON DELETE CASCADE,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'treasurer', 'chairperson', 'secretary', 'member', 'auditor')),
    permissions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    must_change_password BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API Integration Logs (Mobile Money)
CREATE TABLE api_integration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider mobile_money_provider NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    request_method VARCHAR(10) NOT NULL,
    request_body JSONB,
    response_body JSONB,
    status_code INTEGER,
    transaction_reference VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dividends Distribution
CREATE TABLE dividends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    financial_year INTEGER NOT NULL,
    distribution_date DATE NOT NULL,
    total_amount DECIMAL(20,2) NOT NULL,
    dividend_per_share DECIMAL(10,4) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'distributed', 'cancelled')),
    approved_by UUID REFERENCES members(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dividend_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dividend_id UUID NOT NULL REFERENCES dividends(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    shares_count INTEGER NOT NULL,
    dividend_amount DECIMAL(20,2) NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'cash',
    mobile_money_reference VARCHAR(100),
    paid BOOLEAN DEFAULT FALSE,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_members_group ON members(group_id);
CREATE INDEX idx_members_status ON members(status);
CREATE INDEX idx_savings_member ON savings(member_id);
CREATE INDEX idx_savings_group ON savings(group_id);
CREATE INDEX idx_savings_date ON savings(transaction_date);
CREATE INDEX idx_loans_member ON loans(member_id);
CREATE INDEX idx_loans_group ON loans(group_id);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_loan_repayments_loan ON loan_repayments(loan_id);
CREATE INDEX idx_transactions_group ON transactions(group_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_sms_member ON sms_notifications(member_id);
CREATE INDEX idx_credit_scores_member ON credit_scores(member_id);
CREATE INDEX idx_audit_logs_group ON audit_logs(group_id);
CREATE INDEX idx_meetings_group ON meetings(group_id);
CREATE INDEX idx_users_member ON users(member_id);

-- ============================================
-- VIEWS FOR REPORTING
-- ============================================

-- Member Summary View
CREATE VIEW member_summary AS
SELECT 
    m.id,
    m.membership_number,
    m.first_name || ' ' || m.last_name AS full_name,
    m.phone_number,
    g.name AS group_name,
    m.status,
    COALESCE(SUM(s.amount), 0) AS total_savings,
    COALESCE((SELECT SUM(principal_amount) FROM loans WHERE member_id = m.id AND status IN ('disbursed', 'repaying')), 0) AS total_loans,
    COALESCE((SELECT SUM(outstanding_balance) FROM loans WHERE member_id = m.id AND status IN ('disbursed', 'repaying')), 0) AS outstanding_balance,
    m.credit_score,
    m.shares_owned
FROM members m
LEFT JOIN groups g ON m.group_id = g.id
LEFT JOIN savings s ON m.id = s.member_id
GROUP BY m.id, g.name;

-- Loan Performance View
CREATE VIEW loan_performance AS
SELECT 
    l.id,
    l.loan_number,
    m.first_name || ' ' || m.last_name AS borrower_name,
    l.principal_amount,
    l.total_repayable,
    l.amount_paid,
    l.outstanding_balance,
    l.status,
    l.due_date,
    CASE 
        WHEN l.due_date < CURRENT_DATE AND l.status != 'completed' THEN 'overdue'
        ELSE 'current'
    END AS loan_status,
    EXTRACT(DAY FROM CURRENT_DATE - l.due_date) AS days_overdue
FROM loans l
JOIN members m ON l.member_id = m.id;

-- Weekly Contributions Summary
CREATE VIEW weekly_contributions_summary AS
SELECT 
    g.id AS group_id,
    g.name AS group_name,
    s.year,
    s.week_number,
    COUNT(DISTINCT s.member_id) AS contributing_members,
    SUM(s.amount) AS total_contributions,
    AVG(s.amount) AS average_contribution
FROM savings s
JOIN groups g ON s.group_id = g.id
WHERE s.transaction_type IN ('weekly_contribution', 'voluntary_saving')
GROUP BY g.id, g.name, s.year, s.week_number
ORDER BY s.year DESC, s.week_number DESC;

-- ============================================
-- TRIGGERS FOR AUTOMATION
-- ============================================

-- Update group totals trigger
CREATE OR REPLACE FUNCTION update_group_totals()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF TG_TABLE_NAME = 'savings' THEN
            UPDATE groups 
            SET total_savings = total_savings + NEW.amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.group_id;
            
            UPDATE members 
            SET total_savings = total_savings + NEW.amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.member_id;
        ELSIF TG_TABLE_NAME = 'loans' AND NEW.status = 'disbursed' THEN
            UPDATE groups 
            SET total_loans_outstanding = total_loans_outstanding + NEW.principal_amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.group_id;
            
            UPDATE members 
            SET total_borrowed = total_borrowed + NEW.principal_amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.member_id;
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        IF TG_TABLE_NAME = 'loans' THEN
            IF OLD.status != 'disbursed' AND NEW.status = 'disbursed' THEN
                UPDATE groups 
                SET total_loans_outstanding = total_loans_outstanding + NEW.principal_amount,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.group_id;
            ELSIF OLD.status IN ('disbursed', 'repaying') AND NEW.status = 'completed' THEN
                UPDATE groups 
                SET total_loans_outstanding = total_loans_outstanding - OLD.outstanding_balance,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.group_id;
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_group_totals_savings
AFTER INSERT ON savings
FOR EACH ROW EXECUTE FUNCTION update_group_totals();

CREATE TRIGGER trg_update_group_totals_loans
AFTER INSERT OR UPDATE ON loans
FOR EACH ROW EXECUTE FUNCTION update_group_totals();

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_members_timestamp
BEFORE UPDATE ON members
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_update_groups_timestamp
BEFORE UPDATE ON groups
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_update_loans_timestamp
BEFORE UPDATE ON loans
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- INITIAL DATA (Optional)
-- ============================================

-- Insert a default admin user (password should be hashed in production)
-- INSERT INTO users (username, password_hash, role) 
-- VALUES ('admin', '$2b$10$...', 'admin');

COMMENT ON DATABASE sacco_vsla_system IS 'SACCO and VSLA Management System for Uganda - Supports UGX, Mobile Money integration, and regulatory compliance';
