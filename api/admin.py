from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import Template, Context
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django import forms
from django.core.exceptions import PermissionDenied

from .models import (
    User,
    OTP,
    Project,
    ProjectFile,
    RequestLog,
    Notification,
    PasswordChangeHistory,
    UserFeedback,
    EmailLog,
    APIUser,
    EmployeeProfile,
    ShowcaseItem
)
from .forms import EmployeeProfileForm


class RestrictedAdminMixin:
    """
    Security & Demo Control Mixin:
    - Superusers (Master Admin) have full Read/Write/Delete/Action access across all models.
    - Non-Superusers (e.g. Demo Admin) have STRICT READ-ONLY access to view records and panels.
      All Add, Change, Delete, and Mutating Bulk Actions are disabled.
    """
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        if not request.user.is_staff:
            return False
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        try:
            profile = request.user.employee_profile
            if profile.visible_models.exists():
                return profile.visible_models.filter(app_label=app_label, model=model_name).exists()
            return True
        except AttributeError:
            return True

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not request.user.is_staff:
            return False
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        try:
            profile = request.user.employee_profile
            if profile.visible_models.exists():
                return profile.visible_models.filter(app_label=app_label, model=model_name).exists()
            return True
        except AttributeError:
            return True

    def has_add_permission(self, request):
        # Only Master Admin (superuser) can add records
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Only Master Admin (superuser) can modify records
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Only Master Admin (superuser) can delete records
        return request.user.is_superuser

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            # Strip modifying bulk actions for demo users
            return {}
        return actions

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            raise PermissionDenied("Demo admin account is strictly Read-Only. Data creation and editing are disabled.")
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if not request.user.is_superuser:
            raise PermissionDenied("Demo admin account is strictly Read-Only. Deleting records is disabled.")
        super().delete_model(request, obj)


class RestrictedModelAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    pass


class ProjectFileInline(admin.TabularInline):
    model = ProjectFile
    extra = 0
    readonly_fields = ('file_name', 'uploaded_at', 'file_url_link')
    fields = ('file_name', 'file_url', 'file_url_link', 'uploaded_at')

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def file_url_link(self, obj):
        if obj.file_url:
            return format_html(
                '<a href="{}" target="_blank" style="color: #4CAF50; font-weight: bold;">View File ↗</a>',
                obj.file_url
            )
        return "No file"
    file_url_link.short_description = 'Download Link'


class ProjectAdmin(RestrictedModelAdmin):
    list_display = ('name', 'user_email', 'type', 'status', 'created_at', 'upload_count')
    list_filter = ('status', 'type', 'created_at')
    search_fields = ('name', 'user__email', 'description')
    inlines = [ProjectFileInline]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def upload_count(self, obj):
        return obj.files.count()
    upload_count.short_description = 'Uploads'


class ProjectFileAdmin(RestrictedModelAdmin):
    list_display = ('file_name', 'project_name', 'user_email', 'uploaded_at', 'view_link')
    list_filter = ('uploaded_at',)
    search_fields = ('file_name', 'project__name', 'project__user__email')

    def project_name(self, obj):
        return obj.project.name
    project_name.short_description = 'Project'

    def user_email(self, obj):
        return obj.project.user.email
    user_email.short_description = 'User'

    def view_link(self, obj):
        if obj.file_url:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file_url)
        return "No Link"
    view_link.short_description = 'Link'


class RequestLogAdmin(RestrictedModelAdmin):
    list_display = ('user', 'endpoint', 'status_code', 'response_time', 'success', 'timestamp')
    list_filter = ('status_code', 'success', 'timestamp')
    search_fields = ('user__email', 'endpoint')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__is_superuser=False).exclude(user__email__icontains='master')
        return qs


@admin.register(Notification)
class NotificationAdmin(RestrictedModelAdmin):
    list_display = ('user_email', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__email', 'subject', 'message')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__is_superuser=False).exclude(user__email__icontains='master')
        return qs


@admin.register(PasswordChangeHistory)
class PasswordChangeHistoryAdmin(RestrictedModelAdmin):
    list_display = ('user_email', 'changed_at')
    search_fields = ('user__email',)
    readonly_fields = ('user', 'old_password_hashed', 'new_password_hashed', 'changed_at')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__is_superuser=False).exclude(user__email__icontains='master')
        return qs


@admin.register(UserFeedback)
class UserFeedbackAdmin(RestrictedModelAdmin):
    list_display = ('user', 'project', 'rating', 'feedback_text', 'emojis', 'status', 'is_approved', 'popup_count', 'created_at')
    list_filter = ('status', 'is_approved', 'rating', 'created_at')
    search_fields = ('user__email', 'user__name', 'project__name', 'feedback_text')
    actions = ['approve_feedback', 'reject_feedback']

    def approve_feedback(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, "Permission denied: Demo admin cannot modify feedback.", level=messages.ERROR)
            return
        rows_updated = queryset.update(status='approved', is_approved=True)
        self.message_user(request, f"{rows_updated} feedback(s) successfully marked as Approved.")
    approve_feedback.short_description = "Mark selected feedback as Approved"

    def reject_feedback(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, "Permission denied: Demo admin cannot modify feedback.", level=messages.ERROR)
            return
        rows_updated = queryset.update(status='rejected', is_approved=False)
        self.message_user(request, f"{rows_updated} feedback(s) successfully marked as Rejected.")
    reject_feedback.short_description = "Mark selected feedback as Rejected"


