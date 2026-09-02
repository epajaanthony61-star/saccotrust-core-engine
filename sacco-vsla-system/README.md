# SACCO & VSLA Management System

A secure, comprehensive management system tailored for Savings and Credit Cooperatives (SACCOs) and Village Savings and Loans Associations (VSLAs) in Uganda.

## Features

### Core Functionality
- **Member Management**: Register members, track savings, and manage profiles
- **Weekly Contributions**: Log UGX contributions with week/year tracking
- **Loan Management**: Application, approval, disbursement, and repayment tracking
- **Automated Credit Scoring**: Algorithm-based scoring using repayment history, savings patterns, and attendance
- **Mobile Money Integration**: Direct deposits and disbursements via MTN MoMo and Airtel Money
- **SMS Notifications**: Automated reminders for contributions and loan repayments
- **PDF Audit Reports**: Transparent, downloadable financial reports
- **Meeting Management**: Track VSLA weekly meeting attendance and contributions

### Security Features
- JWT-based authentication with refresh tokens
- Role-based access control (Admin, Treasurer, Chairperson, Secretary, Member, Auditor)
- Two-factor authentication support
- Comprehensive audit logging
- Password hashing with bcrypt
- Account lockout after failed login attempts

### Ugandan Context
- UGX currency support throughout
- Integration with local mobile money providers (MTN, Airtel)
- Support for National ID and TIN numbers
- District/Sub-county/Village address structure
- Compliance with Ugandan SACCO regulations

## Technology Stack

- **Database**: PostgreSQL (recommended) or MySQL
- **Backend**: Python/Node.js (implementation flexible)
- **API**: RESTful endpoints
- **Authentication**: JWT tokens
- **SMS**: Africa's Talking API
- **Mobile Money**: MTN MoMo API, Airtel Money API
- **PDF Generation**: ReportLab or similar

## Project Structure

```
sacco-vsla-system/
├── database/
│   └── schema.sql              # Complete database schema
├── src/
│   ├── controllers/            # Request handlers
│   ├── services/
│   │   ├── credit_scoring.py   # Credit score calculation
│   │   ├── mobile_money.py     # Mobile money integration
│   │   └── sms_notification.py # SMS reminders
│   ├── models/                 # Database models
│   ├── middleware/             # Auth, validation, logging
│   ├── routes/                 # API route definitions
│   ├── utils/                  # Helper functions
│   └── config/                 # Configuration files
├── docs/
│   └── API_DOCUMENTATION.md    # Complete API reference
├── migrations/                 # Database migrations
└── tests/                      # Test suites
```

## Database Schema

The system uses a relational database with the following main tables:

- `groups` - SACCO/VSLA groups
- `members` - Member profiles and financial summaries
- `savings` - Weekly contributions and savings transactions
- `loans` - Loan applications and status
- `loan_repayments` - Repayment records
- `transactions` - General ledger
- `credit_scores` - Credit score history
- `sms_notifications` - SMS log
- `meetings` - VSLA meeting records
- `users` - System users with roles
- `audit_logs` - Complete audit trail

