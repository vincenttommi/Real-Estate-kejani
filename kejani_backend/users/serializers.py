import logging
import quopri
import re
import secrets
import string
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import (
    send_admin_new_registration_alert,
    send_temp_credentials_email,
    send_verification_email,
    send_approval_email,
)

from .models import (
    AccessAuditLog,
    EmailVerificationToken,
    PMInvitation,
    PasswordResetToken,
    TenantInvitation,
)

logger = logging.getLogger(__name__)

User = get_user_model()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_phone(phone: str) -> str:
    """
    Normalize a Kenyan phone number to E.164 format.

    Examples:
        0712345678 -> +254712345678
        254712345678 -> +254712345678
        +254712345678 -> +254712345678
    """
    if not phone:
        return phone

    phone = phone.strip().replace(" ", "").replace("-", "")

    if phone.startswith("0") and len(phone) == 10:
        phone = "+254" + phone[1:]

    elif phone.startswith("254") and not phone.startswith("+"):
        phone = "+" + phone

    return phone


def generate_random_password(length=12):
    """
    Generate a secure random password.
    """
    chars = string.ascii_letters + string.digits + "!@#$%"

    return "".join(
        secrets.choice(chars)
        for _ in range(length)
    )


def get_client_ip(request):
    """
    Extract the client's IP address from the request.
    """
    if not request:
        return None

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def log_audit(event, user=None, request=None, **details):
    """
    Create an AccessAuditLog entry.
    """

    ip_address = get_client_ip(request)

    AccessAuditLog.objects.create(
        event=event,
        user=user,
        ip_address=ip_address,
        role=getattr(user, "role", ""),
        details=details,
    )


# ============================================================
# USER PROFILE
# ============================================================

class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            "uuid",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "role",
            "email_verified",
            "approval_status",
            "is_first_login",
            "is_demo",
            "created_at",
        ]

        read_only_fields = [
            "uuid",
            "email",
            "role",
            "email_verified",
            "approval_status",
            "is_first_login",
            "is_demo",
            "created_at",
        ]


# ============================================================
# LANDLORD REGISTRATION
# ============================================================

class LandlordRegistrationSerializer(serializers.Serializer):

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    id_number = serializers.CharField(max_length=20)

    estimated_properties = serializers.ChoiceField(
        choices=ESTIMATED_PROPERTIES_CHOICES
    )

    email = serializers.EmailField()

    phone = serializers.CharField(max_length=15)

    subscription_tier = serializers.ChoiceField(
        choices=LANDLORD_TIERS
    )

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True
    )

    terms_agreed = serializers.BooleanField()

    # --------------------------------------------------------
    # VALIDATIONS
    # --------------------------------------------------------

    def validate_id_number(self, value):

        if not re.fullmatch(r"\d{7,8}", value):
            raise serializers.ValidationError(
                "National ID must be 7-8 digits."
            )

        return value

    def validate_email(self, value):

        value = value.lower()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate_terms_agreed(self, value):

        if not value:
            raise serializers.ValidationError(
                "You must agree to the terms and conditions."
            )

        return value

    def validate(self, data):

        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm":
                    "Passwords do not match."
                }
            )

        return data

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    def create(self, validated_data):

        validated_data.pop("password_confirm")
        validated_data.pop("terms_agreed")

        id_number = validated_data.pop("id_number")

        estimated_properties = validated_data.pop(
            "estimated_properties"
        )

        subscription_tier = validated_data.pop(
            "subscription_tier"
        )

        phone = normalize_phone(
            validated_data.pop("phone")
        )

        password = validated_data.pop("password")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone=phone,
            id_number=id_number,
            estimated_properties=estimated_properties,
            role="landlord",
            approval_status="pending",
            email_verified=False,
            is_active=True,
            is_first_login=False,
        )

        user.subscription_tier = subscription_tier
        user.save(update_fields=["subscription_tier"])

        # Email verification
        token_obj = EmailVerificationToken.objects.create(
            user=user
        )

        send_verification_email(
            user,
            token_obj.token
        )

        send_admin_new_registration_alert(user)

        # Audit
        log_audit(
            "registration",
            user=user,
            request=self.context.get("request"),
            role="landlord",
        )

        return user


