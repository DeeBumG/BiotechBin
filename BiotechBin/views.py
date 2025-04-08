from django.shortcuts import render
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from .models import Ticker

def home(request):
    return render(request, 'BiotechBin/home.html', {'title': 'Home'})

def tickers(request):
    tickers = Ticker.objects.all().prefetch_related(
        'options__prices'  # prefetch options AND their prices
    )
    return render(request, 'BiotechBin/tickers.html', {
        'tickers': tickers,
        'title': 'All Tickers',
    })

def events(request):
    # Placeholder for upcoming events (e.g., expiration dates)
    return render(request, 'BiotechBin/events.html', {'title': 'Upcoming Events'})

def custom_logout(request):
    logout(request)
    return HttpResponseRedirect('/')