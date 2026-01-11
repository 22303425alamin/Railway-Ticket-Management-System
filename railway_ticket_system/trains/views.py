from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .models import Train, Station, Route, TrainSchedule
from datetime import datetime


def home(request):
    """Home Page - Search Form"""
    stations = Station.objects.all().order_by('station_name')
    return render(request, 'trains/home.html', {'stations': stations})


def search_trains(request):
    """Search Trains - Normal Search"""
    if request.method == 'POST':
        origin_code = request.POST.get('origin')
        destination_code = request.POST.get('destination')
        journey_date_str = request.POST.get('journey_date')
        
        # Store in session for deep search
        request.session['search_origin'] = origin_code
        request.session['search_destination'] = destination_code
        request.session['journey_date'] = journey_date_str
        request.session['deep_search_count'] = 0
        
        try:
            origin = Station.objects.get(station_code=origin_code)
            destination = Station.objects.get(station_code=destination_code)
            journey_date = datetime.strptime(journey_date_str, '%Y-%m-%d').date()
        except:
            messages.error(request, 'Invalid search parameters!')
            return render(request, 'trains/home.html')
        
        # Find trains that have both stations in route
        trains_found = []
        
        # Get all trains
        all_trains = Train.objects.all()
        
        for train in all_trains:
            # Check if train has both stations in correct order
            origin_route = Route.objects.filter(train=train, station=origin).first()
            dest_route = Route.objects.filter(train=train, station=destination).first()
            
            if origin_route and dest_route:
                # Check sequence order
                if origin_route.sequence_order < dest_route.sequence_order:
                    # Check if train schedule exists for this date
                    schedule = TrainSchedule.objects.filter(
                        train=train,
                        journey_date=journey_date,
                        status='running'
                    ).first()
                    
                    if schedule:
                        trains_found.append({
                            'train': train,
                            'schedule': schedule,
                            'origin_route': origin_route,
                            'dest_route': dest_route,
                        })
        
        context = {
            'trains': trains_found,
            'origin': origin,
            'destination': destination,
            'journey_date': journey_date,
            'show_deep_search': len(trains_found) == 0,
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
    
    # Find destination in any train route
    dest_routes = Route.objects.filter(station=destination)
    
    if not dest_routes.exists():
        messages.error(request, f'No route information available for {destination.station_name}')
        return render(request, 'trains/home.html')
    
    # Get first train's route as reference
    dest_route = dest_routes.first()
    train_obj = dest_route.train
    
    # Determine new destination based on deep search count
    if deep_count == 0:
        # First deep search: X+1 (next station)
        new_sequence = dest_route.sequence_order + 1
        request.session['deep_search_count'] = 1
        search_direction = "next"
    elif deep_count == 1:
        # Second deep search: X-1 (previous station)
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
    
    # Find station with new sequence
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
    
    # Search trains to new destination
    trains_found = []
    all_trains = Train.objects.all()
    
    for train in all_trains:
        origin_route = Route.objects.filter(train=train, station=origin).first()
        dest_route_new = Route.objects.filter(train=train, station=new_destination).first()
        
        if origin_route and dest_route_new:
            if origin_route.sequence_order < dest_route_new.sequence_order:
                schedule = TrainSchedule.objects.filter(
                    train=train,
                    journey_date=journey_date,
                    status='running'
                ).first()
                
                if schedule:
                    trains_found.append({
                        'train': train,
                        'schedule': schedule,
                        'origin_route': origin_route,
                        'dest_route': dest_route_new,
                    })
    
    context = {
        'trains': trains_found,
        'origin': origin,
        'destination': new_destination,
        'original_destination': destination,
        'journey_date': journey_date,
        'show_deep_search': deep_count < 2 and len(trains_found) == 0,
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