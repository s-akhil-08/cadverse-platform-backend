from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType


class EmployeeAdminSite(AdminSite):
    site_header = "CADverse Admin & Demo Portal"
    site_title = "CADverse Administration Portal"
    index_title = "Welcome to the CADverse Management Dashboard"

    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        User = get_user_model()

        # 1. Total Employees / Staff
        total_employees = User.objects.filter(is_staff=True, is_superuser=False).count()

        # 2. Active Permissions
        active_employees = User.objects.filter(is_staff=True, is_active=True)
        active_permissions_count = 0
        for emp in active_employees:
            active_permissions_count += emp.user_permissions.count()
            for group in emp.groups.all():
                active_permissions_count += group.permissions.count()

        # 3. Target Models
        target_models_keys = [
            ('api', 'user'),
            ('api', 'userfeedback'),
            ('api', 'project'),
            ('api', 'projectfile'),
            ('api', 'emaillog'),
            ('api', 'apiuser'),
            ('api', 'notification'),
            ('api', 'showcaseitem'),
        ]

        if request.user.is_superuser:
            restricted_count = 0
        else:
            try:
                profile = request.user.employee_profile
                visible_cts = profile.visible_models.all()
                if visible_cts.exists():
                    visible_keys = {(ct.app_label, ct.model) for ct in visible_cts}
                    restricted_count = sum(1 for app, model in target_models_keys if (app, model) not in visible_keys)
                else:
                    restricted_count = 0
            except AttributeError:
                restricted_count = 0

        # 4. Last Login
        last_login = request.user.last_login

        extra_context.update({
            'total_employees': total_employees,
            'active_permissions_count': active_permissions_count,
            'restricted_count': restricted_count,
            'last_login_time': last_login,
            'show_metrics': request.user.is_staff,
            'is_demo_mode': not request.user.is_superuser,
        })

        return super().index(request, extra_context=extra_context)

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        if request.user.is_superuser:
            return app_list

        try:
            profile = request.user.employee_profile
            visible_content_types = profile.visible_models.all()
            if visible_content_types.exists():
                visible_keys = {f"{ct.app_label}.{ct.model}" for ct in visible_content_types}
                new_app_list = []
                for app in app_list:
                    new_models = []
                    for model in app['models']:
                        model_name = model['object_name'].lower()
                        app_label = app['app_label']
                        model_key = f"{app_label}.{model_name}"
                        if model_key in visible_keys:
                            new_models.append(model)
                    if new_models:
                        app_copy = app.copy()
                        app_copy['models'] = new_models
                        new_app_list.append(app_copy)
                return new_app_list
            else:
                # If no specific restrictions set, demo admin can view all panels in read-only mode
                return app_list
        except AttributeError:
            return app_list
