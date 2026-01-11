from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from .models import Booking, Passenger, Payment, Cancellation
from trains.models import Train, TrainSchedule, Station, Route
from datetime import datetime
import random
import string


def generate_transaction_id():
    """Generate random transaction ID"""
    return 'TXN' + ''.join(random.choices(string.digits, k=12))


@login_required
def new_booking(request, train_id):
    """New Booking Form - Passenger Details"""
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
        schedule = TrainSchedule.objects.get(train=train, journey_date=journey_date)
        
        # Get route details for fare calculation
        origin_route = Route.objects.filter(train=train, station=origin).first()
        dest_route = Route.objects.filter(train=train, station=destination).first()
        
        if not origin_route or not dest_route:
            messages.error(request, 'Route information not available!')
            return redirect('trains:home')
        
        # Calculate distance
        distance = dest_route.distance_from_origin - origin_route.distance_from_origin
        
        # Calculate fare for 1 passenger
        fare_per_km = 2
        fare_per_passenger = distance * fare_per_km
        reservation_charge = 50
        tax = (fare_per_passenger + reservation_charge) * 0.05
        total_fare = fare_per_passenger + reservation_charge + tax
        
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
        'fare_per_passenger': fare_per_passenger,
        'tax_amount': tax,
        'total_fare': total_fare,
    }
    
    return render(request, 'bookings/new_booking.html', context)


@login_required
@transaction.atomic
def confirm_booking(request):
    """Confirm Booking and Create Records"""
    if request.method != 'POST':
        return redirect('trains:home')
    
    # Get form data
    train_id = request.POST.get('train_id')
    origin_code = request.POST.get('origin_code')
    destination_code = request.POST.get('destination_code')
    journey_date_str = request.POST.get('journey_date')
    
    # Passenger details
    passenger_names = request.POST.getlist('passenger_name[]')
    passenger_ages = request.POST.getlist('passenger_age[]')
    passenger_genders = request.POST.getlist('passenger_gender[]')
    
    # Validate
    if not all([train_id, origin_code, destination_code, journey_date_str]):
        messages.error(request, 'Invalid booking data!')
        return redirect('trains:home')
    
    if not passenger_names or len(passenger_names) == 0:
        messages.error(request, 'Please add at least one passenger!')
        return redirect('trains:home')
    
    try:
        train = Train.objects.get(id=train_id)
        origin = Station.objects.get(station_code=origin_code)
        destination = Station.objects.get(station_code=destination_code)
        journey_date = datetime.strptime(journey_date_str, '%Y-%m-%d').date()
        schedule = TrainSchedule.objects.get(train=train, journey_date=journey_date)
        
        # Get route details for fare calculation
        origin_route = Route.objects.filter(train=train, station=origin).first()
        dest_route = Route.objects.filter(train=train, station=destination).first()
        
        # Calculate distance
        distance = dest_route.distance_from_origin - origin_route.distance_from_origin
        
        # Fare calculation: 2 BDT per KM per passenger
        fare_per_km = 2
        base_fare = distance * fare_per_km * len(passenger_names)
        reservation_charge = 50
        
    except Exception as e:
        messages.error(request, f'Invalid booking information! {str(e)}')
        return redirect('trains:home')
    
    # Create booking
    booking = Booking.objects.create(
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
        status='booked'
    )
    
    # Calculate fare
    booking.calculate_fare()
    
    # Create passengers
    for i in range(len(passenger_names)):
        Passenger.objects.create(
            booking=booking,
            name=passenger_names[i],
            age=passenger_ages[i],
            gender=passenger_genders[i]
        )
    
    # Store booking ID in session for payment
    request.session['pending_booking_id'] = booking.id
    
    messages.success(request, f'Booking created! PNR: {booking.pnr}')
    return redirect('bookings:payment', booking_id=booking.id)


@login_required
def payment(request, booking_id):
    """Payment Page - Simulated Payment Gateway"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if hasattr(booking, 'payment'):
        messages.info(request, 'This booking is already paid!')
        return redirect('bookings:booking_detail', pnr=booking.pnr)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        # Simulate payment processing (5 seconds delay would be in frontend JS)
        transaction_id = generate_transaction_id()
        
        Payment.objects.create(
            booking=booking,
            amount=booking.total_fare,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status='success'
        )
        
        messages.success(request, f'Payment successful! Transaction ID: {transaction_id}')
        return redirect('bookings:booking_detail', pnr=booking.pnr)
    
    passengers = booking.passengers.all()
    
    context = {
        'booking': booking,
        'passengers': passengers
    }
    
    return render(request, 'bookings/payment.html', context)


@login_required
def my_bookings(request):
    """View All User Bookings"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    
    context = {
        'bookings': bookings
    }
    
    return render(request, 'bookings/my_bookings.html', context)


@login_required
def booking_detail(request, pnr):
    """View Single Booking Detail"""
    booking = get_object_or_404(Booking, pnr=pnr, user=request.user)
    passengers = booking.passengers.all()
    
    context = {
        'booking': booking,
        'passengers': passengers
    }
    
    return render(request, 'bookings/booking_detail.html', context)


@login_required
@transaction.atomic
def cancel_booking(request, booking_id):
    """Cancel Booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status != 'booked':
        messages.error(request, 'This booking cannot be cancelled!')
        return redirect('bookings:booking_detail', pnr=booking.pnr)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        # Create cancellation
        cancellation = Cancellation.objects.create(
            booking=booking,
            reason=reason
        )
        cancellation.calculate_refund()
        
        # Update booking status
        booking.status = 'cancelled'
        booking.save()
        
        messages.success(request, f'Booking cancelled! Refund amount: ৳{cancellation.refund_amount}')
        return redirect('bookings:booking_detail', pnr=booking.pnr)
    
    context = {
        'booking': booking
    }
    
    return render(request, 'bookings/cancel_booking.html', context)


@login_required
def download_ticket(request, pnr):
    """Download Ticket as PDF (Simple HTML for now)"""
    booking = get_object_or_404(Booking, pnr=pnr, user=request.user)
    
    if booking.status != 'booked':
        messages.error(request, 'Cannot download ticket for cancelled booking!')
        return redirect('bookings:booking_detail', pnr=pnr)
    
    if not hasattr(booking, 'payment'):
        messages.error(request, 'Please complete payment first!')
        return redirect('bookings:payment', booking_id=booking.id)
    
    passengers = booking.passengers.all()
    
    context = {
        'booking': booking,
        'passengers': passengers
    }
    
    # For now, render HTML template (PDF generation will be added later)
    return render(request, 'bookings/ticket.html', context)