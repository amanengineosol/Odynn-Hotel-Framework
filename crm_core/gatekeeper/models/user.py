from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid
from .company_info import Company


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, user_type='client', **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, user_type=user_type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, password, **extra_fields)

    def ops_users_for_client(self, client_id):
        return self.filter(client_id=client_id, user_type='client_ops').order_by('-created_at')
    
    def get_ops_user(self, user_id, client_id):
        return self.get(id=user_id, client_id=client_id, user_type='client_ops')


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('operations', 'Operations'),
        ('client_admin', 'Client Admin'),
        ('client_ops' , 'Client Operations'),
    )
    client_id = models.ForeignKey(Company, blank=True, null=True, on_delete= models.CASCADE, help_text = 'This tells to which company user is related to')
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='client_admin')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for admin access

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Full name or others can go here

    def __str__(self):
        return f"{self.email} ({self.user_type})"
    
    
    
