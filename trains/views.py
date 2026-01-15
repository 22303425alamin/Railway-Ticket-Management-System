from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Train, Station, Route, TrainSchedule
from datetime import datetime, date, timedelta


def home(request):
    """Home Page - Search Form"""
    stations = Station.objects.all().order_by('station_name')
    today = date.today()
    max_date = today + timedelta(days=10)
    
    context = {
        'stations': stations,
        'today': today,
        'max_date': max_date,
    }
    
    # Pre-fill for modify search
    if request.GET.get('modify'):
        context['origin'] = request.session.get('search_origin')
        context['destination'] = request.session.get('search_destination')
        context['journey_date'] = request.session.get('journey_date')
        context['seat_type'] = request.session.get('seat_type')
    
    return render(request, 'trains/home.html', context)


def search_trains(request):
    """Search Trains - Normal Search"""
    if request.method == 'POST':
        origin_code = request.POST.get('origin')
        destination_code = request.POST.get('destination')
        journey_date_str = request.POST.get('journey_date')
        seat_type = request.POST.get('seat_type', '')
        
        # Store in session for deep search
        request.session['search_origin'] = origin_code
        request.session['search_destination'] = destination_code
        request.session['journey_date'] = journey_date_str
        request.session['seat_type'] = seat_type
        request.session['deep_search_count'] = 0
        
        try:
            origin = Station.objects.get(station_code=origin_code)
            destination = Station.objects.get(station_code=destination_code)
            journey_date = datetime.strptime(journey_date_str, '%Y-%m-%d').date()
            
            # Validate date range
            today = date.today()
            max_date = today + timedelta(days=10)
            
            if journey_date < today:
                messages.error(request, 'Journey date cannot be in the past!')
                return redirect('trains:home')
            
            if journey_date > max_date:
                messages.error(request, 'You can only book tickets up to 10 days in advance!')
                return redirect('trains:home')
                
        except Station.DoesNotExist:
            messages.error(request, 'Invalid station selected!')
            return redirect('trains:home')
        except ValueError:
            messages.error(request, 'Invalid date format!')
            return redirect('trains:home')
        
        # Find trains that have both stations in route
        trains_found = []
        all_trains = Train.objects.all()
        
        for train in all_trains:
            origin_route = Route.objects.filter(train=train, station=origin).first()
            dest_route = Route.objects.filter(train=train, station=destination).first()
            
            if origin_route and dest_route:
                if origin_route.sequence_order < dest_route.sequence_order:
                    # Filter by seat type if provided
                    if seat_type and seat_type not in train.classes_available:
                        continue
                    
                    # Calculate fare
                    distance = float(dest_route.distance_from_origin - origin_route.distance_from_origin)
                    base_fare = distance * 2
                    reservation = 50
                    tax = (base_fare + reservation) * 0.05
                    total_fare = base_fare + reservation + tax

                    
                    trains_found.append({
                        'train': train,
                        'origin_route': origin_route,
                        'dest_route': dest_route,
                        'distance': distance,
                        'base_fare': base_fare,
                        'total_fare': round(total_fare, 2),
                    })
        
        context = {
            'trains': trains_found,
            'origin': origin,
            'destination': destination,
            'journey_date': journey_date,
            'show_deep_search': True,
            'search_type': 'normal'
        }
        
        return render(request, 'trains/search_results.html', context)
    
    return render(request, 'trains/home.html')


def deep_search(request):
    """Deep Search - Find trains to nearby stations"""
    origin_code = request.session.get('search_origin')
    destination_code = request.session.get('search_destination')
    journey_date_str = request.session.get('journey_date')
    deep_count = request.session.get('deep_search_count', 0)
    
    if not all([origin_code, destination_code, journey_date_str]):
        messages.error(request, 'Please perform a search first!')
        return render(request, 'trains/home.html')
    
    try:
        origin = Station.objects.get(station_code=origin_code)
        destination = Station.objects.get(station_code=destination_code)
        journey_date = datetime.strptime(journey_date_str, '%Y-%m-%d').date()
    except:
        messages.error(request, 'Invalid search data!')
        return render(request, 'trains/home.html')
    
    dest_routes = Route.objects.filter(station=destination)
    
    if not dest_routes.exists():
        messages.error(request, f'No route information available for {destination.station_name}')
        return render(request, 'trains/home.html')
    
    dest_route = dest_routes.first()
    train_obj = dest_route.train
    
    if deep_count == 0:
        new_sequence = dest_route.sequence_order + 1
        request.session['deep_search_count'] = 1
        search_direction = "next"
    elif deep_count == 1:
        new_sequence = dest_route.sequence_order - 1
        request.session['deep_search_count'] = 2
        search_direction = "previous"
    else:
        messages.info(request, 'Deep search limit reached. No more nearby stations available.')
        return render(request, 'trains/search_results.html', {
            'trains': [],
            'origin': origin,
            'destination': destination,
            'show_deep_search': False
        })
    
    try:
        new_dest_route = Route.objects.get(
            train=train_obj,
            sequence_order=new_sequence
        )
        new_destination = new_dest_route.station
    except Route.DoesNotExist:
        messages.error(request, f'No {search_direction} station found in route.')
        return render(request, 'trains/search_results.html', {
            'trains': [],
            'origin': origin,
            'destination': destination,
            'show_deep_search': False
        })
    
    trains_found = []
    all_trains = Train.objects.all()
    
    for train in all_trains:
        origin_route = Route.objects.filter(train=train, station=origin).first()
        dest_route_new = Route.objects.filter(train=train, station=new_destination).first()
        
        if origin_route and dest_route_new:
            if origin_route.sequence_order < dest_route_new.sequence_order:
                distance = float(dest_route_new.distance_from_origin - origin_route.distance_from_origin)
                base_fare = distance * 2
                reservation = 50
                tax = (base_fare + reservation) * 0.05
                total_fare = base_fare + reservation + tax
                trains_found.append({
                    'train': train,
                    'origin_route': origin_route,
                    'dest_route': dest_route_new,
                    'distance': distance,
                    'base_fare': base_fare,
                    'total_fare': round(total_fare, 2),
                })
    
    context = {
          
        'trains': trains_found,
        'origin': origin,
        'destination': new_destination,
        'original_destination': destination,
        'journey_date': journey_date,
        'show_deep_search': deep_count < 2,
        'search_type': 'deep',
        'deep_count': deep_count
    }

    
    return render(request, 'trains/search_results.html', context)


