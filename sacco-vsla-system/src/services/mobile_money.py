"""
Mobile Money Integration Service for Ugandan SACCO/VSLA System
Supports MTN Mobile Money, Airtel Money, and other local providers
"""

import requests
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime
import hashlib
import base64
import uuid


class MobileMoneyService:
    """
    Integration service for Ugandan mobile money providers.
    Supports MTN MoMo, Airtel Money, and Humans UX.
    """
    
    PROVIDERS = {
        'mtn_momo': {
            'base_url': 'https://sandbox.momodeveloper.mtn.com',
            'production_url': 'https://ericssonbasicapi2.azure-api.net',
            'collection_api': '/collection/v1_0/requesttopay',
            'disbursement_api': '/disbursement/v1_0/transfer',
            'auth_header': 'Authorization',
            'currency': 'UGX'
        },
        'airtel_money': {
            'base_url': 'https://openapiuat.airtel.africa',
            'production_url': 'https://openapi.airtel.africa',
            'payment_api': '/merchant/v1/payments',
            'payout_api': '/merchant/v1/payouts',
            'currency': 'UGX'
        },
        'humans_ux': {
            'base_url': 'https://api.humans.ug',
            'payment_api': '/v1/payments',
            'currency': 'UGX'
        }
    }
    
    def __init__(self, config: Dict):
        """
        Initialize with provider credentials.
        
        Args:
            config: Dictionary containing API credentials for each provider
                {
                    'mtn_momo': {
                        'api_key': '...',
                        'user_id': '...',
                        'target_environment': 'sandbox'
                    },
                    'airtel_money': {
                        'api_key': '...',
                        'client_id': '...',
                        'client_secret': '...'
                    }
                }
        """
        self.config = config
        self.session = requests.Session()
    
    def initiate_collection(self, provider: str, amount: Decimal, 
                           phone_number: str, reference: str,
                           narration: str) -> Dict:
        """
        Initiate a mobile money collection (deposit from member to SACCO).
        
        Args:
            provider: Provider name ('mtn_momo', 'airtel_money')
            amount: Amount in UGX
            phone_number: Member's phone number (+256...)
            reference: Transaction reference
            narration: Description of the payment
            
        Returns:
            Transaction details including status and transaction ID
        """
        if provider not in self.config:
            raise ValueError(f"Provider {provider} not configured")
        
        provider_config = self.PROVIDERS[provider]
        credentials = self.config[provider]
        
        # Format phone number (remove +, ensure correct format)
        formatted_phone = self._format_phone_number(phone_number, provider)
        
        try:
            if provider == 'mtn_momo':
                return self._mtn_request_to_pay(
                    amount=amount,
                    phone_number=formatted_phone,
                    reference=reference,
                    narration=narration,
                    credentials=credentials
                )
            elif provider == 'airtel_money':
                return self._airtel_request_payment(
                    amount=amount,
                    phone_number=formatted_phone,
                    reference=reference,
                    narration=narration,
                    credentials=credentials
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            # Log error to database
            self._log_api_call(
                provider=provider,
                endpoint='collection',
                success=False,
                error=str(e)
            )
            raise
    
    def disburse_funds(self, provider: str, amount: Decimal,
                      phone_number: str, reference: str,
                      narration: str) -> Dict:
        """
        Disburse funds via mobile money (loan disbursement or withdrawal).
        
        Args:
            provider: Provider name ('mtn_momo', 'airtel_money')
            amount: Amount in UGX
            phone_number: Recipient's phone number (+256...)
            reference: Transaction reference
            narration: Description of the payment
            
        Returns:
            Transaction details including status and transaction ID
        """
        if provider not in self.config:
            raise ValueError(f"Provider {provider} not configured")
        
        provider_config = self.PROVIDERS[provider]
        credentials = self.config[provider]
        
        formatted_phone = self._format_phone_number(phone_number, provider)
        
        try:
            if provider == 'mtn_momo':
                return self._mtn_transfer(
                    amount=amount,
                    phone_number=formatted_phone,
                    reference=reference,
                    narration=narration,
                    credentials=credentials
                )
            elif provider == 'airtel_money':
                return self._airtel_payout(
                    amount=amount,
                    phone_number=formatted_phone,
                    reference=reference,
                    narration=narration,
                    credentials=credentials
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            self._log_api_call(
                provider=provider,
                endpoint='disbursement',
                success=False,
                error=str(e)
            )
            raise
    
    def check_transaction_status(self, provider: str, 
                                transaction_reference: str) -> Dict:
        """
        Check the status of a mobile money transaction.
        
        Args:
            provider: Provider name
            transaction_reference: Reference ID from initial request
            
        Returns:
            Transaction status (SUCCESS, FAILED, PENDING)
        """
        credentials = self.config.get(provider)
        if not credentials:
            raise ValueError(f"Provider {provider} not configured")
        
        try:
            if provider == 'mtn_momo':
                return self._mtn_check_status(transaction_reference, credentials)
            elif provider == 'airtel_money':
                return self._airtel_check_status(transaction_reference, credentials)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except Exception as e:
            self._log_api_call(
                provider=provider,
                endpoint='status_check',
                success=False,
                error=str(e)
            )
            raise
    
    def _mtn_request_to_pay(self, amount: Decimal, phone_number: str,
                           reference: str, narration: str,
                           credentials: Dict) -> Dict:
        """MTN Mobile Money - Request to Pay API"""
        url = f"{self.PROVIDERS['mtn_momo']['base_url']}{self.PROVIDERS['mtn_momo']['collection_api']}"
        
        # Get access token
        token = self._get_mtn_token(credentials)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Reference-Id': reference,
            'X-Target-Environment': credentials.get('target_environment', 'sandbox'),
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': credentials.get('api_key')
        }
        
        payload = {
            'amount': str(amount),
            'currency': 'UGX',
            'externalId': reference,
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': phone_number
            },
            'payerMessage': narration,
            'payeeNote': ''
        }
        
        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = {
            'success': True,
            'provider': 'mtn_momo',
            'transaction_reference': reference,
            'status': 'PENDING',
            'amount': float(amount),
            'phone_number': phone_number,
            'message': 'Payment request sent to customer',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._log_api_call(
            provider='mtn_momo',
            endpoint='collection',
            request_body=payload,
            response_body=result,
            status_code=response.status_code,
            transaction_reference=reference,
            success=True
        )
        
        return result
    
    def _mtn_transfer(self, amount: Decimal, phone_number: str,
                     reference: str, narration: str,
                     credentials: Dict) -> Dict:
        """MTN Mobile Money - Transfer API (Disbursement)"""
        url = f"{self.PROVIDERS['mtn_momo']['base_url']}{self.PROVIDERS['mtn_momo']['disbursement_api']}"
        
        token = self._get_mtn_token(credentials)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Reference-Id': reference,
            'X-Target-Environment': credentials.get('target_environment', 'sandbox'),
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': credentials.get('api_key')
        }
        
        payload = {
            'amount': str(amount),
            'currency': 'UGX',
            'externalId': reference,
            'payee': {
                'partyIdType': 'MSISDN',
                'partyId': phone_number
            },
            'payerMessage': '',
            'payeeNote': narration
        }
        
        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = {
            'success': True,
            'provider': 'mtn_momo',
            'transaction_reference': reference,
            'status': 'PENDING',
            'amount': float(amount),
            'phone_number': phone_number,
            'message': 'Transfer initiated',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._log_api_call(
            provider='mtn_momo',
            endpoint='disbursement',
            request_body=payload,
            response_body=result,
            status_code=response.status_code,
            transaction_reference=reference,
            success=True
        )
        
        return result
    
    def _get_mtn_token(self, credentials: Dict) -> str:
        """Get MTN access token using basic auth"""
        url = f"{self.PROVIDERS['mtn_momo']['base_url']}/collection/token/"
        
        auth_string = f"{credentials['user_id']}:{credentials['api_key']}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Ocp-Apim-Subscription-Key': credentials.get('subscription_key')
        }
        
        response = self.session.post(url, headers=headers)
        response.raise_for_status()
        
        return response.json().get('access_token')
    
    def _airtel_request_payment(self, amount: Decimal, phone_number: str,
                               reference: str, narration: str,
                               credentials: Dict) -> Dict:
        """Airtel Money - Payment Request API"""
        url = f"{self.PROVIDERS['airtel_money']['base_url']}{self.PROVIDERS['airtel_money']['payment_api']}"
        
        token = self._get_airtel_token(credentials)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-Country': 'UG',
            'X-Currency': 'UGX'
        }
        
        payload = {
            'amount': str(amount),
            'currency': 'UGX',
            'transaction_ref': reference,
            'msisdn': phone_number,
            'narration': narration
        }
        
        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        self._log_api_call(
            provider='airtel_money',
            endpoint='collection',
            request_body=payload,
            response_body=result,
            status_code=response.status_code,
            transaction_reference=reference,
            success=True
        )
        
        return {
            'success': True,
            'provider': 'airtel_money',
            'transaction_reference': reference,
            'status': result.get('status', 'PENDING'),
            'amount': float(amount),
            'phone_number': phone_number,
            'message': 'Payment request sent',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _airtel_payout(self, amount: Decimal, phone_number: str,
                      reference: str, narration: str,
                      credentials: Dict) -> Dict:
        """Airtel Money - Payout API (Disbursement)"""
        url = f"{self.PROVIDERS['airtel_money']['base_url']}{self.PROVIDERS['airtel_money']['payout_api']}"
        
        token = self._get_airtel_token(credentials)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-Country': 'UG',
            'X-Currency': 'UGX'
        }
        
        payload = {
            'amount': str(amount),
            'currency': 'UGX',
            'transaction_ref': reference,
            'msisdn': phone_number,
            'narration': narration
        }
        
        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        self._log_api_call(
            provider='airtel_money',
            endpoint='disbursement',
            request_body=payload,
            response_body=result,
            status_code=response.status_code,
            transaction_reference=reference,
            success=True
        )
        
        return {
            'success': True,
            'provider': 'airtel_money',
            'transaction_reference': reference,
            'status': result.get('status', 'PENDING'),
            'amount': float(amount),
            'phone_number': phone_number,
            'message': 'Payout initiated',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_airtel_token(self, credentials: Dict) -> str:
        """Get Airtel access token"""
        url = f"{self.PROVIDERS['airtel_money']['base_url']}/auth/token/"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'client_id': credentials['client_id'],
            'client_secret': credentials['client_secret'],
            'grant_type': 'client_credentials'
        }
        
        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json().get('access_token')
    
    def _mtn_check_status(self, reference: str, credentials: Dict) -> Dict:
        """Check MTN transaction status"""
        url = f"{self.PROVIDERS['mtn_momo']['base_url']}/collection/v1_0/requesttopay/{reference}"
        
        token = self._get_mtn_token(credentials)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Target-Environment': credentials.get('target_environment', 'sandbox'),
            'Ocp-Apim-Subscription-Key': credentials.get('api_key')
        }
        
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            'success': True,
            'provider': 'mtn_momo',
            'transaction_reference': reference,
            'status': result.get('status', 'UNKNOWN'),
            'amount': result.get('amount'),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _airtel_check_status(self, reference: str, credentials: Dict) -> Dict:
        """Check Airtel transaction status"""
        url = f"{self.PROVIDERS['airtel_money']['base_url']}/merchant/v1/paymentstatus/{reference}"
        
        token = self._get_airtel_token(credentials)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Country': 'UG',
            'X-Currency': 'UGX'
        }
        
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            'success': True,
            'provider': 'airtel_money',
            'transaction_reference': reference,
            'status': result.get('status', 'UNKNOWN'),
            'amount': result.get('amount'),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _format_phone_number(self, phone: str, provider: str) -> str:
        """Format phone number according to provider requirements"""
        # Remove any non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Ensure it starts with country code
        if cleaned.startswith('+'):
            cleaned = cleaned[1:]
        
        # For Uganda, ensure it starts with 256
        if cleaned.startswith('0'):
            cleaned = '256' + cleaned[1:]
        elif not cleaned.startswith('256'):
            cleaned = '256' + cleaned
        
        return cleaned
    
    def _log_api_call(self, provider: str, endpoint: str, success: bool,
                     request_body: Optional[Dict] = None,
                     response_body: Optional[Dict] = None,
                     status_code: Optional[int] = None,
                     transaction_reference: Optional[str] = None,
                     error: Optional[str] = None) -> None:
        """Log API call to database for audit trail"""
        log_entry = {
            'id': str(uuid.uuid4()),
            'provider': provider,
            'endpoint': endpoint,
            'request_method': 'POST' if 'status' not in endpoint else 'GET',
            'request_body': request_body,
            'response_body': response_body,
            'status_code': status_code,
            'transaction_reference': transaction_reference,
            'error_message': error,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Store in database (implement based on your DB layer)
        # db.insert('api_integration_logs', log_entry)
        print(f"API LOG: {log_entry}")


# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        'mtn_momo': {
            'user_id': 'your-user-id',
            'api_key': 'your-api-key',
            'subscription_key': 'your-subscription-key',
            'target_environment': 'sandbox'
        },
        'airtel_money': {
            'client_id': 'your-client-id',
            'client_secret': 'your-client-secret'
        }
    }
    
    # Initialize service
    momo_service = MobileMoneyService(config)
    
    # Example: Collect payment (member deposit)
    try:
        collection_result = momo_service.initiate_collection(
            provider='mtn_momo',
            amount=Decimal('50000'),
            phone_number='+256700000000',
            reference=f"DEP-{uuid.uuid4()}",
            narration='Weekly contribution - Week 3'
        )
        print(f"Collection initiated: {collection_result}")
    except Exception as e:
        print(f"Collection failed: {e}")
    
    # Example: Disburse loan
    try:
        disbursement_result = momo_service.disburse_funds(
            provider='mtn_momo',
            amount=Decimal('2000000'),
            phone_number='+256700000000',
            reference=f"LOAN-{uuid.uuid4()}",
            narration='Loan disbursement - LN-2024-001'
        )
        print(f"Disbursement initiated: {disbursement_result}")
    except Exception as e:
        print(f"Disbursement failed: {e}")
    
    print("\nMobile Money Service initialized successfully!")
    print("Supports MTN Mobile Money and Airtel Money for Uganda")
