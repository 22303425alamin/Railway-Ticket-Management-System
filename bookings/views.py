from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from .models import Payment
from trains.models import Train, TrainSchedule, Station, Route
from datetime import datetime, date
import random
import string


def generate_transaction_id():
    """Generate random transaction ID"""
    return 'TXN' + ''.join(random.choices(string.digits, k=12))


@login_required
def new_booking(request, train_id):
    """New Booking Form - Single Passenger (User's info)"""
    train = get_object_or_404(Train, id=train_id)
    
    # Get search data from session
    origin_code = request.session.get('search_origin')
    destination_code = request.session.get('search_destination')
    journey_date_str = request.session.get('journey_date')
    
    if not all([origin_code, destination_code, journey_date_str]):
        messages.error(request, 'Invalid booking request!')
        return redirect('trains:home')
    
    try:
        origin = Station.objects.get(station_code=origin_code)
        destination = Station.objects.get(station_code=destination_code)
        journey_date = datetime.strptime(journey_date_str, '%Y-%m-%d').date()
        schedule = TrainSchedule.objects.get(train=train)
        
        if not schedule.is_running_on_date(journey_date):
            messages.error(request, f'Train does not run on {journey_date.strftime("%A")}')
            return redirect('trains:home')
        
        # Get route details for fare calculation
        origin_route = Route.objects.filter(train=train, station=origin).first()
        dest_route = Route.objects.filter(train=train, station=destination).first()
        
        if not origin_route or not dest_route:
            messages.error(request, 'Route information not available!')
            return redirect('trains:home')
        
        # Calculate distance
        distance = float(dest_route.distance_from_origin - origin_route.distance_from_origin)
        
        # Calculate fare
        fare_per_km = 2
        base_fare = distance * fare_per_km
        reservation_charge = 50
        tax = (base_fare + reservation_charge) * 0.05
        total_fare = base_fare + reservation_charge + tax
        
    except Exception as e:
        messages.error(request, f'Invalid booking data! {str(e)}')
        return redirect('trains:home')
    
    context = {
        'train': train,
        'schedule': schedule,
        'origin': origin,
        'destination': destination,
        'journey_date': journey_date,
        'distance': distance,
        'base_fare': base_fare,
        'reservation_charge': reservation_charge,
        'tax': tax,
        'total_fare': total_fare,
        'user': request.user,
    }
    
    return render(request, 'bookings/new_booking.html', context)


@login_required
@transaction.atomic
def confirm_booking(request):
    """Confirm Booking and Create Payment Record"""
    if request.method != 'POST':
        return redirect('trains:home')
    
    # Get form data
    train_id = request.POST.get('train_id')
    origin_code = request.POST.get('origin_code')
    destination_code = request.POST.get('destination_code')
    journey_date_str = request.POST.get('journey_date')
    
    # Validate
    if not all([train_id, origin_code, destination_code, journey_date_str]):
        messages.error(request, 'Invalid booking data!')
        return redirect('trains:home')
    
    try:
        train = Train.objects.get(id=train_id)
        origin = Station.objects.get(station_code=origin_code)
        destination = Station.objects.get(station_code=destination_code)
        journey_date = datetime.strptime(journey_date_str, '%Y-%m-%d').date()
        schedule = TrainSchedule.objects.get(train=train)
        
        if not schedule.is_running_on_date(journey_date):
            messages.error(request, f'Train does not run on {journey_date.strftime("%A")}')
            return redirect('trains:home')
        
        # Check seat availability
        if train.available_seats < 1:
            messages.error(request, 'No seats available!')
            return redirect('trains:home')
        
        # Get route details for fare calculation
        origin_route = Route.objects.filter(train=train, station=origin).first()
        dest_route = Route.objects.filter(train=train, station=destination).first()
        
        # Calculate distance
        distance = float(dest_route.distance_from_origin - origin_route.distance_from_origin)
        
        # Fare calculation: 2 BDT per KM
        fare_per_km = 2
        base_fare = distance * fare_per_km
        reservation_charge = 50
        
    except Exception as e:
        messages.error(request, f'Invalid booking information! {str(e)}')
        return redirect('trains:home')
    
    # Create payment/booking record
    payment = Payment.objects.create(
        user=request.user,
        train=train,
        train_schedule=schedule,
        origin_station=origin,
        destination_station=destination,
        journey_date=journey_date,
        base_fare=base_fare,
        reservation_charge=reservation_charge,
        tax=0,
        total_fare=0,
        payment_status='pending'
    )
    
    # Calculate fare
    payment.calculate_fare()
    
    # Reduce seat count
    train.book_seat(1)
    
    messages.success(request, f'Booking created! PNR: {payment.pnr}')
    return redirect('bookings:payment', pnr=payment.pnr)


@login_required
def payment(request, pnr):
    """Payment Page - Simulated Payment Gateway"""
    booking = get_object_or_404(Payment, pnr=pnr, user=request.user)
    
    if booking.payment_status == 'success':
        messages.info(request, 'This booking is already paid!')
        return redirect('bookings:booking_detail', pnr=booking.pnr)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        # Simulate payment processing
        transaction_id = generate_transaction_id()
        
        booking.payment_method = payment_method
        booking.transaction_id = transaction_id
        booking.payment_status = 'success'
        booking.payment_date = datetime.now()
        booking.save()
        
        messages.success(request, f'Payment successful! Transaction ID: {transaction_id}')
        return redirect('bookings:booking_detail', pnr=booking.pnr)
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'bookings/payment.html', context)


@login_required
def my_bookings(request):
    """View All User Bookings"""
    bookings = Payment.objects.filter(user=request.user).order_by('-booking_date')
    
    context = {
        'bookings': bookings,
        'today': date.today(),
    }
    
    return render(request, 'bookings/my_bookings.html', context)


@login_required
def booking_detail(request, pnr):
    """View Single Booking Detail"""
    booking = get_object_or_404(Payment, pnr=pnr, user=request.user)
    
    context = {
        'booking': booking,
        'today': date.today(),
    }
    
    return render(request, 'bookings/booking_detail.html', context)


@login_required
@transaction.atomic
def cancel_booking(request, booking_id):
    """Cancel Booking - Feature Disabled"""
    messages.info(request, 'Cancellation feature is currently disabled.')
    return redirect('bookings:my_bookings')


@login_required
def download_ticket(request, pnr):
    """Download Ticket as PDF"""
    booking = get_object_or_404(Payment, pnr=pnr, user=request.user)
    
    if booking.payment_status != 'success':
        messages.error(request, 'Please complete payment first!')
        return redirect('bookings:payment', pnr=booking.pnr)
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'bookings/ticket.html', context)
