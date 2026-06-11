from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import VerificationProfile, Role, ProfileType, VerificationStatus

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, max_length=128)
    confirm_password = serializers.CharField(write_only=True, min_length=6, max_length=128)
    role = serializers.ChoiceField(choices=Role.choices, default=Role.DONOR)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'role', 'phone']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': '两次密码输入不一致'})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': '该邮箱已被注册'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email
        token['is_verified'] = user.is_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'role_display': self.user.get_role_display(),
            'phone': self.user.phone,
            'is_verified': self.user.is_verified,
        }
        return data


class UserInfoSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'role_display', 'phone', 'avatar', 'is_verified', 'date_joined']
        read_only_fields = ['id', 'username', 'email', 'role', 'date_joined']


class VerificationProfileSerializer(serializers.ModelSerializer):
    profile_type_display = serializers.CharField(source='get_profile_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = VerificationProfile
        fields = [
            'id', 'profile_type', 'profile_type_display', 'status', 'status_display',
            'real_name', 'id_card', 'personal_id_front', 'personal_id_back',
            'enterprise_license', 'enterprise_legal_person', 'reject_reason',
            'verified_at', 'submitted_at'
        ]
        read_only_fields = ['id', 'status', 'reject_reason', 'verified_at', 'submitted_at']

    def validate(self, attrs):
        profile_type = attrs.get('profile_type')
        if profile_type == ProfileType.PERSONAL:
            if not attrs.get('real_name'):
                raise serializers.ValidationError({'real_name': '真实姓名不能为空'})
            if not attrs.get('id_card'):
                raise serializers.ValidationError({'id_card': '身份证号不能为空'})
        elif profile_type == ProfileType.ENTERPRISE:
            if not attrs.get('real_name'):
                raise serializers.ValidationError({'real_name': '企业名称不能为空'})
            if not attrs.get('id_card'):
                raise serializers.ValidationError({'id_card': '统一社会信用代码不能为空'})
            if not attrs.get('enterprise_legal_person'):
                raise serializers.ValidationError({'enterprise_legal_person': '企业法人不能为空'})
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        if hasattr(user, 'verification_profile'):
            raise serializers.ValidationError('您已提交过实名认证，请等待审核或修改现有资料')
        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if instance.status == VerificationStatus.APPROVED:
            raise serializers.ValidationError('已通过的实名认证无法修改')
        validated_data['status'] = VerificationStatus.PENDING
        return super().update(instance, validated_data)


class VerificationAuditSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[('approved', '通过'), ('rejected', '拒绝')])
    reject_reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        if attrs.get('status') == 'rejected' and not attrs.get('reject_reason'):
            raise serializers.ValidationError({'reject_reason': '拒绝原因不能为空'})
        return attrs
