from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.authtoken.models import Token


class UserManager(BaseUserManager):
    def create_user(self, email, name, mobile, password=None, is_verified=False, is_active=True, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            mobile=mobile,
            is_verified=is_verified,
            is_active=is_active,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, mobile, password, **extra_fields):
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.create_user(
            email,
            name,
            mobile,
            password,
            **extra_fields
        )
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'mobile']

    class Meta:
        db_table = 'api_user'

    def __str__(self):
        return self.email


class TempUser(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=20)
    password = models.CharField(max_length=128)
    raw_password = models.CharField(max_length=128)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'api_tempuser'

    def __str__(self):
        return self.email


class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.email}"


class Project(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=100)
    status = models.CharField(
        max_length=50,
        choices=[
            ('Submitted', 'Submitted'),
            ('In Review', 'In Review'),
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed')
        ],
        default='Submitted'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProjectFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    file_url = models.URLField(max_length=500)
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name


class RequestLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=255)
    status_code = models.IntegerField()
    response_time = models.FloatField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.endpoint} - {self.timestamp}"


class Notification(models.Model):
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.user.email}"


class PasswordChangeHistory(models.Model):
    """
    Model to store history of password changes.
    Tracks user, old and new hashed passwords, and timestamp.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_changes'
    )
    old_password_hashed = models.CharField(max_length=128, help_text="Hashed old password")
    new_password_hashed = models.CharField(max_length=128, help_text="Hashed new password")
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Password Change History"
        verbose_name_plural = "Password Change Histories"

    def __str__(self):
        return f"Password change for {self.user.email} at {self.changed_at}"


class UserFeedback(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_id')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, db_column='project_id')
    rating = models.SmallIntegerField(null=True, blank=True)
    feedback_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    emojis = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    short_note = models.TextField(blank=True, null=True)
    popup_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'api_userfeedback'

    def __str__(self):
        return f"Feedback by {self.user.name or self.user.email}"

    def clean(self):
        if self.rating is not None and (self.rating < 1 or self.rating > 5):
            raise ValidationError({'rating': 'Rating must be between 1 and 5.'})

    def save(self, *args, **kwargs):
        if self.status == 'approved':
            self.is_approved = True
        elif self.is_approved and self.status == 'pending':
            self.status = 'approved'
        super().save(*args, **kwargs)


class FeedbackDetail(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for User {self.user.id} and Project {self.project.id}"


class EmailLog(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    html_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Email to {self.recipient.email} - {self.sent_at}"

    class Meta:
        ordering = ['-sent_at']


class APIUser(Token):
    class Meta:
        proxy = True
        verbose_name = "API User"
        verbose_name_plural = "API Users"


class EmployeeProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        limit_choices_to={'is_staff': True}
    )
    visible_models = models.ManyToManyField(
        ContentType,
        blank=True,
        help_text="Select which admin panels (models) should be visible to this employee."
    )

    class Meta:
        verbose_name = "Employee Profile"
        verbose_name_plural = "Employee Profiles"

    def __str__(self):
        return f"Employee Profile: {self.user.email}"


class ShowcaseItem(models.Model):
    title = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    before_url = models.URLField(blank=True, null=True)
    after_url = models.URLField(blank=True, null=True)
    feedback = models.ForeignKey(
        'UserFeedback',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='showcase_items'
    )

    class Meta:
        db_table = 'showcaseitem'
        ordering = ['-created_at']

    def __str__(self):
        return self.title or "Untitled Showcase"