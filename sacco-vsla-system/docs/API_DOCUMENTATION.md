# SACCO & VSLA Management System - REST API Documentation

## Base URL
```
/api/v1
```

## Authentication
All endpoints require JWT authentication except `/auth/login` and `/auth/register`.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## Authentication Endpoints

### POST /auth/register
Register a new user (group admin/treasurer)

**Request Body:**
```json
{
  "username": "treasurer_kampala",
  "password": "SecurePassword123!",
  "email": "treasurer@sacco.ug",
  "group_id": "uuid",
  "role": "treasurer"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user_id": "uuid",
    "username": "treasurer_kampala"
  }
}
```

### POST /auth/login
Login and receive JWT token

**Request Body:**
```json
{
  "username": "treasurer_kampala",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "access_token": "jwt_token_here",
    "refresh_token": "refresh_token_here",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "username": "treasurer_kampala",
      "role": "treasurer",
      "group_id": "uuid"
    }
  }
}
```

### POST /auth/refresh
Refresh access token

**Request Body:**
```json
{
  "refresh_token": "refresh_token_here"
}
```

---

## Groups/SACCOs/VSLAs Endpoints

### GET /groups
List all groups (admin only) or current user's group

**Query Parameters:**
- `page` (integer): Page number
- `limit` (integer): Items per page
- `status` (string): Filter by status
- `group_type` (string): Filter by type (sacco, vsla, cooperative)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "groups": [
      {
        "id": "uuid",
        "name": "Kampala SACCO",
        "registration_number": "SACCO-UG-001",
        "group_type": "sacco",
        "district": "Kampala",
        "total_members": 150,
        "total_savings": 45000000.00,
        "total_loans_outstanding": 25000000.00,
        "status": "active"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 50
    }
  }
}
```

### GET /groups/:id
Get specific group details

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Kampala SACCO",
    "registration_number": "SACCO-UG-001",
    "group_type": "sacco",
    "district": "Kampala",
    "sub_county": "Central",
    "village": "Nakasero",
    "contact_phone": "+256700000000",
    "contact_email": "info@kampalasacco.ug",
    "registration_date": "2020-01-15",
    "status": "active",
    "total_members": 150,
    "total_savings": 45000000.00,
    "total_loans_outstanding": 25000000.00
  }
}
```

### POST /groups
Create a new group

**Request Body:**
```json
{
  "name": "Entebbe VSLA Group",
  "registration_number": "VSLA-UG-025",
  "group_type": "vsla",
  "district": "Wakiso",
  "sub_county": "Entebbe Municipality",
  "village": "Kigungu",
  "contact_phone": "+256700000000",
  "contact_email": "entebbe@vsla.ug"
}
```

### PUT /groups/:id
Update group information

### DELETE /groups/:id
Delete a group (soft delete)

---

## Members Endpoints

### GET /members
List all members in the group

**Query Parameters:**
- `page`, `limit`: Pagination
- `status`: Filter by status (active, inactive, suspended)
- `search`: Search by name or membership number

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "members": [
      {
        "id": "uuid",
        "membership_number": "MEM-001",
        "first_name": "John",
        "last_name": "Mukasa",
        "phone_number": "+256700000000",
        "status": "active",
        "total_savings": 3500000.00,
        "total_borrowed": 2000000.00,
        "credit_score": 750,
        "shares_owned": 50
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 10,
      "total_items": 150
    }
  }
}
```

### GET /members/:id
Get member details with full profile

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "membership_number": "MEM-001",
    "first_name": "John",
    "last_name": "Mukasa",
    "date_of_birth": "1985-05-15",
    "gender": "male",
    "national_id_number": "CF123456789012",
    "phone_number": "+256700000000",
    "email": "john.mukasa@email.com",
    "district": "Kampala",
    "next_of_kin_name": "Sarah Mukasa",
    "next_of_kin_phone": "+256700000001",
    "join_date": "2020-03-01",
    "status": "active",
    "total_savings": 3500000.00,
    "total_borrowed": 2000000.00,
    "credit_score": 750,
    "shares_owned": 50
  }
}
```

