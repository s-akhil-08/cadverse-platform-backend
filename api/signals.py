import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import User, ProjectFile, UserFeedback, EmployeeProfile
from .email_backends import SignalEmailBackend


@receiver(post_save, sender=User)
def send_user_creation_notification(sender, instance, created, **kwargs):
    """
    Signal to notify admin when a new user is created and send a welcome email to the user.
    """
    if created and not instance.is_superuser:
        admin_subject = 'New User Registration Notification'
        admin_context = {
            'user': instance,
            'settings': settings,
        }
        admin_html_message = render_to_string('emails/admin_user_creation.html', admin_context)
        admin_plain_message = strip_tags(admin_html_message)

        try:
            send_mail(
                subject=admin_subject,
                message=admin_plain_message,
                from_email=settings.SIGNAL_DEFAULT_FROM_EMAIL,
                recipient_list=['cadverse.a@gmail.com'],
                html_message=admin_html_message,
                fail_silently=False,
                connection=SignalEmailBackend(),
            )
        except Exception as e:
            print(f"Error sending admin notification: {e}")

        # Send welcome email to user
        user_subject = 'Welcome to CADverse!'
        user_context = {
            'user': instance,
            'settings': settings,
        }
        user_html_message = render_to_string('emails/welcome_email.html', user_context)
        user_plain_message = strip_tags(user_html_message)

        try:
            send_mail(
                subject=user_subject,
                message=user_plain_message,
                from_email=settings.SIGNAL_DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                html_message=user_html_message,
                fail_silently=False,
                connection=SignalEmailBackend(),
            )
        except Exception as e:
            print(f"Error sending welcome email to user: {e}")


@receiver(post_save, sender=ProjectFile)
def send_project_upload_notification(sender, instance, created, **kwargs):
    """
    Signal to notify admin when a project file is uploaded.
    """
    if created:
        subject = 'New Project File Uploaded'
        context = {
            'project_file': instance,
            'project': instance.project,
            'user': instance.project.user,
            'settings': settings,
        }
        html_message = render_to_string('emails/admin_project_upload.html', context)
        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.SIGNAL_DEFAULT_FROM_EMAIL,
                recipient_list=['cadverse.a@gmail.com'],
                html_message=html_message,
                fail_silently=False,
                connection=SignalEmailBackend(),
            )
        except Exception as e:
            print(f"Error sending project upload notification: {e}")


@receiver(post_save, sender=UserFeedback)
def send_user_feedback_notification(sender, instance, created, **kwargs):
    """
    Signal to notify admin when a user submits feedback.
    """
    if created:
        subject = 'New User Feedback Submitted'
        context = {
            'feedback': instance,
            'user': instance.user,
            'project': instance.project,
            'settings': settings,
        }
        html_message = render_to_string('emails/admin_feedback.html', context)
        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.SIGNAL_DEFAULT_FROM_EMAIL,
                recipient_list=['cadverse.a@gmail.com'],
                html_message=html_message,
                fail_silently=False,
                connection=SignalEmailBackend(),
            )
        except Exception as e:
            print(f"Error sending feedback notification: {e}")


@receiver(post_save, sender=UserFeedback)
def send_feedback_approved_notification(sender, instance, created, **kwargs):
    """
    Signal to notify user when their feedback is approved.
    """
    if not created and instance.is_approved:
        subject = 'Your Feedback Has Been Approved!'
        context = {
            'feedback': instance,
            'user': instance.user,
            'project': instance.project,
            'settings': settings,
        }
        html_message = render_to_string('emails/feedback_approved.html', context)
        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.SIGNAL_DEFAULT_FROM_EMAIL,
                recipient_list=[instance.user.email],
                html_message=html_message,
                fail_silently=False,
                connection=SignalEmailBackend(),
            )
        except Exception as e:
            print(f"Error sending feedback approval email: {e}")


@receiver(post_save, sender=User)
def handle_employee_profile_creation(sender, instance, created, **kwargs):
    """
    Signal to automatically create EmployeeProfile when a user is marked as staff (employee).
    """
    if instance.is_staff and not instance.is_superuser:
        EmployeeProfile.objects.get_or_create(user=instance)
