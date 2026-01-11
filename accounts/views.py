from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User


def register(request):
    """User Registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone_number')
        address = request.POST.get('address')
        
        # Validation
        if password != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('accounts:register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('accounts:register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('accounts:register')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone_number=phone,
            address=address,
            role='customer'
        )
        
        messages.success(request, 'Registration successful! Please login.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/register.html')


def user_login(request):
    """User Login - Redirect based on role"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect based on role
            if user.is_admin_user():
                return redirect('accounts:admin_dashboard')
            else:
                return redirect('trains:home')
        else:
            messages.error(request, 'Invalid username or password!')
            return redirect('accounts:login')
    
    return render(request, 'accounts/login.html')


@login_required
def user_logout(request):
    """User Logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('trains:home')


@login_required
def profile(request):
    """View Profile"""
    return render(request, 'accounts/profile.html')


@login_required
def edit_profile(request):
    """Edit Profile"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone_number')
        user.address = request.POST.get('address')
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/edit_profile.html')


@login_required
def change_password(request):
    """Change Password"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Old password is incorrect!')
            return redirect('accounts:change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match!')
            return redirect('accounts:change_password')
        
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/change_password.html')


@login_required
def admin_dashboard(request):
    """Admin Dashboard - Only for admin users"""
    if not request.user.is_admin_user():
        messages.error(request, 'Access denied! Admin only.')
        return redirect('trains:home')
    
    from trains.models import Train, Station, Route, TrainSchedule
    from bookings.models import Payment
    
    context = {
        'total_trains': Train.objects.count(),
        'total_stations': Station.objects.count(),
        'total_routes': Route.objects.count(),
        'total_bookings': Payment.objects.count(),
        'recent_trains': Train.objects.all()[:5],
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)