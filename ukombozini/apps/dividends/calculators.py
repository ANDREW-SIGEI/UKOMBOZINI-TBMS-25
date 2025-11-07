from decimal import Decimal
from .models import Dividend

class DividendCalculator:
    @staticmethod
    def calculate_total_dividends(user):
        """Calculate total dividends for a user"""
        dividends = Dividend.objects.filter(user=user)
        return sum(dividend.amount for dividend in dividends)

    @staticmethod
    def calculate_average_dividend(user):
        """Calculate average dividend amount for a user"""
        dividends = Dividend.objects.filter(user=user)
        if not dividends:
            return Decimal('0.00')
        total = sum(dividend.amount for dividend in dividends)
        return total / len(dividends)

    @staticmethod
    def get_dividend_summary(user):
        """Get a summary of dividends for a user"""
        dividends = Dividend.objects.filter(user=user)
        total = sum(dividend.amount for dividend in dividends)
        count = len(dividends)
        average = total / count if count > 0 else Decimal('0.00')

        return {
            'total_dividends': total,
            'number_of_dividends': count,
            'average_dividend': average,
        }