### POST /members
Add a new member

**Request Body:**
```json
{
  "membership_number": "MEM-151",
  "first_name": "Grace",
  "last_name": "Nalubega",
  "date_of_birth": "1990-08-20",
  "gender": "female",
  "national_id_number": "CM987654321098",
  "phone_number": "+256700000002",
  "email": "grace.n@email.com",
  "district": "Kampala",
  "sub_county": "Rubaga",
  "village": "Mengo",
  "next_of_kin_name": "Peter Nalubega",
  "next_of_kin_phone": "+256700000003",
  "next_of_kin_relationship": "spouse"
}
```

### PUT /members/:id
Update member information

### DELETE /members/:id
Deactivate a member

### GET /members/:id/savings
Get member's savings history

### GET /members/:id/loans
Get member's loan history

### GET /members/:id/credit-score
Get member's credit score and eligibility

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "member_id": "uuid",
    "current_score": 750,
    "risk_category": "good",
    "max_loan_eligible": 10000000.00,
    "calculation_factors": {
      "savings_history": 300,
      "repayment_history": 350,
      "membership_duration": 100,
      "attendance": 50,
      "share_ownership": 50
    },
    "calculated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Savings/Contributions Endpoints

### GET /savings
List all savings transactions

**Query Parameters:**
- `member_id`: Filter by member
- `week_number`: Filter by week
- `year`: Filter by year
- `transaction_type`: Filter by type
- `start_date`, `end_date`: Date range

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "savings": [
      {
        "id": "uuid",
        "member_id": "uuid",
        "member_name": "John Mukasa",
        "amount": 50000.00,
        "transaction_type": "weekly_contribution",
        "payment_method": "mtn_momo",
        "mobile_money_reference": "MOB123456789",
        "week_number": 3,
        "year": 2024,
        "transaction_date": "2024-01-15",
        "is_verified": true
      }
    ]
  }
}
```

### POST /savings
Record a new savings contribution

**Request Body:**
```json
{
  "member_id": "uuid",
  "amount": 50000.00,
  "transaction_type": "weekly_contribution",
  "payment_method": "mtn_momo",
  "mobile_money_reference": "MOB123456789",
  "week_number": 3,
  "year": 2024,
  "notes": "Regular weekly contribution"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Contribution recorded successfully",
  "data": {
    "id": "uuid",
    "member_id": "uuid",
    "amount": 50000.00,
    "transaction_type": "weekly_contribution",
    "week_number": 3,
    "year": 2024,
    "new_total_savings": 3550000.00
  }
}
```

### POST /savings/bulk
Record multiple contributions at once (for weekly meetings)

**Request Body:**
```json
{
  "meeting_id": "uuid",
  "week_number": 3,
  "year": 2024,
  "contributions": [
    {
      "member_id": "uuid",
      "amount": 50000.00,
      "payment_method": "cash"
    },
    {
      "member_id": "uuid",
      "amount": 100000.00,
      "payment_method": "mtn_momo",
      "mobile_money_reference": "MOB123456789"
    }
  ]
}
```

### GET /savings/summary
Get savings summary for the group

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "total_savings": 45000000.00,
    "total_contributors": 145,
    "average_contribution": 310344.83,
    "this_week_contributions": 7250000.00,
    "last_week_contributions": 7100000.00,
    "growth_percentage": 2.11
  }
}
```

---

## Loans Endpoints

### GET /loans
List all loans