# ============================================================
# PROPERTY MANAGER REGISTRATION
# ============================================================

class PMRegistrationSerializer(serializers.Serializer):

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    company_name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
    )

    id_number = serializers.CharField(max_length=20)

    commission_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    email = serializers.EmailField()

    phone = serializers.CharField(max_length=15)

    subscription_tier = serializers.ChoiceField(
        choices=PM_TIERS
    )

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True
    )

    terms_agreed = serializers.BooleanField()

    # --------------------------------------------------------
    # VALIDATIONS
    # --------------------------------------------------------

    def validate_id_number(self, value):

        if not re.fullmatch(r"[A-Za-z0-9]{3,20}", value):
            raise serializers.ValidationError(
                "ID must be alphanumeric (3-20 characters)."
            )

        return value

    def validate_commission_rate(self, value):

        if not (10 <= value <= 20):
            raise serializers.ValidationError(
                "Commission rate must be between 10% and 20%."
            )

        return value

    def validate_email(self, value):

        value = value.lower()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate_terms_agreed(self, value):

        if not value:
            raise serializers.ValidationError(
                "You must agree to the terms."
            )

        return value

    def validate(self, data):

        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm":
                    "Passwords do not match."
                }
            )

        return data

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    def create(self, validated_data):

        validated_data.pop("password_confirm")
        validated_data.pop("terms_agreed")

        id_number = validated_data.pop("id_number")

        commission_rate = validated_data.pop(
            "commission_rate"
        )

        subscription_tier = validated_data.pop(
            "subscription_tier"
        )

        company_name = validated_data.pop(
            "company_name",
            "",
        )

        phone = normalize_phone(
            validated_data.pop("phone")
        )

        password = validated_data.pop("password")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone=phone,
            id_number=id_number,
            role="property_manager",
            approval_status="pending",
            email_verified=False,
            is_active=True,
            is_first_login=False,
        )

        user.company_name = company_name
        user.commission_rate = commission_rate
        user.subscription_tier = subscription_tier

        user.save(
            update_fields=[
                "company_name",
                "commission_rate",
                "subscription_tier",
            ]
        )

        # Email verification
        token_obj = EmailVerificationToken.objects.create(
            user=user
        )

        send_verification_email(
            user,
            token_obj.token
        )

        send_admin_new_registration_alert(user)

        log_audit(
            "registration",
            user=user,
            request=self.context.get("request"),
            role="property_manager",
        )

        return user


# ============================================================
# INVITED PROPERTY MANAGER REGISTRATION
# ============================================================

