from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
import random

from .models import (
    User,
    TempUser,
    OTP,
    Project,
    ProjectFile,
    Notification,
    UserFeedback,
    FeedbackDetail,
    ShowcaseItem
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'mobile', 'is_verified']


class SignupSerializer(serializers.ModelSerializer):
    confirmPassword = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = TempUser
        fields = ['email', 'name', 'mobile', 'password', 'confirmPassword']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data.get('password') != data.get('confirmPassword'):
            raise serializers.ValidationError({'confirmPassword': 'Passwords do not match.'})
        return data

    def to_internal_value(self, data):
        email = data.get('email')
        if email:
            email = email.lower()
            TempUser.objects.filter(email__iexact=email).delete()
            data = data.copy()
            data['email'] = email
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        return super().to_internal_value(data)

    def create(self, validated_data):
        validated_data.pop('confirmPassword', None)
        validated_data['email'] = validated_data['email'].lower()
        raw_password = validated_data['password']
        validated_data['password'] = make_password(raw_password)
        validated_data['raw_password'] = raw_password
        validated_data['otp'] = str(random.randint(100000, 999999))
        temp_user = TempUser.objects.create(**validated_data)
        return temp_user


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password')
        if not user.is_verified:
            raise serializers.ValidationError('Email is not verified')
        data['user'] = user
        return data


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'status', 'type', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'subject', 'message', 'created_at', 'is_read']


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_token = serializers.CharField(required=True)
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class UserFeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    short_note = serializers.CharField(read_only=True)

    class Meta:
        model = UserFeedback
        fields = [
            'id', 'user', 'user_name', 'project', 'project_name', 'rating',
            'feedback_text', 'emojis', 'is_approved', 'status', 'short_note',
            'popup_count', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'project_name', 'created_at', 'is_approved', 'status', 'popup_count', 'short_note']

    def validate_rating(self, value):
        if value is not None and (value < 1 or value > 5):
            raise ValidationError("Rating must be between 1 and 5.")
        return value


class UserFeedbackCreateSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())

    class Meta:
        model = UserFeedback
        fields = ['project', 'rating', 'feedback_text', 'emojis']
        read_only_fields = ['user', 'created_at', 'is_approved', 'status', 'popup_count', 'short_note']

    def validate_rating(self, value):
        if value is not None and (value < 1 or value > 5):
            raise ValidationError("Rating must be between 1 and 5.")
        return value


class FeedbackDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_type = serializers.CharField(source='project.type', read_only=True)

    class Meta:
        model = FeedbackDetail
        fields = ['id', 'user', 'user_name', 'project', 'project_name', 'project_type', 'created_at']


class ShowcaseItemSerializer(serializers.ModelSerializer):
    before_file = serializers.URLField(source='before_url', read_only=True)
    after_file = serializers.URLField(source='after_url', read_only=True)

    class Meta:
        model = ShowcaseItem
        fields = ['id', 'title', 'before_file', 'after_file', 'feedback']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.feedback:
            data['feedback'] = {
                'user': {'name': instance.feedback.user.name if instance.feedback.user else ''},
                'feedback_text': instance.feedback.feedback_text,
                'rating': instance.feedback.rating or 5,
                'emojis': instance.feedback.emojis or "",
                'project_title': instance.title or (instance.feedback.project.name if instance.feedback.project else "CAD Project")
            }
        return data