See `database/schema.sql` for full schema with indexes, triggers, and views.

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/refresh` - Refresh access token

### Members
- `GET /api/v1/members` - List members
- `POST /api/v1/members` - Add member
- `GET /api/v1/members/:id` - Get member details
- `GET /api/v1/members/:id/credit-score` - Get credit score

### Savings
- `GET /api/v1/savings` - List savings transactions
- `POST /api/v1/savings` - Record contribution
- `POST /api/v1/savings/bulk` - Bulk record (weekly meetings)

### Loans
- `GET /api/v1/loans` - List loans
- `POST /api/v1/loans` - Apply for loan
- `PUT /api/v1/loans/:id/approve` - Approve loan
- `POST /api/v1/loans/:id/disburse` - Disburse loan
- `GET /api/v1/loans/:id/eligibility` - Check eligibility

### Mobile Money
- `POST /api/v1/mobile-money/deposit` - Initiate deposit
- `POST /api/v1/mobile-money/disburse` - Disburse funds
- `GET /api/v1/mobile-money/status/:id` - Check status

### SMS
- `POST /api/v1/sms/send` - Send SMS
- `POST /api/v1/sms/bulk/send` - Bulk SMS

### Reports
- `GET /api/v1/reports/audit` - Generate audit PDF
- `GET /api/v1/reports/member-statement/:id` - Member statement
- `GET /api/v1/reports/loan-performance` - Loan report

See `docs/API_DOCUMENTATION.md` for complete endpoint documentation.

## Credit Scoring Algorithm

The automated credit scoring system evaluates members on:

1. **Repayment History (35%)**: On-time payments, defaults, outstanding loans
2. **Savings Consistency (25%)**: Regular weekly contributions over 6 months
3. **Savings Balance (20%)**: Total accumulated savings
4. **Membership Duration (10%)**: Length of membership
5. **Meeting Attendance (10%)**: Participation in VSLA meetings

**Risk Categories:**
- Excellent (800-1000): Can borrow up to 5x savings
- Good (650-799): Can borrow up to 4x savings
- Fair (500-649): Can borrow up to 3x savings
- Poor (300-499): Can borrow up to 2x savings
- Very Poor (0-299): Can borrow only 1x savings

## Mobile Money Integration

Supported providers:
- **MTN Mobile Money**: Collections and disbursements via MTN MoMo API
- **Airtel Money**: Payments and payouts via Airtel Money API

Features:
- Automatic phone number formatting for Uganda (+256)
- Transaction status checking
- Comprehensive API logging
- Sandbox and production environments

## SMS Notifications

Pre-configured message templates for:
- Weekly contribution reminders
- Loan due date reminders (3 days before)
- Overdue payment notices (urgent)
- Loan disbursement confirmations
- Repayment confirmations
- Welcome messages for new members
- Meeting reminders

Provider: Africa's Talking (popular in Uganda)

## Setup Instructions

### Prerequisites
- PostgreSQL 12+ or MySQL 8+
- Python 3.9+ or Node.js 16+
- Redis (for caching and sessions, optional)

### Database Setup

```bash
# Create database
createdb sacco_vsla_system

# Run schema
psql sacco_vsla_system < database/schema.sql
```

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sacco_vsla_system

# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRY=3600

# Mobile Money
MTN_MOMO_USER_ID=your-user-id
MTN_MOMO_API_KEY=your-api-key
MTN_MOMO_TARGET_ENV=sandbox

AIRTEL_CLIENT_ID=your-client-id
AIRTEL_CLIENT_SECRET=your-client-secret

# SMS
AFRICAS_TALKING_API_KEY=your-api-key
AFRICAS_TALKING_USERNAME=sandbox
SMS_SENDER_ID=SACCO

# Application
APP_ENV=development
APP_URL=http://localhost:3000
```

### Install Dependencies

```bash
# Python example
pip install flask jwt psycopg2-binary requests reportlab

# Or Node.js example
npm install express jsonwebtoken pg sequelize nodemailer twilio
```

### Run Application

```bash
# Start server
python src/app.py

# Or with Node.js
npm start
```

## Testing

```bash
# Run tests
pytest tests/

# Or with Node.js
npm test
```

## Security Considerations

1. **Always use HTTPS** in production
2. **Hash passwords** with bcrypt (cost factor 12+)
3. **Implement rate limiting** on authentication endpoints
4. **Validate all inputs** to prevent SQL injection
5. **Use prepared statements** for database queries
6. **Enable CORS** only for trusted domains
7. **Regular security audits** and penetration testing
8. **Backup data** regularly with encryption
9. **Comply with Uganda Data Protection Act**

## Compliance

This system is designed to comply with:
- Uganda Cooperative Societies Act
- Bank of Uganda microfinance regulations
- Uganda Data Protection and Privacy Act
- Anti-Money Laundering (AML) requirements

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Email: support@saccosystem.ug
- Documentation: `/docs` folder

## Credits

Developed for Ugandan SACCOs and VSLAs to promote financial inclusion and transparent group savings management.

---

**Version**: 1.0.0  
**Last Updated**: January 2024
