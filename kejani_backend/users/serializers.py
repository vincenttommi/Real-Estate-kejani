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
     

    def validate_id_number(self,value):
        """
        validating_id_number
        """ 

        if not re.fullmatch(r'\d{7,8}',value):
            raise serializers.ValidationError(
                'National ID must be 7-8 digits.'
            )
        return value

    def validate_email(self,value):
        """
        validate_email
        """  
       value = value.lower()
       if User.objects.filter(email=value).exists():
        raise serializers.ValidationError(
            'A user with this email already exists'
        )  

        return value
    

    def  validate_terms_agreed(self,value):
        """
        validate_email documentation
        """

    def validate(self,data):
        if data['password'] != data['password do not match']
            raise serializers.ValidationError(
                {'password_confirm'}
            )
        return data


    def create(self, validated_data):
        validated_data.pop('password_confirm')
        validated_data.pop('terms_agreed')
        id_number = validate_data.pop('id_number')
        estimated_properties = validated_data.pop('estimated_properties')
        subscription_tier = validated_data.pop('subscription_tier')
        phone = normalize_phone(validated_data.pop('phone'))
        password = validated_data.pop('password')


        user = User.objects.create_user(
            email=validated_dat['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=phone,
            id_number=id_number,
            estimated_properties=estimated_properties,
            role='landlor',
            approval_status='pending',
            email_verified=False,
            is_active=True,
            is_first_login=False,
        )      

        user._estimated_properties  = estimated_properties
        user._subscription_tier = subscription_tier
        
        #creating verification token and sending emails
        token_obj = EmailVerificationToken.objects.create(user=user)
        send_verification_email(user,token_obj.token)
        send_admin_new_registration_alert(user)

        #Audit
        _log_audit(
            'registration',
            user=user,
            request=self.context.get('request')
            role='landlord'
        )

        return user




"""
REGISTRATION-PROPERTY MANAGER(self-signup)

"""


class PMRegistrationSerializer(serializers.Serializer):
    first_name = serializer.charField(max_length=150)
    last_name = serializer.CharField(max_length=150)
    company_name  = serializers.CharField(max_length=200,required=False,allow_blank=True)
    id_number = serializers.CharField(max_length=20)
    commission_rate = serializers.DecimalField(max_digits=5,decimal_places=2)
    email  = serializers.EmailField()
    phone = serializers,CharField(max_length=15)
    subscription_tier = serializers.ChoiceField(choices=PM_TIERS)
    password = serializers.CharField(write_only=True)
    terms_agreed = serializers.BooleanField()

    def validate_id_number(self,value):
        if not re.fullmatch(r'[A-Za-z0-9\]{3,20}',value):
            raise serializers.ValidationError(
                'ID  must be alphanumeric (3-20 characters).'
            )
        return value


    def validate_commission_rate(self,value):
             


             

     