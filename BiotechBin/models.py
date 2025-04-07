from django.db import models
from django.contrib.auth.models import AbstractUser

# Ticker Model
class Ticker(models.Model):
    symbol = models.CharField(max_length=10, unique=True)  # e.g., AAPL, GOOGL

    def __str__(self):
        return self.symbol

    class Meta:
        db_table = 'tickers'

# StrikePrice Model
class StrikePrice(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name='strike_prices')
    strike_price = models.DecimalField(max_digits=10, decimal_places=2)  # e.g., 150.00

    def __str__(self):
        return f"{self.ticker.symbol} - {self.strike_price}"

    class Meta:
        db_table = 'strike_prices'
        unique_together = ('ticker', 'strike_price')  # Ensure unique strike prices per ticker

# ExpirationDate Model
class ExpirationDate(models.Model):
    strike_price = models.ForeignKey(StrikePrice, on_delete=models.CASCADE, related_name='expiration_dates')
    expiration_date = models.DateField()  # e.g., 2024-12-20

    def __str__(self):
        return f"{self.strike_price} - {self.expiration_date}"

    class Meta:
        db_table = 'expiration_dates'
        unique_together = ('strike_price', 'expiration_date')  # Ensure unique expiration dates per strike price

# DatePrice Model
class DatePrice(models.Model):
    expiration_date = models.ForeignKey(ExpirationDate, on_delete=models.CASCADE, related_name='date_prices')
    date_collected = models.DateField()  # Date the price was collected
    high_price = models.DecimalField(max_digits=10, decimal_places=2)  # High price of the day
    low_price = models.DecimalField(max_digits=10, decimal_places=2)   # Low price of the day
    end_price = models.DecimalField(max_digits=10, decimal_places=2)   # End price of the day

    def __str__(self):
        return f"{self.expiration_date} - {self.date_collected}"

    class Meta:
        db_table = 'date_prices'
        unique_together = ('expiration_date', 'date_collected')  # Ensure unique date prices per expiration date

# User Model
class User(AbstractUser):
    is_admin = models.BooleanField(default=False)  # Add custom field if needed

    class Meta:
        db_table = 'users'