class ShowcaseItemForm(forms.ModelForm):
    class Meta:
        model = ShowcaseItem
        fields = ['feedback', 'title', 'before_url', 'after_url']


@admin.register(ShowcaseItem)
class ShowcaseItemAdmin(RestrictedModelAdmin):
    form = ShowcaseItemForm
    list_display = ('title', 'get_project_name', 'get_feedback_user', 'before_preview', 'after_preview', 'created_at')
    search_fields = ('title', 'feedback__user__name', 'feedback__user__email', 'feedback__project__name')
    list_filter = ('created_at',)

    def get_project_name(self, obj):
        if obj.feedback and obj.feedback.project:
            return obj.feedback.project.name
        return "—"
    get_project_name.short_description = "Project"

    def get_feedback_user(self, obj):
        if obj.feedback and obj.feedback.user:
            return obj.feedback.user.name or obj.feedback.user.email
        return "—"
    get_feedback_user.short_description = "Client"

    def before_preview(self, obj):
        if obj.before_url:
            return format_html(
                '<div style="display:flex;align-items:center;gap:8px;">'
                '<img src="{}" style="width:60px;height:45px;object-fit:cover;border-radius:4px;border:1px solid #ccc;" />'
                '<a href="{}" target="_blank" style="font-size:12px;color:#2196F3;">Before ↗</a>'
                '</div>',
                obj.before_url, obj.before_url
            )
        return "—"
    before_preview.short_description = "Before Design"

    def after_preview(self, obj):
        if obj.after_url:
            return format_html(
                '<div style="display:flex;align-items:center;gap:8px;">'
                '<img src="{}" style="width:60px;height:45px;object-fit:cover;border-radius:4px;border:1px solid #4CAF50;" />'
                '<a href="{}" target="_blank" style="font-size:12px;color:#4CAF50;font-weight:bold;">After ↗</a>'
                '</div>',
                obj.after_url, obj.after_url
            )
        return "—"
    after_preview.short_description = "Optimized / After"

    class Media:
        js = ('admin/js/showcase_admin.js',)


class SendEmailForm(forms.Form):
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'placeholder': 'Enter email subject'}),
        help_text="Placeholders available: {{ name }}, {{ email }}, {{ mobile }}, {{ project_name }}"
    )
    project_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'placeholder': 'Optional: Project name or Project ID'}),
        help_text="Enter custom project name or Project ID (e.g. 12). If empty, defaults to 'CADverse Project'."
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 8,
            'class': 'vLargeTextField',
            'placeholder': 'Hello {{ name }},\n\nWe have an update regarding your project {{ project_name }}...'
        }),
        required=False,
        help_text="Plain text version. Placeholders: {{ name }}, {{ email }}, {{ mobile }}, {{ project_name }}"
    )
    html_message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 15,
            'class': 'vLargeTextField',
            'placeholder': '<h2>Hello {{ name }}</h2><p>Update for {{ project_name }}...</p>'
        }),
        required=False,
        help_text="HTML version. Same placeholders work."
    )

    def clean(self):
        cleaned_data = super().clean()
        message = cleaned_data.get('message')
        html_message = cleaned_data.get('html_message')

        if not message and not html_message:
            raise forms.ValidationError(
                "You must provide either a plain text message or an HTML message (or both)."
            )
        return cleaned_data