class InvitedPMRegistrationSerializer(serializers.Serializer):

    invite_token = serializers.UUIDField()

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    company_name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
    )

    id_number = serializers.CharField(max_length=20)

    commission_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    email = serializers.EmailField()

    phone = serializers.CharField(max_length=15)

    subscription_tier = serializers.ChoiceField(
        choices=PM_TIERS
    )

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True
    )

    terms_agreed = serializers.BooleanField()

    # --------------------------------------------------------
    # VALIDATIONS
    # --------------------------------------------------------

    def validate_invite_token(self, value):

        try:
            invitation = PMInvitation.objects.get(
                invite_token=value
            )

        except PMInvitation.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid invitation token."
            )

        if not invitation.is_valid():
            raise serializers.ValidationError(
                "This invitation has expired or been used."
            )

        self._invitation = invitation

        return value

    def validate_id_number(self, value):

        if not re.fullmatch(
            r"[A-Za-z0-9]{3,20}",
            value,
        ):
            raise serializers.ValidationError(
                "ID must be alphanumeric (3-20 characters)."
            )

        return value

    def validate_commission_rate(self, value):

        if not (10 <= value <= 20):
            raise serializers.ValidationError(
                "Commission rate must be between 10% and 20%."
            )

        return value

    def validate_email(self, value):

        value = value.lower()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate_terms_agreed(self, value):

        if not value:
            raise serializers.ValidationError(
                "You must agree to the terms."
            )

        return value

    def validate(self, data):

        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm":
                    "Passwords do not match."
                }
            )

        invitation = getattr(
            self,
            "_invitation",
            None,
        )

        if invitation:

            invited_email = (
                invitation.invited_email
                .strip()
                .lower()
            )

            if data["email"].strip().lower() != invited_email:
                raise serializers.ValidationError(
                    {
                        "email":
                        "This email does not match the invitation."
                    }
                )

        return data

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    def create(self, validated_data):

        with transaction.atomic():

            invite_token = validated_data["invite_token"]

            try:
                invitation = (
                    PMInvitation.objects
                    .select_for_update()
                    .get(invite_token=invite_token)
                )

            except PMInvitation.DoesNotExist:
                raise serializers.ValidationError(
                    "This invitation has expired or been used."
                )

            if not invitation.is_valid():
                raise serializers.ValidationError(
                    "This invitation has expired or been used."
                )

            validated_data.pop("invite_token")
            validated_data.pop("password_confirm")
            validated_data.pop("terms_agreed")

            id_number = validated_data.pop("id_number")

            commission_rate = validated_data.pop(
                "commission_rate"
            )

            subscription_tier = validated_data.pop(
                "subscription_tier"
            )

            company_name = validated_data.pop(
                "company_name",
                "",
            )

            phone = normalize_phone(
                validated_data.pop("phone")
            )

            password = validated_data.pop("password")

            user = User.objects.create_user(
                email=validated_data["email"],
                password=password,
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                phone=phone,
                id_number=id_number,
                role="property_manager",
                approval_status="pending",
                email_verified=False,
                is_active=True,
                is_first_login=False,
            )

            user.company_name = company_name
            user.commission_rate = commission_rate
            user.subscription_tier = subscription_tier

            user.save(
                update_fields=[
                    "company_name",
                    "commission_rate",
                    "subscription_tier",
                ]
            )

            invitation.accepted_by = user
            invitation.status = "accepted"

            invitation.save(
                update_fields=[
                    "accepted_by",
                    "status",
                ]
            )

            token_obj = EmailVerificationToken.objects.create(
                user=user
            )

            send_verification_email(
                user,
                token_obj.token,
            )

            send_admin_new_registration_alert(user)

            log_audit(
                "registration",
                user=user,
                request=self.context.get("request"),
                role="property_manager",
            )

            log_audit(
                "invitation_accepted",
                user=user,
                request=self.context.get("request"),
                role="property_manager",
                invited_by=invitation.invited_by.email,
            )

            return user


# ============================================================
# INVITED TENANT REGISTRATION
# ============================================================

