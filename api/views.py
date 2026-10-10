import json
import logging
import os
import random
import time
import uuid
from io import BytesIO
from uuid import uuid4

import psycopg2
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction
from django.db.models import Avg, Count
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.timezone import now, timedelta
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from supabase import Client, create_client

from .models import (
    APIUser,
    EmailLog,
    EmployeeProfile,
    FeedbackDetail,
    Notification,
    OTP,
    PasswordChangeHistory,
    Project,
    ProjectFile,
    RequestLog,
    ShowcaseItem,
    TempUser,
    UserFeedback,
)
from .serializers import (
    FeedbackDetailSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    NotificationSerializer,
    OTPVerificationSerializer,
    ProjectSerializer,
    ResetPasswordSerializer,
    ShowcaseItemSerializer,
    SignupSerializer,
    UserFeedbackCreateSerializer,
    UserFeedbackSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = None
try:
    if getattr(settings, 'SUPABASE_URL', None) and getattr(settings, 'SUPABASE_KEY', None):
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
except Exception as e:
    logger.warning(f"Supabase client initialization skipped: {e}")



# ==========================================
# AUTHENTICATION & REGISTRATION VIEWS
# ==========================================

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug(f"Signup attempt with data: {request.data}")
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            temp_user = serializer.save()

            # Plain text fallback
            plain_message = f"""
Hey {temp_user.name} 👋,

Thank you for signing up for CADverse!

Your verification code is: {temp_user.otp}

⏰ This code is valid for 10 minutes.

If you did not request this, please ignore this email.

Best regards,
The CADverse Team 🚀
            """.strip()

            # HTML version from template
            html_message = render_to_string('emails/otp_verification.html', {
                'otp': temp_user.otp,
                'name': temp_user.name,
                'email': temp_user.email,
            })

            try:
                msg = EmailMultiAlternatives(
                    subject="CADverse - Verify Your Account 🔐",
                    body=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[temp_user.email]
                )
                msg.attach_alternative(html_message, "text/html")
                msg.send()

                logger.debug(f"OTP email sent to {temp_user.email}: {temp_user.otp}")
            except Exception as e:
                logger.error(f"Failed to send verification email to {temp_user.email}: {str(e)}")

            return Response({
                'message': 'Signup successful. Verification code sent to your email.'
            }, status=status.HTTP_201_CREATED)

        logger.error(f"Signup validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug(f"Verifying OTP with data: {request.data}")
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email'].lower()
            otp = serializer.validated_data['otp']
            try:
                temp_user = TempUser.objects.get(email__iexact=email, otp=otp)
                if temp_user.created_at < now() - timedelta(minutes=10):
                    temp_user.delete()
                    logger.error(f"OTP expired for email: {email}")
                    return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)

                with transaction.atomic():
                    user = User.objects.create_user(
                        email=temp_user.email,
                        name=temp_user.name,
                        mobile=temp_user.mobile,
                        password=temp_user.raw_password,
                        is_verified=True,
                        is_active=True
                    )
                    token = Token.objects.create(user=user)
                    temp_user.delete()
                    logger.debug(f"User created and TempUser deleted for email: {email}")
                    return Response({
                        'message': 'OTP verified successfully',
                        'token': token.key,
                        'user': UserSerializer(user).data
                    }, status=status.HTTP_200_OK)
            except TempUser.DoesNotExist:
                logger.error(f"Invalid OTP or email: {email}")
                return Response({'error': 'Invalid OTP or email'}, status=status.HTTP_400_BAD_REQUEST)

        logger.error(f"OTP verification failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug(f"Login request data: {request.data}")
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            logger.info(f"User authenticated: {user.email}")
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.name,
                    'mobile': user.mobile,
                    'is_verified': user.is_verified
                }
            }, status=status.HTTP_200_OK)
        logger.error(f"Login failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# FORGOT / RESET PASSWORD VIEWS
# ==========================================

class ForgotPasswordView(APIView):
    """
    API endpoint to handle forgot password requests.
    Accepts email, checks if it exists, generates OTP, and sends HTML email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email'].strip().lower()

            # Check if user exists in Database
            user_exists = User.objects.filter(email__iexact=email).exists()
            if not user_exists:
                # Check supabase table
                try:
                    res = supabase.table('api_user').select('email').eq('email', email).execute()
                    if res.data:
                        user_exists = True
                except Exception:
                    pass

            if not user_exists:
                return Response(
                    {"error": "User does not exist. Please create an account."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Generate 6-digit OTP
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            # Store OTP in cache for 5 minutes
            cache_key = f"forgot_otp_{email}"
            cache.set(cache_key, otp, timeout=300)
            cache.set(f"otp_{email}", otp, timeout=300)

            logger.debug(f"Password reset OTP generated for {email}: {otp}")

            plain_message = f"""
Hey 👋,

We received a request to reset your CADverse password.

Your verification code is: {otp}

⏰ This code expires in 5 minutes.

If you didn't request this, please ignore this email.

Stay safe,
The CADverse Team 🔒
            """.strip()

            html_message = render_to_string('emails/password_reset_otp.html', {
                'otp': otp,
                'email': email,
            })

            try:
                msg = EmailMultiAlternatives(
                    subject="CADverse - Password Reset Code 🔑",
                    body=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                msg.attach_alternative(html_message, "text/html")
                msg.send()

                logger.info(f"Password reset OTP email sent to {email}")
            except Exception as e:
                logger.error(f"Failed to send password reset email to {email}: {str(e)}")
                return Response(
                    {"error": "Failed to send OTP email. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                {"message": "Password reset code sent to your email."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyPasswordResetOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email'].strip().lower()
            otp_input = str(serializer.validated_data['otp']).strip()

            cache_key = f"forgot_otp_{email}"
            cached_otp = cache.get(cache_key) or cache.get(f"otp_{email}")

            if cached_otp is None:
                return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

            if str(cached_otp) != otp_input:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            # Generate reset token
            reset_token = str(uuid4())
            reset_token_key = f"reset_token_{email}"
            cache.set(reset_token_key, reset_token, timeout=300)

            return Response({
                'message': 'OTP verified successfully',
                'reset_token': reset_token
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPViewForget(VerifyPasswordResetOTPView):
    pass


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email'].strip().lower()
            reset_token_input = serializer.validated_data['reset_token']
            new_password = serializer.validated_data['new_password']

            cache_key = f"reset_token_{email}"
            stored_token = cache.get(cache_key)

            if not stored_token:
                return Response(
                    {"error": "Reset token has expired or does not exist."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if stored_token != reset_token_input:
                return Response(
                    {"error": "Invalid reset token."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(email__iexact=email)
                old_password_hashed = user.password
                user.set_password(new_password)
                user.save()

                try:
                    supabase.table('api_user').update({
                        'password': user.password
                    }).eq('email', email).execute()
                except Exception as ex:
                    logger.warning(f"Could not update password in Supabase: {ex}")

                PasswordChangeHistory.objects.create(
                    user=user,
                    old_password_hashed=old_password_hashed,
                    new_password_hashed=user.password,
                )

                cache.delete(cache_key)
                cache.delete(f"forgot_otp_{email}")
                cache.delete(f"otp_{email}")

                return Response(
                    {"message": "Password reset successfully."},
                    status=status.HTTP_200_OK
                )

            except User.DoesNotExist:
                return Response(
                    {"error": "User does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {"error": f"Error resetting password: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# MESSAGING & UPLOAD VIEWS
# ==========================================

class SendMessageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        subject = request.data.get('subject')
        message = request.data.get('message')
        if not subject or not message:
            return Response({'error': 'Subject and message are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['cadverse.a@gmail.com'],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Error sending contact message: {e}")
        return Response({'message': 'Message sent successfully'}, status=status.HTTP_200_OK)


class UploadFileView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logger.debug(f"Request data: {request.data}")
        logger.debug(f"Request files: {request.FILES}")

        try:
            file = request.FILES.get('file')
            if not file:
                return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

            selected_service = request.data.get('selected_service')
            if not selected_service:
                return Response({"error": "selected_service is required"}, status=status.HTTP_400_BAD_REQUEST)

            valid_services = ["3D Model Design", "3D Printing", "Simulation", "Other"]
            if selected_service not in valid_services:
                return Response({"error": f"Invalid service. Choose one of: {', '.join(valid_services)}"}, status=status.HTTP_400_BAD_REQUEST)

            service_description = request.data.get('service_description', '').strip()
            if selected_service == "Other" and not service_description:
                return Response({"error": "service_description is required when selected_service is 'Other'"}, status=status.HTTP_400_BAD_REQUEST)

            project_description = request.data.get('project_description', '').strip()
            user_email = request.user.email
            if not user_email:
                return Response({"error": "User email not found"}, status=status.HTTP_400_BAD_REQUEST)

            supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            unique_id = str(uuid.uuid4())

            # 1. Upload main file
            main_file_name = f"{user_email}/{unique_id}_{file.name}"
            response = supabase_client.storage.from_(settings.SUPABASE_BUCKET).upload(
                path=main_file_name,
                file=file.read(),
                file_options={"content-type": file.content_type}
            )
            if hasattr(response, 'error') and response.error:
                logger.error(f"Main file upload failed: {response.error}")
                return Response({"error": "Failed to upload main file"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            main_file_url = supabase_client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(main_file_name)
            uploaded_files = [{"file_path": main_file_name, "file_url": main_file_url, "file_name": file.name}]

            # 2. Upload project description txt if provided
            if project_description:
                txt_content = f"Project Description:\n{project_description}"
                txt_file = BytesIO(txt_content.encode('utf-8'))
                txt_file_name = f"{user_email}/{unique_id}_project_description.txt"

                supabase_client.storage.from_(settings.SUPABASE_BUCKET).upload(
                    path=txt_file_name,
                    file=txt_file.read(),
                    file_options={"content-type": "text/plain"}
                )
                description_file_url = supabase_client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(txt_file_name)
                uploaded_files.append({
                    "file_path": txt_file_name,
                    "file_url": description_file_url,
                    "file_name": "project_description.txt"
                })

            # 3. If Other -> upload service description
            if selected_service == "Other":
                other_txt_content = f"Service: Other\nCustom Description:\n{service_description}"
                other_txt_file = BytesIO(other_txt_content.encode('utf-8'))
                other_txt_file_name = f"{user_email}/{unique_id}_service_other_description.txt"

                supabase_client.storage.from_(settings.SUPABASE_BUCKET).upload(
                    path=other_txt_file_name,
                    file=other_txt_file.read(),
                    file_options={"content-type": "text/plain"}
                )
                service_file_url = supabase_client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(other_txt_file_name)
                uploaded_files.append({
                    "file_path": other_txt_file_name,
                    "file_url": service_file_url,
                    "file_name": "service_other_description.txt"
                })

            # Create or update project
            project_id = request.data.get('project_id')
            project_name = request.data.get('project_name') or f"Project_{unique_id[:8]}"

            if project_id:
                project = get_object_or_404(Project, id=project_id, user=request.user)
            else:
                project = Project.objects.create(
                    user=request.user,
                    name=project_name,
                    description=project_description or service_description,
                    type=selected_service,
                    status='Submitted'
                )

            for uf in uploaded_files:
                ProjectFile.objects.create(
                    project=project,
                    file_url=uf['file_url'],
                    file_name=uf['file_name']
                )

            return Response({
                "message": "File(s) uploaded successfully",
                "project_id": project.id,
                "files": uploaded_files
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Upload error:")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# PROJECTS & USER ENDPOINTS
# ==========================================

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_projects(request):
    projects = Project.objects.filter(user=request.user).order_by('-id')
    data = []
    for p in projects:
        data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "type": p.type,
            "submittedDate": p.created_at.isoformat() if p.created_at else None
        })
    return Response(data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def project_detail(request, project_id=None, projectId=None):
    pid = project_id or projectId
    project = get_object_or_404(Project, id=pid, user=request.user)
    data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "type": project.type,
        "submittedDate": project.created_at.isoformat() if project.created_at else None
    }
    return Response(data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def protected_view(request):
    user = request.user
    user_data = {
        "id": user.id,
        "name": user.name or user.email,
        "email": user.email,
        "mobile": getattr(user, "mobile", ""),
        "is_verified": getattr(user, "is_verified", True),
    }
    return Response({"user": user_data}, status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})


def project_status_stream(request):
    def event_stream():
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("LISTEN project_status_updates;")

        last_heartbeat = time.time()
        heartbeat_interval = 15

        try:
            while True:
                conn.poll()
                now_time = time.time()

                if now_time - last_heartbeat >= heartbeat_interval:
                    yield ": heartbeat\n\n"
                    last_heartbeat = now_time

                while conn.notifies:
                    notify = conn.notifies.pop(0)
                    yield f"data: {notify.payload}\n\n"
                    last_heartbeat = now_time

                time.sleep(0.1)
        finally:
            cur.close()
            conn.close()

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    return response


# ==========================================
# FEEDBACK & SHOWCASE VIEWS
# ==========================================

class SubmitFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = {
            'project': request.data.get('project'),
            'rating': request.data.get('rating'),
            'feedback_text': request.data.get('feedback_text'),
            'emojis': request.data.get('emojis'),
        }
        serializer = UserFeedbackCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "Feedback submitted successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedbackListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        feedbacks = UserFeedback.objects.select_related('user', 'project').filter(is_approved=True)
        serializer = UserFeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)


class FeedbackDetailListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        feedback_details = FeedbackDetail.objects.all()
        serializer = FeedbackDetailSerializer(feedback_details, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def user_feedback_list(request):
    feedbacks = UserFeedback.objects.filter(user=request.user).order_by('-created_at')
    serializer = UserFeedbackSerializer(feedbacks, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def increment_feedback_popup(request, feedback_id):
    feedback = get_object_or_404(UserFeedback, id=feedback_id, user=request.user)

    if feedback.status != 'approved':
        return Response({"error": "Only approved feedback can have popups expanded"}, status=status.HTTP_400_BAD_REQUEST)

    if feedback.popup_count >= 3:
        return Response({"error": "Maximum popup expansions reached (3)"}, status=status.HTTP_400_BAD_REQUEST)

    feedback.popup_count += 1
    feedback.save()

    return Response({
        "message": "Popup count incremented",
        "new_count": feedback.popup_count
    }, status=status.HTTP_200_OK)


class GetProjectTitleView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, feedback_id):
        try:
            feedback = UserFeedback.objects.get(id=feedback_id, is_approved=True)
            project_title = feedback.project.name
            return Response({
                'title': project_title,
                'project_id': feedback.project.id,
                'user_name': feedback.user.name or feedback.user.email
            }, status=status.HTTP_200_OK)
        except UserFeedback.DoesNotExist:
            return Response({'error': 'Feedback not found or not approved'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ShowcaseListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        items = ShowcaseItem.objects.select_related('feedback__user').all().order_by('-created_at')
        serializer = ShowcaseItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)


class FeedbackStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        feedbacks = UserFeedback.objects.filter(is_approved=True)
        total = feedbacks.count()
        avg = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
        five_star = feedbacks.filter(rating=5).count()
        satisfaction = round((five_star / total * 100), 2) if total > 0 else 100

        return Response({
            'total_reviews': total,
            'average_rating': round(avg, 1),
            'satisfaction_rate': satisfaction,
            'showcase': ShowcaseItemSerializer(ShowcaseItem.objects.all()[:4], many=True, context={'request': request}).data
        })


# ==========================================
# EMPLOYEE PERMISSIONS VIEW
# ==========================================

class EmployeePermissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_superuser:
            full_models = ["user", "userfeedback", "project", "projectfile", "emaillog", "apiuser", "notification", "showcaseitem"]
            return Response({
                "is_superuser": True,
                "is_staff": True,
                "visible_panels": [m.capitalize() for m in full_models],
                "permissions": {
                    model: ["view", "add", "change", "delete"]
                    for model in full_models
                }
            })

        if not user.is_staff:
            return Response({
                "is_superuser": False,
                "is_staff": False,
                "visible_panels": [],
                "permissions": {}
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            profile = user.employee_profile
            visible_cts = profile.visible_models.all()
            visible_panels = [ct.model for ct in visible_cts]
        except AttributeError:
            visible_panels = []

        target_models = ['user', 'userfeedback', 'project', 'projectfile', 'emaillog', 'apiuser', 'notification', 'showcaseitem']
        permissions = {}
        user_perm_codenames = user.get_all_permissions()

        for model in target_models:
            if model in visible_panels:
                model_perms = []
                for action_name in ['view', 'add', 'change', 'delete']:
                    full_perm_name = f"api.{action_name}_{model}"
                    if full_perm_name in user_perm_codenames:
                        model_perms.append(action_name)
                permissions[model] = model_perms
            else:
                permissions[model] = []

        return Response({
            "is_superuser": False,
            "is_staff": True,
            "visible_panels": [m.capitalize() for m in visible_panels],
            "permissions": permissions
        })