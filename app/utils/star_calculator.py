#!/usr/bin/env python3
"""
Unified Star Calculation System
Simplifies complex star logic into single, consistent formula.
Formula: available_stars = carry_in + awards - usage
"""
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime


class StarCalculator:
    """Unified star calculation with single formula"""
    
    def __init__(self, data_path: Path = Path('instance/offline_scoreboard_data.json')):
        self.data_path = data_path
        self.data = None
        self._load_data()
    
    def _load_data(self):
        """Load the offline scoreboard data"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                print(f"⚠️ Data file not found: {self.data_path}")
                self.data = {'students': [], 'scores': []}
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.data = {'students': [], 'scores': []}
    
    def get_student_carry_in_stars(self, student_id: int, month_key: str) -> int:
        """
        Get carry-in stars for a student in a given month.
        This is the starting balance from previous month or global counter.
        """
        try:
            # For current month, use global counter
            # For historical months, use __month_star_count if available
            student = self._find_student(student_id)
            if not student:
                return 0
            
            # Check if this is historical data with month-specific carry-in
            if '__month_star_count' in student:
                return max(0, int(student.get('__month_star_count', 0)))
            
            # Otherwise use global counter
            return max(0, int(student.get('stars', 0)))
            
        except Exception as e:
            print(f"⚠️ Error getting carry-in stars: {e}")
            return 0
    
    def get_student_month_awards(self, student_id: int, month_key: str) -> int:
        """
        Get total stars awarded to student in a given month.
        Sums all positive star deltas in scores for that month.
        """
        try:
            total_awards = 0
            for score in self.data.get('scores', []):
                if not isinstance(score, dict):
                    continue
                
                # Check if this score belongs to the student and month
                if int(score.get('studentId', 0)) != student_id:
                    continue
                
                score_month = str(score.get('month', '')).strip()
                if score_month != month_key:
                    continue
                
                # Add positive star deltas (awards)
                stars = int(score.get('stars', 0))
                if stars > 0:
                    total_awards += stars
            
            return max(0, total_awards)
            
        except Exception as e:
            print(f"⚠️ Error getting month awards: {e}")
            return 0
    
    def get_student_month_usage(self, student_id: int, month_key: str) -> int:
        """
        Get total stars used by student in a given month.
        Sums absolute value of all negative star deltas in scores for that month.
        """
        try:
            total_usage = 0
            for score in self.data.get('scores', []):
                if not isinstance(score, dict):
                    continue
                
                # Check if this score belongs to the student and month
                if int(score.get('studentId', 0)) != student_id:
                    continue
                
                score_month = str(score.get('month', '')).strip()
                if score_month != month_key:
                    continue
                
                # Add absolute value of negative star deltas (usage)
                stars = int(score.get('stars', 0))
                if stars < 0:
                    total_usage += abs(stars)
            
            return max(0, total_usage)
            
        except Exception as e:
            print(f"⚠️ Error getting month usage: {e}")
            return 0
    
    def calculate_available_stars(self, student_id: int, month_key: str) -> int:
        """
        Calculate available stars using unified formula.
        Formula: available = carry_in + awards - usage
        
        This is the single source of truth for star calculations.
        """
        carry_in = self.get_student_carry_in_stars(student_id, month_key)
        awards = self.get_student_month_awards(student_id, month_key)
        usage = self.get_student_month_usage(student_id, month_key)
        
        available = carry_in + awards - usage
        return max(0, available)
    
    def validate_star_entry(self, student_id: int, stars: int, month_key: str) -> Tuple[bool, str]:
        """
        Validate a star entry before accepting it.
        Checks:
        1. Individual entry doesn't exceed daily limit (100)
        2. Total doesn't exceed monthly limit (500)
        3. Usage doesn't exceed available stars
        """
        # Check individual entry limit
        if stars < -100 or stars > 100:
            return False, "Star entry must be between -100 and +100"
        
        # For usage (negative stars), check against available
        if stars < 0:
            available = self.calculate_available_stars(student_id, month_key)
            if abs(stars) > available:
                return False, f"Cannot use {abs(stars)} stars. Available: {available}"
        
        # For awards (positive stars), check monthly limit
        if stars > 0:
            current_awards = self.get_student_month_awards(student_id, month_key)
            if current_awards + stars > 500:
                return False, f"Monthly star limit (500) would be exceeded. Current: {current_awards}, Requested: +{stars}"
        
        return True, "OK"
    
    def get_star_bonus(self, student_id: int, date: str, month_key: str) -> int:
        """
        Calculate star bonus for normal star usage.
        Bonus: +100 per normal star use if day's score >= -50
        
        Rules:
        - Only applies to normal usage (not disciplinary)
        - Only if day's score >= -50
        - +100 per normal star use
        """
        try:
            # Find the score for this date
            day_score = 0
            normal_usage = 0
            
            for score in self.data.get('scores', []):
                if not isinstance(score, dict):
                    continue
                
                if int(score.get('studentId', 0)) != student_id:
                    continue
                
                if str(score.get('date', '')).strip() != date:
                    continue
                
                # Get the day's score
                day_score = int(score.get('points', 0))
                
                # Get normal usage (not disciplinary, not transfer)
                star_delta = int(score.get('stars', 0))
                if star_delta < 0:
                    # Check if this is normal usage
                    normal = int(score.get('star_usage_normal', 0))
                    disciplinary = int(score.get('star_usage_disciplinary', 0))
                    is_transfer = score.get('star_transfer_out') or score.get('star_transfer_in')
                    
                    # Only count as normal usage if not disciplinary and not transfer
                    if normal > 0 and disciplinary == 0 and not is_transfer:
                        normal_usage = normal
                
                break
            
            # Calculate bonus
            if day_score >= -50 and normal_usage > 0:
                return 100 * normal_usage
            
            return 0
            
        except Exception as e:
            print(f"⚠️ Error calculating bonus: {e}")
            return 0
    
    def get_student_summary(self, student_id: int, month_key: str) -> Dict:
        """Get complete star summary for a student in a month"""
        carry_in = self.get_student_carry_in_stars(student_id, month_key)
        awards = self.get_student_month_awards(student_id, month_key)
        usage = self.get_student_month_usage(student_id, month_key)
        available = self.calculate_available_stars(student_id, month_key)
        
        return {
            'student_id': student_id,
            'month': month_key,
            'carry_in': carry_in,
            'awards': awards,
            'usage': usage,
            'available': available,
            'formula': f"{carry_in} + {awards} - {usage} = {available}"
        }
    
    def _find_student(self, student_id: int) -> Optional[Dict]:
        """Find student by ID"""
        for student in self.data.get('students', []):
            if int(student.get('id', 0)) == student_id:
                return student
        return None


# Global instance
_calculator = None


def get_star_calculator() -> StarCalculator:
    """Get global star calculator instance"""
    global _calculator
    if _calculator is None:
        _calculator = StarCalculator()
    return _calculator


def main():
    """Test the star calculator"""
    calculator = get_star_calculator()
    
    print("=" * 60)
    print("UNIFIED STAR CALCULATOR TEST")
    print("=" * 60)
    
    # Test with a sample student
    test_student_id = 1
    test_month = "2026-03"
    
    print(f"\nTesting student {test_student_id} for month {test_month}:")
    
    summary = calculator.get_student_summary(test_student_id, test_month)
    print(f"\n{summary['formula']}")
    print(f"Available stars: {summary['available']}")
    
    # Test validation
    print(f"\nValidation tests:")
    
    test_cases = [
        (50, "Award 50 stars"),
        (100, "Award 100 stars (max)"),
        (101, "Award 101 stars (should fail)"),
        (-30, "Use 30 stars"),
        (-200, "Use 200 stars (should fail if not available)"),
    ]
    
    for stars, description in test_cases:
        valid, msg = calculator.validate_star_entry(test_student_id, stars, test_month)
        status = "✓" if valid else "❌"
        print(f"  {status} {description}: {msg}")


if __name__ == '__main__':
    main()