class InvitedTenantRegistrationSerializer(serializers.Serializer):

    invite_token = serializers.UUIDField()

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    id_number = serializers.CharField(max_length=8)

    email = serializers.EmailField()

    phone = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
    )

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True
    )

    # --------------------------------------------------------
    # VALIDATIONS
    # --------------------------------------------------------

    def validate_invite_token(self, value):

        try:
            invitation = TenantInvitation.objects.get(
                invite_token=value
            )

        except TenantInvitation.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid invitation token."
            )

        if not invitation.is_valid():
            raise serializers.ValidationError(
                "This invitation has expired or been used."
            )

        self._invitation = invitation

        return value

    def validate_id_number(self, value):

        if not re.fullmatch(r"\d{7,8}", value):
            raise serializers.ValidationError(
                "National ID must be 7-8 digits."
            )

        return value

    def validate_email(self, value):

        value = value.lower()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate(self, data):

        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm":
                    "Passwords do not match."
                }
            )

        invitation = getattr(
            self,
            "_invitation",
            None,
        )

        if invitation:

            invited_email = (
                invitation.invited_email
                .strip()
                .lower()
            )

            if data["email"].strip().lower() != invited_email:
                raise serializers.ValidationError(
                    {
                        "email":
                        "This email does not match the invitation."
                    }
                )

        return data

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    def create(self, validated_data):

        with transaction.atomic():

            invite_token = validated_data["invite_token"]

            try:
                invitation = (
                    TenantInvitation.objects
                    .select_for_update()
                    .get(invite_token=invite_token)
                )

            except TenantInvitation.DoesNotExist:
                raise serializers.ValidationError(
                    "Invalid invitation token."
                )

            if not invitation.is_valid():
                raise serializers.ValidationError(
                    "This invitation has expired or been used."
                )

            validated_data.pop("invite_token")
            validated_data.pop("password_confirm")

            id_number = validated_data.pop("id_number")

            phone = normalize_phone(
                validated_data.pop("phone", "")
            )

            password = validated_data.pop("password")

            user = User.objects.create_user(
                email=validated_data["email"],
                password=password,
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                phone=phone,
                id_number=id_number,
                role="tenant",
                approval_status="not_required",
                email_verified=True,
                is_active=True,
                is_first_login=False,
            )

            invitation.accepted_by = user
            invitation.status = "accepted"

            invitation.save(
                update_fields=[
                    "accepted_by",
                    "status",
                ]
            )

            log_audit(
                "registration",
                user=user,
                request=self.context.get("request"),
                role="tenant",
            )

            log_audit(
                "invitation_accepted",
                user=user,
                request=self.context.get("request"),
                invitation_id=invitation.pk,
            )

            return user


# ============================================================
# CREATE TENANT BY ADMIN / LANDLORD
# ============================================================

class CreateTenantSerializer(serializers.Serializer):

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    email = serializers.EmailField()

    phone = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
    )

    id_number = serializers.CharField(max_length=8)

    # --------------------------------------------------------
    # VALIDATIONS
    # --------------------------------------------------------

    def validate_id_number(self, value):

        if not re.fullmatch(r"\d{7,8}", value):
            raise serializers.ValidationError(
                "National ID must be 7-8 digits."
            )

        return value

    def validate_email(self, value):

        value = value.lower()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    def create(self, validated_data):

        id_number = validated_data.pop("id_number")

        phone = normalize_phone(
            validated_data.pop("phone", "")
        )

        temp_password = generate_random_password()

        user = User.objects.create_user(
            email=validated_data["email"],
            password=temp_password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone=phone,
            id_number=id_number,
            role="tenant",
            approval_status="not_required",
            email_verified=True,
            is_active=True,
            is_first_login=True,
        )

        # Send temporary credentials
        send_temp_credentials_email(
            user,
            temp_password,
        )

        request = self.context.get("request")

        creator = (
            request.user
            if request and request.user.is_authenticated
            else None
        )

        log_audit(
            "registration",
            user=user,
            request=request,
            role="tenant",
            created_by=(
                creator.email
                if creator
                else None
            ),
        )

        return user


# ============================================================
# CUSTOM LOGIN
# ============================================================

