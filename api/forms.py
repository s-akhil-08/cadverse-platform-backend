from django import forms
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from api.models import EmployeeProfile, User
from django.conf import settings


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = ['user', 'visible_models']
        widgets = {
            'visible_models': forms.MultipleHiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['visible_models'].required = False
        
        # Populate initial values for the grid
        self.grid_data = {}
        if self.instance and self.instance.pk:
            user = self.instance.user
            user_perms = user.user_permissions.all()
            user_perm_codenames = {p.codename for p in user_perms}
            visible_cts = self.instance.visible_models.all()
            visible_ids = {ct.id for ct in visible_cts}
        else:
            user_perm_codenames = set()
            visible_ids = set()

        self.target_models = [
            {'name': 'Users', 'app': 'api', 'model': 'user', 'label': 'Users'},
            {'name': 'User Feedbacks', 'app': 'api', 'model': 'userfeedback', 'label': 'User Feedbacks'},
            {'name': 'Projects', 'app': 'api', 'model': 'project', 'label': 'Projects'},
            {'name': 'Project Files', 'app': 'api', 'model': 'projectfile', 'label': 'Project Files'},
            {'name': 'Email Logs', 'app': 'api', 'model': 'emaillog', 'label': 'Email Logs'},
            {'name': 'API Users', 'app': 'api', 'model': 'apiuser', 'label': 'API Users'},
            {'name': 'Notifications', 'app': 'api', 'model': 'notification', 'label': 'Notifications'},
            {'name': 'Showcase Items', 'app': 'api', 'model': 'showcaseitem', 'label': 'Showcase Items'},
        ]

        for item in self.target_models:
            app_label = item['app']
            model_name = item['model']
            
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model_name)
                ct_id = ct.id
            except ContentType.DoesNotExist:
                ct_id = None
                
            self.grid_data[model_name] = {
                'ct_id': ct_id,
                'name': item['name'],
                'visible': ct_id in visible_ids if ct_id else False,
                'view': f"view_{model_name}" in user_perm_codenames,
                'add': f"add_{model_name}" in user_perm_codenames,
                'change': f"change_{model_name}" in user_perm_codenames,
                'delete': f"delete_{model_name}" in user_perm_codenames,
            }

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Ensure user is staff
        user = profile.user
        if not user.is_staff:
            user.is_staff = True
            user.save()
            
        # Process POST grid data
        target_models_names = ['user', 'userfeedback', 'project', 'projectfile', 'emaillog', 'apiuser', 'notification', 'showcaseitem']
        perms_to_add = []
        perms_to_remove = []
        visible_ct_ids = []
        
        for model_name in target_models_names:
            visible_key = f"visible_{model_name}"
            if self.data.get(visible_key) == 'on':
                try:
                    ct = ContentType.objects.get(app_label='api', model=model_name)
                    visible_ct_ids.append(ct.id)
                except ContentType.DoesNotExist:
                    pass
                    
            for action in ['view', 'add', 'change', 'delete']:
                perm_key = f"perm_{action}_{model_name}"
                codename = f"{action}_{model_name}"
                
                try:
                    ct = ContentType.objects.get(app_label='api', model=model_name)
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    
                    if self.data.get(perm_key) == 'on':
                        perms_to_add.append(perm)
                    else:
                        perms_to_remove.append(perm)
                except (ContentType.DoesNotExist, Permission.DoesNotExist):
                    pass

        def save_m2m_custom():
            profile.visible_models.set(ContentType.objects.filter(id__in=visible_ct_ids))
            user.user_permissions.remove(*perms_to_remove)
            user.user_permissions.add(*perms_to_add)

        if commit:
            profile.save()
            save_m2m_custom()
        else:
            self.save_m2m = save_m2m_custom
            
        return profile
