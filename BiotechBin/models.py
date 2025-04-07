from django.db import models
from django.contrib.auth.models import AbstractUser

# Ticker Model
class Ticker(models.Model):
    symbol = models.CharField(max_length=10, unique=True)  # e.g., AAPL, SPY, GOOGL

    def __str__(self):
        return self.symbol

    class Meta:
        db_table = 'tickers'

# Option Model
class Option(models.Model):
    OPTION_TYPES = (
        ('CALL', 'Call'),
        ('PUT', 'Put'),
    )

    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name='options')
    expiration_date = models.DateField()
    strike_price = models.DecimalField(max_digits=10, decimal_places=2)
    option_type = models.CharField(max_length=4, choices=OPTION_TYPES)

    def __str__(self):
        return f"{self.ticker.symbol} {self.strike_price} {self.option_type} {self.expiration_date}"

    class Meta:
        db_table = 'options'
        unique_together = ('ticker', 'expiration_date', 'strike_price', 'option_type')
        indexes = [
            models.Index(fields=['ticker', 'expiration_date', 'strike_price', 'option_type']),
        ]

# OptionPrice Model
class OptionPrice(models.Model):
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='prices')
    date_collected = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    end_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.IntegerField()

    def __str__(self):
        return f"{self.option} - {self.date_collected}"

    class Meta:
        db_table = 'option_prices'
        unique_together = ('option', 'date_collected')
        indexes = [
            models.Index(fields=['option', 'date_collected']),
        ]

# User Model (if needed)
class User(AbstractUser):
    is_admin = models.BooleanField(default=False)

    class Meta:
        db_table = 'users'