class CustomTokenObtainSerializer(
    TokenObtainPairSerializer
):

    remember_me = serializers.BooleanField(
        default=False,
        required=False,
    )

    def validate(self, attrs):

        remember_me = attrs.pop(
            "remember_me",
            False,
        )

        email = attrs.get(
            self.username_field,
            "",
        ).lower()

        attrs[self.username_field] = email

        request = self.context.get("request")

        try:

            data = super().validate(attrs)

        except Exception:

            log_audit(
                "login_failed",
                request=request,
                email=email,
                reason="invalid_credentials",
            )

            raise

        user = self.user

        # ----------------------------------------------------
        # ROLE BASED LOGIN CHECKS
        # ----------------------------------------------------

        if user.role in (
            "landlord",
            "property_manager",
        ):

            if not user.email_verified:
                raise serializers.ValidationError(
                    "Please verify your email before logging in."
                )

            if user.approval_status == "pending":
                raise serializers.ValidationError(
                    "Your account is pending admin approval."
                )

            if user.approval_status == "rejected":
                raise serializers.ValidationError(
                    "Your account registration was not approved."
                )

            if user.approval_status == "suspended":
                raise serializers.ValidationError(
                    "Your account has been suspended. "
                    "Contact support."
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    "Account not active."
                )

        # ----------------------------------------------------
        # REMEMBER ME
        # ----------------------------------------------------

        if not remember_me:

            refresh = RefreshToken.for_user(user)

            refresh.set_exp(
                lifetime=timedelta(days=1)
            )

            data["refresh"] = str(refresh)
            data["access"] = str(
                refresh.access_token
            )

        # ----------------------------------------------------
        # CAPTURE LOGIN IP
        # ----------------------------------------------------

        ip = get_client_ip(request)

        if ip:

            user.last_login_ip = ip

            user.save(
                update_fields=["last_login_ip"]
            )

        # ----------------------------------------------------
        # USER RESPONSE
        # ----------------------------------------------------

        data["user"] = {
            "uuid": str(user.uuid),
            "email": user.email,
            "full_name": user.get_full_name(),
            "role": user.role,
            "email_verified": user.email_verified,
            "approval_status": user.approval_status,
            "is_first_login": user.is_first_login,
            "is_demo": user.is_demo,
        }

        log_audit(
            "login_success",
            user=user,
            request=request,
        )

        return data


# ============================================================
# CHANGE PASSWORD
# ============================================================

class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField(
        write_only=True
    )

    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    new_password_confirm = serializers.CharField(
        write_only=True
    )

    def validate_old_password(self, value):

        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Current password is incorrect."
            )

        return value

    def validate(self, data):

        if (
            data["new_password"]
            != data["new_password_confirm"]
        ):
            raise serializers.ValidationError(
                {
                    "new_password_confirm":
                    "Passwords do not match."
                }
            )

        return data

    def save(self, **kwargs):

        user = self.context["request"].user

        user.set_password(
            self.validated_data["new_password"]
        )

        user.is_first_login = False

        user.save(
            update_fields=[
                "password",
                "is_first_login",
                "updated_at",
            ]
        )

        log_audit(
            "password_changed",
            user=user,
            request=self.context.get("request"),
        )

        return user


# ============================================================
# PASSWORD RESET REQUEST
# ============================================================

class PasswordResetSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def save(self, **kwargs):

        email = self.validated_data["email"].lower()

        request = self.context.get("request")

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            # Do not reveal whether the email exists
            log_audit(
                "password_reset_requested",
                request=request,
                email=email,
                found=False,
            )

            return None

        # Invalidate existing tokens
        PasswordResetToken.objects.filter(
            user=user,
            is_used=False,
        ).update(
            is_used=True
        )

        token_obj = PasswordResetToken.objects.create(
            user=user,
            expires_at=(
                timezone.now()
                + timedelta(hours=1)
            ),
        )

        from .emails import send_password_reset_email

        send_password_reset_email(
            user,
            token_obj.token,
        )

        log_audit(
            "password_reset_requested",
            user=user,
            request=request,
            found=True,
        )

        return token_obj


# ============================================================
# PASSWORD RESET CONFIRM
# ============================================================

