from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.views import LogoutView

# List all users
def user_list_view(request):
    users = User.objects.all()
    return render(request, 'users/user_list.html', {'users': users})

# Add a user
def user_add_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        is_staff = 'is_staff' in request.POST
        is_superuser = 'is_superuser' in request.POST
        is_active = 'is_active' in request.POST

        if all([first_name, last_name, email, username, password]):
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.is_active = is_active
            user.save()
            messages.success(request, "User created successfully!")
            return redirect('users:user_list')
        else:
            messages.error(request, "All fields are required.")
    
    return render(request, 'users/user_add.html')

# Edit a user
def user_edit_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        # user.email = request.POST.get('email')
        user.username = request.POST.get('username')
        # user.is_staff = 'is_staff' in request.POST
        # user.is_superuser = 'is_superuser' in request.POST
        # user.is_active = 'is_active' in request.POST

        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)

        user.save()
        messages.success(request, "User updated successfully!")
        return redirect('users:user_list')

    return render(request, 'users/user_edit.html', {'user': user})

# Delete a user
def user_delete_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect('users:user_list')


# Create your views here.
class LogoutViaGetView(LogoutView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
