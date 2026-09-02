"""
SMS Notification Service for SACCO/VSLA System
Integrates with Ugandan SMS providers (Africa's Talking, Twilio, etc.)
Sends automated reminders for contributions, loan repayments, and notifications
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import uuid


class SMSNotificationService:
    """
    SMS notification service for member communications.
    Supports Africa's Talking (popular in Uganda) and other providers.
    """
    
    PROVIDERS = {
        'africas_talking': {
            'base_url': 'https://api.africastalking.com/version1',
            'sms_endpoint': '/messaging',
            'username_header': 'apikey'
        },
        'twilio': {
            'base_url': 'https://api.twilio.com/2010-04-01',
            'sms_endpoint': '/Accounts/{account_sid}/Messages.json'
        }
    }
    
    # Message templates
    TEMPLATES = {
        'contribution_reminder': "Dear {name}, this is a reminder to bring your weekly contribution of UGX {amount:,} to the meeting on {date}. Thank you - {group_name}",
        
        'loan_due_reminder': "Dear {name}, your loan installment of UGX {amount:,} is due on {due_date}. Please pay on time to avoid penalties. Loan #{loan_number}. - {group_name}",
        
        'overdue_notice': "URGENT: Dear {name}, your loan payment of UGX {amount:,} is {days_overdue} days overdue. Outstanding: UGX {balance:,}. Pay immediately to avoid further penalties. - {group_name}",
        
        'disbursement_confirmation': "Dear {name}, your loan of UGX {amount:,} has been disbursed to your mobile money account. Ref: {reference}. Repayment starts {due_date}. - {group_name}",
        
        'repayment_confirmation': "Dear {name}, we've received your payment of UGX {amount:,} for loan #{loan_number}. Outstanding balance: UGX {balance:,}. Thank you! - {group_name}",
        
        'welcome_message': "Welcome to {group_name}! Your membership number is {membership_number}. Start saving regularly to build your credit score and access loans. Contact treasurer for help.",
        
        'meeting_reminder': "Reminder: {group_name} meeting tomorrow at {time} at {location}. Agenda: {agenda}. Bring your contributions. Attendance is mandatory.",
        
        'dividend_notification': "Dear {name}, you have dividend payment of UGX {amount:,} ready for collection. Contact the treasurer to receive. Financial year {year}. - {group_name}"
    }
    
    def __init__(self, config: Dict):
        """
        Initialize SMS service with provider credentials.
        
        Args:
            config: Provider configuration
                {
                    'provider': 'africas_talking',
                    'api_key': 'your-api-key',
                    'sender_id': 'SACCO-UG',  # Registered sender ID
                    'phone_numbers': ['+256...']  # For testing
                }
        """
        self.config = config
        self.provider = config.get('provider', 'africas_talking')
        self.session = requests.Session()
    
    def send_contribution_reminder(self, member: Dict, group: Dict, 
                                   amount: Decimal, meeting_date: str) -> Dict:
        """Send weekly contribution reminder"""
        message = self.TEMPLATES['contribution_reminder'].format(
            name=member['first_name'],
            amount=float(amount),
            date=meeting_date,
            group_name=group['name']
        )
        
        return self.send_sms(
            phone_number=member['phone_number'],
            message=message,
            message_type='contribution_reminder',
            member_id=member['id']
        )
    
    def send_loan_due_reminder(self, member: Dict, loan: Dict, 
                              group: Dict, days_before: int = 3) -> Dict:
        """Send loan repayment reminder before due date"""
        due_date = loan.get('due_date')
        if not due_date:
            raise ValueError("Loan missing due_date")
        
        message = self.TEMPLATES['loan_due_reminder'].format(
            name=member['first_name'],
            amount=float(loan.get('amount_paid', 0)),
            due_date=due_date,
            loan_number=loan.get('loan_number'),
            group_name=group['name']
        )
        
        return self.send_sms(
            phone_number=member['phone_number'],
            message=message,
            message_type='loan_due_reminder',
            member_id=member['id'],
            reference_id=loan['id']
        )
    
    def send_overdue_notice(self, member: Dict, loan: Dict, 
                           group: Dict, days_overdue: int) -> Dict:
        """Send urgent overdue payment notice"""
        message = self.TEMPLATES['overdue_notice'].format(
            name=member['first_name'],
            amount=float(loan.get('outstanding_balance', 0)),
            days_overdue=days_overdue,
            balance=float(loan.get('outstanding_balance', 0)),
            group_name=group['name']
        )
        
        return self.send_sms(
            phone_number=member['phone_number'],
            message=message,
            message_type='overdue_notice',
            member_id=member['id'],
            reference_id=loan['id'],
            priority='high'
        )
    
    def send_disbursement_confirmation(self, member: Dict, loan: Dict,
                                      group: Dict, amount: Decimal,
                                      reference: str) -> Dict:
        """Send confirmation when loan is disbursed"""
        message = self.TEMPLATES['disbursement_confirmation'].format(
            name=member['first_name'],
            amount=float(amount),
            reference=reference,
            due_date=loan.get('due_date'),
            group_name=group['name']
        )
        
        return self.send_sms(
            phone_number=member['phone_number'],
            message=message,
            message_type='disbursement_confirmation',
            member_id=member['id'],
            reference_id=loan['id']
        )
    
    def send_repayment_confirmation(self, member: Dict, loan: Dict,
                                   group: Dict, amount: Decimal,
                                   balance: Decimal) -> Dict:
        """Send confirmation when repayment is received"""
        message = self.TEMPLATES['repayment_confirmation'].format(
            name=member['first_name'],
            amount=float(amount),
            loan_number=loan.get('loan_number'),
            balance=float(balance),
            group_name=group['name']
        )
        
        return self.send_sms(
            phone_number=member['phone_number'],
            message=message,
            message_type='repayment_confirmation',
            member_id=member['id'],
            reference_id=loan['id']
        )
    
    def send_welcome_message(self, member: Dict, group: Dict) -> Dict:
        """Send welcome message to new members"""
        message = self.TEMPLATES['welcome_message'].format(
            name=member['first_name'],
            group_name=group['name'],
            membership_number=member.get('membership_number')
        )
        
        return self.send_sms(
            phone_number=member['phone_number'],
            message=message,
            message_type='welcome_message',
            member_id=member['id']
        )
    
    def send_meeting_reminder(self, members: List[Dict], group: Dict,
                             meeting_info: Dict) -> List[Dict]:
        """Send meeting reminder to all members"""
        results = []
        
        message = self.TEMPLATES['meeting_reminder'].format(
            group_name=group['name'],
            time=meeting_info.get('time', '5:00 PM'),
            location=meeting_info.get('location', 'usual venue'),
            agenda=meeting_info.get('agenda', 'Weekly business')
        )
        
        for member in members:
            result = self.send_sms(
                phone_number=member['phone_number'],
                message=message,
                message_type='meeting_reminder',
                member_id=member['id'],
                bulk=True
            )
            results.append(result)
        
        return results
    
    def send_bulk_sms(self, members: List[Dict], message: str,
                     message_type: str) -> List[Dict]:
        """Send custom bulk SMS to multiple members"""
        results = []
        
        for member in members:
            result = self.send_sms(
                phone_number=member['phone_number'],
                message=message,
                message_type=message_type,
                member_id=member['id'],
                bulk=True
            )
            results.append(result)
        
        return results
    
    def send_sms(self, phone_number: str, message: str, 
                message_type: str, member_id: str,
                reference_id: Optional[str] = None,
                priority: str = 'normal',
                bulk: bool = False) -> Dict:
        """
        Send SMS using configured provider.
        
        Args:
            phone_number: Recipient's phone number (+256...)
            message: SMS content
            message_type: Type of message (for logging)
            member_id: Member UUID
            reference_id: Related record ID (loan, savings, etc.)
            priority: Message priority (normal, high)
            bulk: Whether this is part of bulk send
            
        Returns:
            Send status and details
        """
        # Format phone number
        formatted_phone = self._format_phone_number(phone_number)
        
        # Truncate message if too long (SMS limit: 160 chars per segment)
        if len(message) > 480:  # Allow up to 3 segments
            message = message[:477] + "..."
        
        try:
            if self.provider == 'africas_talking':
                result = self._send_via_africas_talking(
                    phone_number=formatted_phone,
                    message=message,
                    priority=priority
                )
            elif self.provider == 'twilio':
                result = self._send_via_twilio(
                    phone_number=formatted_phone,
                    message=message
                )
            else:
                raise ValueError(f"Unsupported SMS provider: {self.provider}")
            
            # Log the notification
            notification_log = {
                'id': str(uuid.uuid4()),
                'member_id': member_id,
                'phone_number': formatted_phone,
                'message_type': message_type,
                'message_content': message,
                'status': result.get('status', 'sent'),
                'provider_response': result.get('response', ''),
                'sent_at': datetime.utcnow().isoformat(),
                'reference_id': reference_id
            }
            
            # Store in database (implement based on your DB layer)
            # db.insert('sms_notifications', notification_log)
            
            return {
                'success': True,
                'message_id': result.get('message_id'),
                'status': result.get('status'),
                'phone_number': formatted_phone,
                'message_type': message_type,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Log failed attempt
            error_log = {
                'id': str(uuid.uuid4()),
                'member_id': member_id,
                'phone_number': formatted_phone,
                'message_type': message_type,
                'message_content': message,
                'status': 'failed',
                'error': str(e),
                'sent_at': datetime.utcnow().isoformat()
            }
            
            return {
                'success': False,
                'error': str(e),
                'phone_number': formatted_phone,
                'message_type': message_type,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _send_via_africas_talking(self, phone_number: str, 
                                  message: str, priority: str) -> Dict:
        """Send SMS via Africa's Talking API"""
        url = f"{self.PROVIDERS['africas_talking']['base_url']}{self.PROVIDERS['africas_talking']['sms_endpoint']}"
        
        headers = {
            'apiKey': self.config['api_key'],
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'username': self.config.get('username', 'sandbox'),
            'to': phone_number,
            'message': message,
            'from': self.config.get('sender_id', 'SACCO')
        }
        
        # Add priority for urgent messages
        if priority == 'high':
            data['bulkMode'] = 'false'  # Premium route for urgent messages
        
        response = self.session.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            'status': 'sent' if result.get('responses', [{}])[0].get('statusCode') == 101 else 'failed',
            'message_id': result.get('responses', [{}])[0].get('messageId'),
            'response': result
        }
    
    def _send_via_twilio(self, phone_number: str, message: str) -> Dict:
        """Send SMS via Twilio API"""
        account_sid = self.config['account_sid']
        auth_token = self.config['auth_token']
        from_number = self.config['from_number']
        
        url = f"{self.PROVIDERS['twilio']['base_url']}/Accounts/{account_sid}/Messages.json"
        
        data = {
            'From': from_number,
            'To': phone_number,
            'Body': message
        }
        
        response = self.session.post(
            url, 
            data=data, 
            auth=(account_sid, auth_token)
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            'status': 'sent',
            'message_id': result.get('sid'),
            'response': result
        }
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for SMS delivery"""
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        if cleaned.startswith('+'):
            cleaned = cleaned[1:]
        
        if cleaned.startswith('0'):
            cleaned = '256' + cleaned[1:]
        elif not cleaned.startswith('256'):
            cleaned = '256' + cleaned
        
        return f"+{cleaned}"
    
    def schedule_automated_reminders(self):
        """
        Schedule automated SMS reminders.
        This should be called by a cron job or scheduled task.
        
        Tasks:
        - Send contribution reminders 1 day before weekly meeting
        - Send loan due reminders 3 days before due date
        - Send overdue notices for payments > 7 days late
        """
        # Implementation depends on your scheduler (Celery, APScheduler, etc.)
        pass


# Example usage
if __name__ == "__main__":
    # Configuration for Africa's Talking
    config = {
        'provider': 'africas_talking',
        'api_key': 'your-africas-talking-api-key',
        'username': 'sandbox',  # Use 'sandbox' for testing
        'sender_id': 'SACCO'
    }
    
    # Initialize service
    sms_service = SMSNotificationService(config)
    
    # Example: Send contribution reminder
    member = {
        'id': 'uuid-here',
        'first_name': 'John',
        'phone_number': '+256700000000'
    }
    
    group = {
        'name': 'Kampala SACCO'
    }
    
    try:
        result = sms_service.send_contribution_reminder(
            member=member,
            group=group,
            amount=Decimal('50000'),
            meeting_date='2024-01-19'
        )
        print(f"SMS sent: {result}")
    except Exception as e:
        print(f"SMS failed: {e}")
    
    print("\nSMS Notification Service initialized!")
    print("Supports Africa's Talking and Twilio for Uganda")
