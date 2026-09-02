"""
Credit Scoring Service for SACCO/VSLA System
Automated credit scoring based on repayment history, savings patterns, and member behavior
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal


class CreditScoringService:
    """
    Automated credit scoring system tailored for Ugandan SACCOs and VSLAs.
    Calculates credit scores (0-1000) based on multiple factors.
    """
    
    # Score weights (must sum to 1000)
    WEIGHTS = {
        'repayment_history': 350,      # 35% - Most important factor
        'savings_consistency': 250,    # 25% - Regular savings behavior
        'savings_balance': 200,        # 20% - Total savings amount
        'membership_duration': 100,    # 10% - Loyalty factor
        'meeting_attendance': 100      # 10% - Engagement level
    }
    
    # Risk categories
    RISK_CATEGORIES = {
        'excellent': (800, 1000),
        'good': (650, 799),
        'fair': (500, 649),
        'poor': (300, 499),
        'very_poor': (0, 299)
    }
    
    # Loan multipliers based on risk category
    LOAN_MULTIPLIERS = {
        'excellent': 5.0,  # Can borrow up to 5x savings
        'good': 4.0,
        'fair': 3.0,
        'poor': 2.0,
        'very_poor': 1.0   # Only can borrow what they've saved
    }
    
    def __init__(self, db_connection):
        """Initialize with database connection"""
        self.db = db_connection
    
    def calculate_credit_score(self, member_id: str, group_id: str) -> Dict:
        """
        Calculate comprehensive credit score for a member.
        
        Args:
            member_id: UUID of the member
            group_id: UUID of the group/SACCO
            
        Returns:
            Dictionary containing score, risk category, and eligibility details
        """
        # Fetch member data
        member = self._get_member(member_id, group_id)
        if not member:
            raise ValueError("Member not found")
        
        # Calculate individual component scores
        repayment_score = self._calculate_repayment_score(member_id, group_id)
        savings_consistency_score = self._calculate_savings_consistency_score(member_id, group_id)
        savings_balance_score = self._calculate_savings_balance_score(member_id, group_id)
        membership_duration_score = self._calculate_membership_duration_score(member)
        attendance_score = self._calculate_attendance_score(member_id, group_id)
        
        # Calculate weighted total score
        total_score = (
            repayment_score * (self.WEIGHTS['repayment_history'] / 100) +
            savings_consistency_score * (self.WEIGHTS['savings_consistency'] / 100) +
            savings_balance_score * (self.WEIGHTS['savings_balance'] / 100) +
            membership_duration_score * (self.WEIGHTS['membership_duration'] / 100) +
            attendance_score * (self.WEIGHTS['meeting_attendance'] / 100)
        )
        
        # Ensure score is within bounds
        total_score = max(0, min(1000, int(total_score)))
        
        # Determine risk category
        risk_category = self._get_risk_category(total_score)
        
        # Calculate loan eligibility
        total_savings = Decimal(str(member.get('total_savings', 0)))
        multiplier = self.LOAN_MULTIPLIERS[risk_category]
        max_loan_eligible = total_savings * multiplier
        
        # Prepare calculation factors for transparency
        calculation_factors = {
            'repayment_history': {
                'score': repayment_score,
                'weight': self.WEIGHTS['repayment_history'],
                'weighted_contribution': repayment_score * (self.WEIGHTS['repayment_history'] / 100)
            },
            'savings_consistency': {
                'score': savings_consistency_score,
                'weight': self.WEIGHTS['savings_consistency'],
                'weighted_contribution': savings_consistency_score * (self.WEIGHTS['savings_consistency'] / 100)
            },
            'savings_balance': {
                'score': savings_balance_score,
                'weight': self.WEIGHTS['savings_balance'],
                'weighted_contribution': savings_balance_score * (self.WEIGHTS['savings_balance'] / 100)
            },
            'membership_duration': {
                'score': membership_duration_score,
                'weight': self.WEIGHTS['membership_duration'],
                'weighted_contribution': membership_duration_score * (self.WEIGHTS['membership_duration'] / 100)
            },
            'meeting_attendance': {
                'score': attendance_score,
                'weight': self.WEIGHTS['meeting_attendance'],
                'weighted_contribution': attendance_score * (self.WEIGHTS['meeting_attendance'] / 100)
            }
        }
        
        # Store the score in database
        self._store_credit_score(
            member_id=member_id,
            group_id=group_id,
            score=total_score,
            risk_category=risk_category,
            max_loan_eligible=max_loan_eligible,
            calculation_factors=calculation_factors
        )
        
        return {
            'member_id': member_id,
            'score': total_score,
            'risk_category': risk_category,
            'max_loan_eligible': float(max_loan_eligible),
            'loan_multiplier': multiplier,
            'calculation_factors': calculation_factors,
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    def _calculate_repayment_score(self, member_id: str, group_id: str) -> int:
        """
        Calculate score based on loan repayment history (0-100).
        Considers: on-time payments, defaults, outstanding loans.
        """
        loans = self._get_member_loans(member_id, group_id)
        
        if not loans:
            # No loan history - neutral score
            return 70
        
        total_loans = len(loans)
        on_time_payments = 0
        late_payments = 0
        defaulted_loans = 0
        total_installments = 0
        missed_installments = 0
        
        for loan in loans:
            repayments = self._get_loan_repayments(loan['id'])
            total_installments += loan.get('number_of_installments', 0)
            
            if loan.get('status') == 'defaulted':
                defaulted_loans += 1
                missed_installments += loan.get('number_of_installments', 0) - len(repayments)
            else:
                for repayment in repayments:
                    due_date = loan.get('due_date')
                    paid_date = repayment.get('repayment_date')
                    
                    if paid_date <= due_date:
                        on_time_payments += 1
                    else:
                        days_late = (paid_date - due_date).days
                        if days_late <= 7:
                            on_time_payments += 0.5  # Slightly late but acceptable
                            late_payments += 0.5
                        elif days_late <= 30:
                            late_payments += 1
                        else:
                            missed_installments += 1
        
        if total_installments == 0:
            return 70
        
        # Calculate repayment rate
        repayment_rate = (on_time_payments / total_installments) * 100 if total_installments > 0 else 0
        
        # Penalty for defaults
        default_penalty = (defaulted_loans / total_loans) * 50 if total_loans > 0 else 0
        
        # Calculate final score
        base_score = min(100, repayment_rate)
        final_score = max(0, base_score - default_penalty)
        
        return int(final_score)
    
    def _calculate_savings_consistency_score(self, member_id: str, group_id: str) -> int:
        """
        Calculate score based on savings consistency (0-100).
        Rewards regular weekly contributions.
        """
        savings_records = self._get_member_savings(member_id, group_id)
        
        if not savings_records:
            return 0
        
        # Get last 6 months of weeks
        current_date = datetime.utcnow()
        six_months_ago = current_date - timedelta(days=180)
        
        total_weeks = 26  # Approximately 6 months
        weeks_with_contributions = set()
        
        for saving in savings_records:
            if saving.get('transaction_date', datetime.min) >= six_months_ago:
                week_key = (saving.get('year'), saving.get('week_number'))
                weeks_with_contributions.add(week_key)
        
        consistency_rate = (len(weeks_with_contributions) / total_weeks) * 100
        
        return min(100, int(consistency_rate))
    
    def _calculate_savings_balance_score(self, member_id: str, group_id: str) -> int:
        """
        Calculate score based on total savings balance (0-100).
        Higher savings = higher score.
        """
        member = self._get_member(member_id, group_id)
        total_savings = Decimal(str(member.get('total_savings', 0)))
        
        # Define thresholds (in UGX) - adjust based on group norms
        thresholds = {
            10000000: 100,   # 10M UGX
            5000000: 90,     # 5M UGX
            2000000: 80,     # 2M UGX
            1000000: 70,     # 1M UGX
            500000: 60,      # 500K UGX
            200000: 50,      # 200K UGX
            100000: 40,      # 100K UGX
            50000: 30,       # 50K UGX
            10000: 20,       # 10K UGX
            0: 10            # Any savings
        }
        
        for threshold, score in sorted(thresholds.items(), reverse=True):
            if total_savings >= threshold:
                return score
        
        return 0
    
    def _calculate_membership_duration_score(self, member: Dict) -> int:
        """
        Calculate score based on membership duration (0-100).
        Longer membership = higher loyalty score.
        """
        join_date = member.get('join_date')
        if not join_date:
            return 0
        
        days_as_member = (datetime.utcnow() - join_date).days
        
        # Score progression
        if days_as_member >= 1825:  # 5+ years
            return 100
        elif days_as_member >= 1095:  # 3+ years
            return 90
        elif days_as_member >= 730:  # 2+ years
            return 80
        elif days_as_member >= 365:  # 1+ year
            return 70
        elif days_as_member >= 180:  # 6+ months
            return 60
        elif days_as_member >= 90:  # 3+ months
            return 50
        else:
            return max(10, int((days_as_member / 90) * 50))
    
    def _calculate_attendance_score(self, member_id: str, group_id: str) -> int:
        """
        Calculate score based on meeting attendance (0-100).
        Regular attendance shows engagement.
        """
        attendance_records = self._get_member_attendance(member_id, group_id)
        
        if not attendance_records:
            return 50  # Neutral if no records
        
        total_meetings = len(attendance_records)
        present_count = sum(1 for record in attendance_records 
                          if record.get('attendance_status') == 'present')
        
        attendance_rate = (present_count / total_meetings) * 100 if total_meetings > 0 else 0
        
        return min(100, int(attendance_rate))
    
    def _get_risk_category(self, score: int) -> str:
        """Determine risk category based on score."""
        for category, (min_score, max_score) in self.RISK_CATEGORIES.items():
            if min_score <= score <= max_score:
                return category
        return 'very_poor'
    
    def check_loan_eligibility(self, member_id: str, group_id: str, 
                              requested_amount: Decimal) -> Dict:
        """
        Check if a member is eligible for a loan and provide recommendations.
        
        Args:
            member_id: UUID of the member
            group_id: UUID of the group
            requested_amount: Amount requested in UGX
            
        Returns:
            Eligibility decision with reasoning
        """
        # Get or calculate credit score
        credit_info = self.calculate_credit_score(member_id, group_id)
        member = self._get_member(member_id, group_id)
        
        total_savings = Decimal(str(member.get('total_savings', 0)))
        existing_loans = self._get_outstanding_loans(member_id, group_id)
        total_outstanding = sum(Decimal(str(loan.get('outstanding_balance', 0))) 
                               for loan in existing_loans)
        
        max_eligible = credit_info['max_loan_eligible']
        
        # Check eligibility criteria
        is_eligible = True
        reasons = []
        
        if credit_info['risk_category'] in ['poor', 'very_poor']:
            is_eligible = False
            reasons.append(f"Credit score too low ({credit_info['score']}). Improve repayment history.")
        
        if total_outstanding > 0:
            debt_to_savings_ratio = total_outstanding / total_savings if total_savings > 0 else 999
            if debt_to_savings_ratio > 2:
                is_eligible = False
                reasons.append("Existing debt too high relative to savings.")
        
        if requested_amount > max_eligible:
            is_eligible = False
            reasons.append(f"Requested amount exceeds maximum eligibility of UGX {max_eligible:,.0f}")
        
        recommended_amount = min(max_eligible - total_outstanding, max_eligible * 0.8)
        
        return {
            'is_eligible': is_eligible,
            'requested_amount': float(requested_amount),
            'max_loan_amount': float(max_eligible),
            'recommended_amount': float(recommended_amount),
            'existing_loans': float(total_outstanding),
            'available_capacity': float(max_eligible - total_outstanding),
            'credit_score': credit_info['score'],
            'risk_category': credit_info['risk_category'],
            'reasons': reasons if not is_eligible else ['All criteria met']
        }
    
    def batch_calculate_scores(self, group_id: str) -> Dict:
        """Calculate credit scores for all members in a group."""
        members = self._get_all_members(group_id)
        
        results = {
            'total_members': len(members),
            'scores_calculated': 0,
            'errors': [],
            'distribution': {
                'excellent': 0,
                'good': 0,
                'fair': 0,
                'poor': 0,
                'very_poor': 0
            }
        }
        
        for member in members:
            try:
                score_info = self.calculate_credit_score(member['id'], group_id)
                results['scores_calculated'] += 1
                results['distribution'][score_info['risk_category']] += 1
            except Exception as e:
                results['errors'].append({
                    'member_id': member['id'],
                    'error': str(e)
                })
        
        results['average_score'] = sum(
            self.calculate_credit_score(m['id'], group_id)['score'] 
            for m in members if m['id'] not in [e['member_id'] for e in results['errors']]
        ) / max(1, results['scores_calculated'])
        
        return results
    
    # Database helper methods (implement based on your DB framework)
    def _get_member(self, member_id: str, group_id: str) -> Optional[Dict]:
        """Fetch member details from database."""
        # Implementation depends on your ORM/database layer
        pass
    
    def _get_member_loans(self, member_id: str, group_id: str) -> List[Dict]:
        """Fetch all loans for a member."""
        pass
    
    def _get_loan_repayments(self, loan_id: str) -> List[Dict]:
        """Fetch all repayments for a loan."""
        pass
    
    def _get_member_savings(self, member_id: str, group_id: str) -> List[Dict]:
        """Fetch all savings records for a member."""
        pass
    
    def _get_member_attendance(self, member_id: str, group_id: str) -> List[Dict]:
        """Fetch meeting attendance records for a member."""
        pass
    
    def _get_outstanding_loans(self, member_id: str, group_id: str) -> List[Dict]:
        """Fetch all outstanding loans for a member."""
        pass
    
    def _get_all_members(self, group_id: str) -> List[Dict]:
        """Fetch all active members in a group."""
        pass
    
    def _store_credit_score(self, member_id: str, group_id: str, 
                           score: int, risk_category: str,
                           max_loan_eligible: Decimal, 
                           calculation_factors: Dict) -> None:
        """Store credit score in database."""
        pass


# Example usage
if __name__ == "__main__":
    # Initialize service with database connection
    # db = get_database_connection()
    # scorer = CreditScoringService(db)
    
    # Calculate score for a member
    # result = scorer.calculate_credit_score(
    #     member_id="uuid-here",
    #     group_id="uuid-here"
    # )
    # print(f"Credit Score: {result['score']}")
    # print(f"Risk Category: {result['risk_category']}")
    # print(f"Max Loan Eligible: UGX {result['max_loan_eligible']:,.0f}")
    
    # Check loan eligibility
    # eligibility = scorer.check_loan_eligibility(
    #     member_id="uuid-here",
    #     group_id="uuid-here",
    #     requested_amount=Decimal("5000000")
    # )
    # print(f"Eligible: {eligibility['is_eligible']}")
    # print(f"Recommended Amount: UGX {eligibility['recommended_amount']:,.0f}")
    
    print("Credit Scoring Service initialized successfully!")
    print("This module provides automated credit scoring for SACCO/VSLA members.")