**Query Parameters:**
- `member_id`: Filter by member
- `status`: Filter by status
- `start_date`, `end_date`: Date range

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "loans": [
      {
        "id": "uuid",
        "loan_number": "LN-2024-001",
        "member_id": "uuid",
        "member_name": "John Mukasa",
        "principal_amount": 2000000.00,
        "interest_rate": 10.00,
        "total_repayable": 2200000.00,
        "outstanding_balance": 1100000.00,
        "status": "repaying",
        "due_date": "2024-12-31",
        "disbursement_date": "2024-01-15"
      }
    ]
  }
}
```

### GET /loans/:id
Get specific loan details

### POST /loans
Apply for a new loan

**Request Body:**
```json
{
  "member_id": "uuid",
  "principal_amount": 3000000.00,
  "purpose": "School fees",
  "repayment_frequency": "monthly",
  "number_of_installments": 12,
  "guarantors": ["uuid1", "uuid2"],
  "collateral_description": "Motorcycle title"
}
```

### PUT /loans/:id/approve
Approve a loan application

**Request Body:**
```json
{
  "approved_by": "uuid",
  "notes": "Approved based on good credit history"
}
```

### PUT /loans/:id/reject
Reject a loan application

**Request Body:**
```json
{
  "rejected_by": "uuid",
  "reason": "Insufficient savings collateral"
}
```

### POST /loans/:id/disburse
Disburse an approved loan

**Request Body:**
```json
{
  "disbursement_method": "mtn_momo",
  "mobile_money_number": "+256700000000",
  "notes": "Disbursed via MTN Mobile Money"
}
```

### GET /loans/:id/eligibility
Check loan eligibility for a member

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "member_id": "uuid",
    "is_eligible": true,
    "max_loan_amount": 10000000.00,
    "recommended_amount": 5000000.00,
    "factors": {
      "total_savings": 3500000.00,
      "savings_multiplier": 3,
      "credit_score": 750,
      "existing_loans": 0,
      "repayment_capacity": "excellent"
    }
  }
}
```

---

## Loan Repayments Endpoints

### GET /loan-repayments
List all loan repayments

### POST /loan-repayments
Record a loan repayment

**Request Body:**
```json
{
  "loan_id": "uuid",
  "amount_paid": 200000.00,
  "payment_method": "mtn_momo",
  "mobile_money_reference": "MOB987654321",
  "installment_number": 5,
  "notes": "Monthly installment"
}
```

