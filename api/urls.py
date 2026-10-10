from django.urls import path
from . import views

urlpatterns = [
    # Auth & OTP endpoints
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('api/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password-api'),
    path('verify-reset-otp/', views.VerifyPasswordResetOTPView.as_view(), name='verify-reset-otp'),
    path('verify-forgot-otp/', views.VerifyOTPViewForget.as_view(), name='verify-forgot-otp'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('api/reset-password/', views.ResetPasswordView.as_view(), name='reset-password-api'),

    # Communication & Files
    path('send-message/', views.SendMessageView.as_view(), name='send-message'),
    path('upload-file/', views.UploadFileView.as_view(), name='upload-file'),

    # Projects
    path('projects/', views.list_projects, name='list-projects'),
    path('projects/<int:project_id>/', views.project_detail, name='project-detail'),
    path('api/projects/<int:projectId>/', views.project_detail, name='project-detail-alias'),
    path('protected/', views.protected_view, name='protected'),
    path('project-status-stream/', views.project_status_stream, name='project_status_stream'),

    # Feedback & Showcase
    path('submit-feedback/', views.SubmitFeedbackView.as_view(), name='submit-feedback'),
    path('feedback/', views.FeedbackListView.as_view(), name='feedback-list'),
    path('feedback-details/', views.FeedbackDetailListView.as_view(), name='feedback-details'),
    path('user-feedback/', views.user_feedback_list, name='user-feedback-list'),
    path('feedback/<int:feedback_id>/increment-popup/', views.increment_feedback_popup, name='increment-feedback-popup'),
    path('get-project-title/<int:feedback_id>/', views.GetProjectTitleView.as_view(), name='get-project-title'),
    path('showcase/', views.ShowcaseListView.as_view(), name='showcase-list'),
    path('feedback-stats/', views.FeedbackStatsView.as_view(), name='feedback-stats'),

    # Employee Permissions
    path('employee/permissions/', views.EmployeePermissionsView.as_view(), name='employee-permissions'),
]