class PasswordResetConfirmSerializer(serializers.Serializer):

    token = serializers.CharField()

    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    new_password_confirm = serializers.CharField(
        write_only=True
    )

    def validate_token(self, value):

        clean_token = (
            quopri.decodestring(
                value.encode("utf-8")
            )
            .decode("utf-8")
        )

        try:

            uuid_obj = uuid.UUID(clean_token)

            token_obj = (
                PasswordResetToken.objects
                .select_related("user")
                .get(token=uuid_obj)
            )

        except PasswordResetToken.DoesNotExist:

            raise serializers.ValidationError(
                "Invalid reset token."
            )

        except ValueError:

            raise serializers.ValidationError(
                "Invalid reset token format."
            ) from None

        if not token_obj.is_valid():

            raise serializers.ValidationError(
                "This reset link has expired or already been used."
            )

        self.token_obj = token_obj

        return clean_token

    def validate(self, data):

        if (
            data["new_password"]
            != data["new_password_confirm"]
        ):
            raise serializers.ValidationError(
                {
                    "new_password_confirm":
                    "Passwords do not match."
                }
            )

        return data

    def save(self, **kwargs):

        with transaction.atomic():

            token_obj = (
                PasswordResetToken.objects
                .select_for_update()
                .select_related("user")
                .get(
                    pk=self.token_obj.pk
                )
            )

            if not token_obj.is_valid():

                raise serializers.ValidationError(
                    "This reset link has expired or already been used."
                )

            user = token_obj.user

            user.set_password(
                self.validated_data["new_password"]
            )

            user.save(
                update_fields=[
                    "password",
                    "updated_at",
                ]
            )

            token_obj.is_used = True

            token_obj.save(
                update_fields=["is_used"]
            )

            log_audit(
                "password_reset_completed",
                user=user,
                request=self.context.get("request"),
            )

            return user


# ============================================================
# PM INVITATION
# ============================================================

class PMInvitationCreateSerializer(serializers.Serializer):

    name = serializers.CharField(
        max_length=200
    )

    email = serializers.EmailField()

    phone = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
    )

    commission_rate = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
    )

    property_id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    def validate_email(self, value):

        value = value.lower()

        if User.objects.filter(
            email=value
        ).exists():

            raise serializers.ValidationError(
                "This PM already has an account. "
                "Ask them to log in and accept the assignment."
            )

        return value

    def validate_commission_rate(self, value):

        if not (10 <= value <= 20):

            raise serializers.ValidationError(
                "Commission rate must be between 10% and 20%."
            )

        return value

    def create(self, validated_data):

        from .emails import (
            send_pm_invitation_email
        )

        landlord = self.context["request"].user

        invitation = PMInvitation.objects.create(
            invited_by=landlord,
            invited_email=validated_data["email"],
            invited_phone=normalize_phone(
                validated_data.get("phone", "")
            ),
            commission_rate=validated_data[
                "commission_rate"
            ],
            property_id=validated_data.get(
                "property_id"
            ),
            expires_at=(
                timezone.now()
                + timedelta(days=7)
            ),
        )

        send_pm_invitation_email(
            invitation
        )

        log_audit(
            "invitation_sent",
            user=landlord,
            request=self.context.get("request"),
            invited_email=invitation.invited_email,
            type="pm",
        )

        return invitation


# ============================================================
# TENANT INVITATION
# ============================================================

class TenantInvitationCreateSerializer(
    serializers.Serializer
):

    email = serializers.EmailField()

    name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
    )

    phone = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
    )

    unit_id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    property_name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
    )

    def validate_email(self, value):

        return value.lower()

    def create(self, validated_data):

        from .emails import (
            send_tenant_invitation_email
        )

        inviter = self.context["request"].user

        invitation = TenantInvitation.objects.create(
            invited_by=inviter,
            invited_email=validated_data["email"],
            invited_name=validated_data.get(
                "name",
                "",
            ),
            invited_phone=normalize_phone(
                validated_data.get(
                    "phone",
                    "",
                )
            ),
            unit_id=validated_data.get(
                "unit_id"
            ),
            property_name=validated_data.get(
                "property_name",
                "",
            ),
            expires_at=(
                timezone.now()
                + timedelta(days=7)
            ),
        )

        send_tenant_invitation_email(
            invitation
        )

        log_audit(
            "invitation_sent",
            user=inviter,
            request=self.context.get("request"),
            invited_email=invitation.invited_email,
            type="tenant",
        )

        return invitation


# ============================================================
# ADMIN PENDING USERS
# ============================================================

class AdminPendingUsersSerializer(
    serializers.ModelSerializer
):

    full_name = serializers.CharField(
        source="get_full_name",
        read_only=True,
    )

    class Meta:

        model = User

        fields = [
            "uuid",
            "email",
            "full_name",
            "phone",
            "role",
            "email_verified",
            "approval_status",
            "created_at",
        ]

        