### GET /loans/:id/repayment-schedule
Get loan repayment schedule

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "loan_id": "uuid",
    "loan_number": "LN-2024-001",
    "total_repayable": 2200000.00,
    "installments": [
      {
        "installment_number": 1,
        "due_date": "2024-02-15",
        "amount_due": 183333.33,
        "principal_portion": 166666.67,
        "interest_portion": 16666.66,
        "status": "paid",
        "paid_date": "2024-02-14"
      },
      {
        "installment_number": 2,
        "due_date": "2024-03-15",
        "amount_due": 183333.33,
        "principal_portion": 166666.67,
        "interest_portion": 16666.66,
        "status": "paid",
        "paid_date": "2024-03-13"
      }
    ]
  }
}
```

---

## Meetings Endpoints (VSLA)

### GET /meetings
List all meetings

### POST /meetings
Create a new meeting

**Request Body:**
```json
{
  "meeting_date": "2024-01-15",
  "week_number": 3,
  "year": 2024,
  "location": "Community Hall",
  "agenda": "Weekly contributions and loan applications review"
}
```

### POST /meetings/:id/attendance
Record attendance for a meeting

**Request Body:**
```json
{
  "attendances": [
    {
      "member_id": "uuid",
      "attendance_status": "present",
      "contribution_amount": 50000.00
    },
    {
      "member_id": "uuid",
      "attendance_status": "absent",
      "fines_amount": 5000.00
    }
  ]
}
```

---

## Mobile Money Integration Endpoints

### POST /mobile-money/deposit
Initiate mobile money deposit (callback from provider)

**Request Body:**
```json
{
  "provider": "mtn_momo",
  "transaction_id": "MOB123456789",
  "amount": 50000.00,
  "phone_number": "+256700000000",
  "status": "completed",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### POST /mobile-money/disburse
Disburse funds via mobile money

**Request Body:**
```json
{
  "recipient_phone": "+256700000000",
  "amount": 2000000.00,
  "purpose": "loan_disbursement",
  "reference_id": "uuid",
  "narration": "Loan disbursement - LN-2024-001"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Disbursement initiated",
  "data": {
    "transaction_id": "MOB987654321",
    "status": "pending",
    "estimated_completion": "2024-01-15T10:35:00Z"
  }
}
```

### GET /mobile-money/status/:transaction_id
Check mobile money transaction status

---

## SMS Notifications Endpoints

### POST /sms/send
Send SMS notification

**Request Body:**
```json
{
  "member_id": "uuid",
  "message_type": "loan_due_reminder",
  "custom_message": "Dear John, your loan installment of UGX 183,333 is due on 2024-02-15. Pay now to avoid penalties."
}
```

### POST /sms/bulk/send
Send bulk SMS notifications

**Request Body:**
```json
{
  "message_type": "contribution_reminder",
  "recipient_group": "all_members",
  "custom_message": "Reminder: Weekly meeting this Friday at 5 PM. Bring your contributions."
}
```

### GET /sms/logs
Get SMS notification logs

---

## Credit Scoring Endpoints

### POST /credit-scores/calculate
Manually trigger credit score calculation for a member

**Request Body:**
```json
{
  "member_id": "uuid"
}
```

### GET /credit-scores/:member_id
Get member's credit score history

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "member_id": "uuid",
    "scores": [
      {
        "score": 750,
        "risk_category": "good",
        "max_loan_eligible": 10000000.00,
        "calculated_at": "2024-01-15T10:30:00Z"
      },
      {
        "score": 720,
        "risk_category": "good",
        "max_loan_eligible": 9000000.00,
        "calculated_at": "2023-12-15T10:30:00Z"
      }
    ]
  }
}
```

### POST /credit-scores/batch-calculate
Calculate credit scores for all members

---

## Reports Endpoints

### GET /reports/audit
Generate audit report (PDF)

**Query Parameters:**
- `start_date`, `end_date`: Date range
- `report_type`: comprehensive, summary, transactions

**Response:** `200 OK`
Returns PDF file or download link

```json
{
  "success": true,
  "data": {
    "report_url": "https://storage.example.com/reports/audit-2024-01.pdf",
    "generated_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-22T10:30:00Z"
  }
}
```

### GET /reports/member-statement/:member_id
Generate member statement (PDF)

### GET /reports/loan-performance
Generate loan performance report

### GET /reports/contributions-summary
Generate weekly/monthly contributions summary

### GET /reports/outstanding-loans
Generate outstanding loans report

---

## Dividends Endpoints

### POST /dividends
Declare dividends for a financial year

**Request Body:**
```json
{
  "financial_year": 2024,
  "distribution_date": "2024-12-31",
  "total_amount": 10000000.00,
  "notes": "Annual dividend distribution"
}
```

### POST /dividends/:id/distribute
Distribute dividends to members

### GET /dividends
List all dividend distributions

---

## Settings Endpoints

### GET /settings
Get system settings

### PUT /settings
Update system settings

**Request Body:**
```json
{
  "interest_rate": 10.00,
  "penalty_rate": 2.00,
  "minimum_contribution": 10000.00,
  "savings_loan_multiplier": 3,
  "sms_enabled": true,
  "mobile_money_enabled": true
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

### Common Error Codes:
- `UNAUTHORIZED`: Invalid or missing authentication
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid input data
- `INSUFFICIENT_FUNDS`: Not enough balance
- `LOAN_INELIGIBLE`: Member not eligible for loan
- `MOBILE_MONEY_ERROR`: Mobile money API error
- `DUPLICATE_ENTRY`: Record already exists

---

## Rate Limiting

- Standard endpoints: 100 requests per minute
- SMS endpoints: 10 requests per minute
- Mobile money endpoints: 20 requests per minute

Headers returned:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642234567
```

---

## Webhooks

The system supports webhooks for:
- Mobile money transaction callbacks
- SMS delivery notifications
- External audit systems

Configure webhook URLs in system settings.