def train_detail(request, train_id):
    """Train Details"""
    train = get_object_or_404(Train, id=train_id)
    routes = Route.objects.filter(train=train).order_by('sequence_order')
    
    context = {
        'train': train,
        'routes': routes
    }
    
    return render(request, 'trains/train_detail.html', context)


# ==================== ADMIN FUNCTIONS ====================

def admin_required(view_func):
    """Decorator to check if user is admin"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_user():
            messages.error(request, 'Access denied! Admin only.')
            return redirect('trains:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_train_list(request):
    """Admin: List all trains"""
    trains = Train.objects.all()
    return render(request, 'trains/admin/train_list.html', {'trains': trains})


@admin_required
def admin_train_add(request):
    """Admin: Add new train"""
    if request.method == 'POST':
        train = Train.objects.create(
            train_number=request.POST.get('train_number'),
            train_name=request.POST.get('train_name'),
            total_seats=request.POST.get('total_seats'),
            available_seats=request.POST.get('total_seats'),
            total_coaches=request.POST.get('total_coaches'),
            classes_available=request.POST.get('classes_available'),
            off_day=request.POST.get('off_day', '')
        )
        messages.success(request, f'Train {train.train_name} added successfully!')
        return redirect('trains:admin_train_list')
    
    return render(request, 'trains/admin/train_form.html')


@admin_required
def admin_train_edit(request, train_id):
    """Admin: Edit train"""
    train = get_object_or_404(Train, id=train_id)
    
    if request.method == 'POST':
        train.train_number = request.POST.get('train_number')
        train.train_name = request.POST.get('train_name')
        train.total_seats = request.POST.get('total_seats')
        train.total_coaches = request.POST.get('total_coaches')
        train.classes_available = request.POST.get('classes_available')
        train.off_day = request.POST.get('off_day', '')
        train.save()
        
        messages.success(request, f'Train {train.train_name} updated successfully!')
        return redirect('trains:admin_train_list')
    
    return render(request, 'trains/admin/train_form.html', {'train': train})


@admin_required
def admin_train_delete(request, train_id):
    """Admin: Delete train"""
    train = get_object_or_404(Train, id=train_id)
    train_name = train.train_name
    train.delete()
    messages.success(request, f'Train {train_name} deleted successfully!')
    return redirect('trains:admin_train_list')


@admin_required
def admin_route_list(request):
    """Admin: List all routes"""
    routes = Route.objects.all().select_related('train', 'station')
    return render(request, 'trains/admin/route_list.html', {'routes': routes})


@admin_required
def admin_route_add(request):
    """Admin: Add new route"""
    if request.method == 'POST':
        route = Route.objects.create(
            train_id=request.POST.get('train'),
            station_id=request.POST.get('station'),
            sequence_order=request.POST.get('sequence_order'),
            distance_from_origin=request.POST.get('distance_from_origin'),
            departure_time=request.POST.get('departure_time'),
            arrival_time=request.POST.get('arrival_time') or None
        )
        messages.success(request, 'Route added successfully!')
        return redirect('trains:admin_route_list')
    
    trains = Train.objects.all()
    stations = Station.objects.all()
    return render(request, 'trains/admin/route_form.html', {
        'trains': trains,
        'stations': stations
    })


@admin_required
def admin_route_delete(request, route_id):
    """Admin: Delete route"""
    route = get_object_or_404(Route, id=route_id)
    route.delete()
    messages.success(request, 'Route deleted successfully!')
    return redirect('trains:admin_route_list')


@admin_required
def admin_schedule_list(request):
    """Admin: List all schedules"""
    schedules = TrainSchedule.objects.all().select_related('train')
    return render(request, 'trains/admin/schedule_list.html', {'schedules': schedules})


@admin_required
def admin_schedule_edit(request, schedule_id):
    """Admin: Edit schedule"""
    schedule = get_object_or_404(TrainSchedule, id=schedule_id)
    
    if request.method == 'POST':
        schedule.departure_time = request.POST.get('departure_time')
        schedule.arrival_time = request.POST.get('arrival_time')
        schedule.off_days = request.POST.get('off_days', '')
        schedule.status = request.POST.get('status')
        schedule.save()
        
        messages.success(request, f'Schedule for {schedule.train.train_name} updated!')
        return redirect('trains:admin_schedule_list')
    
    return render(request, 'trains/admin/schedule_form.html', {'schedule': schedule})
