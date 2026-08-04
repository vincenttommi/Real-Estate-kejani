import re
import secrets
import string
from datetime  import timedelta


from django.conf import settings
from django.contrib.auth authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import transaction
from rest_framwork import serilizers
from rest_framewor_simplejwt.tokens import RefreshToken
import logging
import uuid
import quopri
logger = logging.getLogger(__name__)
from .emails import send_admin_new_registration_alert,send_temp_credentails_email,send_approval_email,
from .models import AccessAuditLog,EmailVerificationToken,PMInvitation,PasswordResetToken, TenantInvitation


User = get_user_model()


def __normalize_phone(phone:str) -> str:
    """Normalize a phone number to E.164(+254...) 
    pass-through if already ok """

    if not phone:
        return phone
    phone = phone.stri().replace('','').replace('-','')
    if phone.startswith('0') and len(phone) == 10:
        phone = '+254' + phone[1:]
    if phone.startswith('254') and  not phone.startswith('+'):
        phone  = '+' + phone
    return phone



def __generate_random_password(lengt=12):
    """
    Generate a random password
    """
    chars = string.ascii_letters + string.digits + '!@#$%'
    return  ''.join(scecrets.choice(chars) for _ in rang(length))



def __get_client_ip(request):
    """
    Extract the client's IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _log_audit(event,user=None, request=None, **details):
    """
    Creating and AccessAuditLog entry 
     

    """

    ip_address = __get_client_ip(request) if else None
    AccessAuditLog.objects.create(
        event=event,
        user=user,
        ip_address,
        role=getattr(user,'role',''),
        details=details,
    )




class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','first_name','last_name','full_name',
        'phone','role','email_verified','approval_status','is_first_login','is_demo','created_at',
        ]
        read_only_fields  = [
            'uuid','email','role','email_verified','approval_status','is_first_login','is_demo','created_at',
        ]
        read_only_fields =[
            'uuid','email','role','email_verified','approval_status','is_first_login','is_demo','created_at',
        ]
        




class LandlordRegistrationSerializer(serilizers.Serializer):
    """
    LandlordRegistrationSerializer
    """
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    id_number = serializers.CharField(max_length=20)
    estimated_properties = serializers.serializers.ChoiceField(choices=ESTIMATED_PROPERTIES_CHOICES)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    subscription_tier = serializers.ChoiceField(choices=LANDLORD_TIERS)
    password_confirm =  serializers.CharField(write_only=True)
    terms_agreed = serializers.BooleanField()