@admin.register(User)
class UserAdmin(RestrictedModelAdmin):
    list_display = ('email', 'name', 'mobile', 'is_verified', 'is_staff')
    search_fields = ('email', 'name')
    actions = ['send_custom_email']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Hide master_admin and any superuser accounts from demo view
            return qs.filter(is_superuser=False).exclude(email__icontains='master')
        return qs

    def send_custom_email(self, request, queryset):
        if not request.user.is_superuser:
            messages.error(request, "Permission denied: Demo admin cannot broadcast emails.")
            return redirect('admin:api_user_changelist')

        if 'apply' in request.POST:
            form = SendEmailForm(request.POST)
            if form.is_valid():
                subject = form.cleaned_data['subject']
                plain_message = form.cleaned_data['message']
                html_message = form.cleaned_data['html_message']
                project_input = form.cleaned_data.get('project_name', '').strip()

                messages_to_send = []
                valid_users = []

                for user in queryset:
                    if not user.email:
                        continue

                    project_name_to_use = "CADverse Project"
                    if project_input:
                        if project_input.isdigit():
                            try:
                                proj = Project.objects.get(id=int(project_input))
                                project_name_to_use = proj.name or f"Project #{proj.id}"
                            except Project.DoesNotExist:
                                project_name_to_use = f"Unknown Project (ID: {project_input})"
                        else:
                            project_name_to_use = project_input

                    context = Context({
                        'name': user.name or user.email.split('@')[0] or 'User',
                        'email': user.email,
                        'mobile': user.mobile or 'N/A',
                        'project_name': project_name_to_use,
                    })

                    rendered_subject = Template(subject).render(context)
                    rendered_plain = Template(plain_message).render(context) if plain_message else ""
                    rendered_html = Template(html_message).render(context) if html_message else None

                    msg = EmailMultiAlternatives(
                        subject=rendered_subject,
                        body=rendered_plain or " ",
                        from_email=settings.SIGNAL_DEFAULT_FROM_EMAIL,
                        to=[user.email],
                    )

                    if rendered_html:
                        msg.attach_alternative(rendered_html, "text/html")

                    messages_to_send.append(msg)
                    valid_users.append(user)

                if messages_to_send:
                    connection = get_connection(
                        backend='django.core.mail.backends.smtp.EmailBackend',
                        host=settings.SIGNAL_EMAIL_HOST,
                        port=settings.SIGNAL_EMAIL_PORT,
                        username=settings.SIGNAL_EMAIL_HOST_USER,
                        password=settings.SIGNAL_EMAIL_HOST_PASSWORD,
                        use_tls=settings.SIGNAL_EMAIL_USE_TLS,
                        fail_silently=False,
                    )

                    try:
                        connection.open()
                        connection.send_messages(messages_to_send)
                        connection.close()

                        logs = []
                        for user, msg in zip(valid_users, messages_to_send):
                            logs.append(EmailLog(
                                recipient=user,
                                subject=msg.subject,
                                message=msg.body,
                                html_message=msg.alternatives[0][0] if msg.alternatives else None,
                                success=True
                            ))
                        EmailLog.objects.bulk_create(logs)

                        messages.success(request, f"Successfully sent {len(messages_to_send)} email(s)!")

                    except Exception as e:
                        logs = []
                        for user in valid_users:
                            logs.append(EmailLog(
                                recipient=user,
                                subject=subject,
                                message=plain_message or "[HTML only]",
                                html_message=html_message,
                                success=False,
                                error_message=str(e)[:500]
                            ))
                        EmailLog.objects.bulk_create(logs)

                        messages.error(request, f"Failed to send emails: {str(e)}")

                else:
                    messages.warning(request, "No valid email addresses found in selected users.")

                return redirect('admin:api_user_changelist')

        form = SendEmailForm()
        return render(request, 'admin/send_custom_email.html', {
            'title': 'Send Custom Email (HTML or Plain Text)',
            'form': form,
            'users': queryset,
            'selected_count': queryset.count(),
        })

    send_custom_email.short_description = "Send custom email"


@admin.register(EmailLog)
class EmailLogAdmin(RestrictedModelAdmin):
    list_display = ('recipient', 'subject', 'sent_at', 'success')
    list_filter = ('success', 'sent_at')
    search_fields = ('recipient__email', 'subject')
    readonly_fields = ('sent_at',)
    date_hierarchy = 'sent_at'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(recipient__is_superuser=False).exclude(recipient__email__icontains='master')
        return qs


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(RestrictedModelAdmin):
    form = EmployeeProfileForm
    change_form_template = 'admin/api/employeeprofile/change_form.html'
    list_display = ('user_email', 'user_name', 'visible_panels_list', 'is_employee_active')
    search_fields = ('user__email', 'user__name')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Employee Email'

    def user_name(self, obj):
        return obj.user.name or 'N/A'
    user_name.short_description = 'Employee Name'

    def is_employee_active(self, obj):
        return obj.user.is_active
    is_employee_active.boolean = True
    is_employee_active.short_description = 'Active'

    def visible_panels_list(self, obj):
        cts = obj.visible_models.all()
        return ", ".join([ct.model.capitalize() for ct in cts]) or "None"
    visible_panels_list.short_description = 'Visible Admin Panels'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__is_superuser=False).exclude(user__email__icontains='master')
        return qs


@admin.register(APIUser)
class APIUserAdmin(RestrictedModelAdmin):
    list_display = ('key', 'user_email', 'user_name', 'created')
    fields = ('user',)
    ordering = ('-created',)
    search_fields = ('user__email', 'user__name', 'key')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def user_name(self, obj):
        return obj.user.name or 'N/A'
    user_name.short_description = 'User Name'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__is_superuser=False).exclude(user__email__icontains='master')
        return qs


@admin.register(OTP)
class OTPAdmin(RestrictedModelAdmin):
    list_display = ('user', 'otp', 'created_at')
    search_fields = ('user__email', 'otp')
    readonly_fields = ('user', 'otp', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__is_superuser=False).exclude(user__email__icontains='master')
        return qs


# Register remaining models
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectFile, ProjectFileAdmin)
admin.site.register(RequestLog, RequestLogAdmin)
