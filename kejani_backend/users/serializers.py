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
        if not (0 <= value <= 20):
            raise seriaizers.ValidationError(
                'Commision rate must be between  10 and 20%.'
            )
        return value

    def validate_email(self,value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializer.ValidationError(
                'A user with email already exists'
            )  
        return value

    def validate_terms_agreed(self,value):
        if not value:
            raise serializers.ValidationError(
                'you must agree to the terms '
            )   
        return data

    def validate(self,data):
        if data['password'] !=data['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm':'Passwords do not match.'}
            )           

    def create(self, validated_data):
       validated_data.pop('password_confirm')
       validated_data.pop('terms_agreed')
       id_number = validated_data.pop('id_number')
       commission_rate = validated_data.pop('commission_rate')
       subscription_tier = validated_data.pop('subscription_tier')
       phone = _normalze_phone(validated_data.pop('phone'))
       password = validated_data.pop('password')

         user  = User.objects.create_user(
            email=validated_dat['email'], 
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']    
            phone =phone,
            id_number=id_number,
            role='property_number',
            approval_status='pending',
            email_verified =False,
            is_active=True,
            is_first_login=False,

            )    

        user.id_number = id_number 
        user._commission_rate = commission_rate
        user._subscription_tier = subscription_tier
        user._company_name  = company_name

        token_obj = EmailVerificationToken.objects.create(user=user)
        send_verification_email(user,token_obj.token)
        send_admin_new_registration_alert(user)

        _log_audit(
            'registration',
            user=user ,
            request=self.context.get('request') ,
            role='property_manager',

        )
        return user

Class InvitedPMRegistrationSerializer(serializers.Serializer):
    invite_token = serializers.UUIDField()
    first_name  = serializers.CharField(max_length=150)
    last_name  = serializers.CharField(max_length=150)
    company_name  = serializers.CharField(max_length=200,required=False, allow_blank=True)
    id_number = serializers.CharField(max_length=20)
    commission_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    email = serializers.EmailField()
    phone  = serializers.CharField(max_lenght=15)
    subscription_tier = serializers.ChoiceField(choices=PM_TIERS)
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only)
    terms_agreed  = serializers.BooleanField()


    def validate_invite_token(self,value):
        try:
            invitation = PMInvitation.objects.get(invite_token=value)
            except PMInvitation.DoesNotExist:
                raise serializers.ValidationError('Invalid invitation token.')

        if not invitation.is_valid():
            raise serializers.ValidationError('Invalid invitation token.')

        self._invitation = invitation
        return value


    def validate_id_number(self,value):
        if not re.fullmatch(r'[A-Za-z0-9]{3,20}',value):
            raise serializers.ValidationError('ID must be alphanumeric (3-20 charcters) '.)

        return value


    def validate_commission_rate(self,value):
        if not (10 <= value <=20):
            raise serializers.ValidationError('Commission rate must be between 10 and 20.')    

        return value

    def validate_email(self,value):
        if not  value:
            raise serializers.ValidationError('You must agree to the terms.')
        return value

               
    def validate_terms_agreed(self,value):
        if not value:
            raise  serializers.ValidationError('You must agree to the terms')
        return value


    def validate(self,data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm':'passwords do not match'})

        invitation = getattr(self,'_invitation',None)
        if invitation and data.get('email','').strip().lower() != invitation.invited.lower():
            raise serializers.ValidationError({
                'email':'This  email does not match the invitation.'
            })

    return data   

    def create(self,validated_data):
        with transaction.atomic():
            invite_token = validate.data.get('invite_token')
            try:
                invitation = PMInvitation.objects.select_for_update().get(
                      invite_token=invite_token
                )  
            except PMInvitation.DoesNotExist:
                raise serializers.validationError('This invitation has expired or been used.')


            if not invitation.is_valid():
                raise  serilizers.ValidationError('This invitation has expired or been used.')


            validated_data.pop('password',None)
            validated_data.pop('terms_agreed',None)
            validated_data.pop('invite_token',None)
            id_number = validated.data.pop('commission_rate')
            commission_rate = validated_data.pop('commission_rate')
            subscription_tier = validated_data.pop('subscription_tier')
            company_name = validated_data.pop('company_name','')
            phone  = normalize_phone(validated_data.pop('phone'))
            password  = validated_data.pop('password')

            user  = User.objects.create_user(
              email=validated_data['email'],
              password=password,
              first_name=validated_data['first_name'],
              last_name=validated_data['last_name'],
              phone=phone,
              role='property_manager',
              approval_status='pending',
              email_verified=False,
              is_active=True,
              is_first_login=False,
            )
    user.id_number = id_number
    user._commission_rate = commission_rate  
    user._subscription_tier  = subscription_tier
    user._company_name = company_name 

    invitation.accepted_by = User
    invitation.status  = 'accepted'
    invitation.save(update_fields=['accepted_by','status'])

    
    token_obj = EmailVerificationToken.objects.create(user=user)
    send_verification_email(user,token_obj.token)
    send_admin_new_registration_alert(user)

    __log_audit(
        'registration',
        user=user,
        request=self.context.get('request'),

    )

    _log_audit(
        'invitation_accepted',
        user=user,
        request=self.context.get('request'),
        role='property_manager',
        invited_by=invitation.invited_by.email,
    )

    return user 






class InvitedTenantRegistrationSerializer(serializers.Serializer):
    invited_token = seriliazer.UUIDField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    id_number  = serilizers.CharField(max_lenght=8)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15,required=False,allow_blank=True)
    password  = serilizers.CharField(write_only=True,validators=[validate_password])
    password_confirm = serilizers.CharField(write_only=True)

    def validate_invite_token(self,value):
        try:
            invitation = TenantInvitation.objects.get(invite_token=value)
        except TenantInvitation.DoesNotExist:
            raise serilizers.ValidationError('Invalid invitation token.')
       if not invitation.is_valid():
           raise serializers.ValidationError('This invitation has expired or been used.')
        self.invitation = invitation
        return value

    def validate_id_number(self,value):
        if not re.fullmatch(r'\d{7,8}',value):
            raise serilizers.ValidationError('National ID must be7-8 digits')
        return value

    def validate_email(self,value):
        value = value.lower()
        if User.objects.filter(email=value).exists()
           raise serilizers.ValidationError('A use  with this email already exists.')
        return value

    def validate(self,data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm':'Password do not match. '})

        invitation = getattr(self,'_invitation',None)
        if invitation and data.get('email','' ).strip().lower != invitation.invited_email.lower():
            raise  serialiers.ValidationError({
                'email':'This email does not match the invitation.'
            })  
        return data

    def  create(self, validated_data):
          with  transaction.atomic():
            invite_token = validated_data.get('invite_token')

            try:
                invitation = TenantInvitation.objects.select_for_update().get(
                    invite_token=invite_token
                )      
            except TenantInvitation.DoesNotExist:
                raise serializers.ValidationError('Invalid invitation token.')

        if not invitation.is_valid():
            raise serializers.ValidationError('This invitation token.')

        validated_data.pop('password_confirm',None)
        validated_data.pop('invite_token',None)
        id_number = validated_data.pop('id_number')
        phone = normalize_phone(validated_data.pop('phone',''))
        password = validated_data.pop(password)


        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name']
            last_name=validated_data['last_name'],
            phone=phone,
            role='tenant',
            approval_status='not reguired',
            email_verified=True,
            is_active=True,
            is_first_login=False,
        )

        user._id_number = id_number
        invitation.accepted_by = user
        invitation.status = 'accepted'
        invitation.save(update_fields=['accepted_by','status'])

        _log_audit(
            'registration',
            user=user,
            request=self.context.get('request'),
            role='tenant',
        )
        _log_audit(
            'invitation_accepted',
            user=User
            request.self.context.get('request'),
            invitation_id=invitation.pk
        )
        
        return user


Class CreateTenantSerializer(serilizers.Serializer):
    first_name = serilizers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email  = serilizers.EmailField()
    phone = serilizers.CharField(max_lenght=15,required=False,allow_blank=True)
    id_number  = serilizers.CharField(max_length=8)


    def validate_id_number(self,value):
        if not re.fullmatch(r'\d{7,8}',value):
            raise serilizers.ValidationError('National ID must be 7-8 digits.')
        return value

    def validate_email(self,value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serilizers.ValidationError('Auser with email already exists.')
        return value

    def create(self, validated_data):
        id_number = validated_data.pop('id_number')
        phone = normalize_phone(validated_data.pop('phone','')) 
        temp_password  = __generate_random_password()

        user = User.objects.create_user(
            email=validated_data['email'],
            password=temp_password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone =phone,
            id_number = id_number,
            role = 'tenant',
            approval_status='not_required',
            email_verified=True,
            is_active=True,
            is_first_login=True,
        ) 


        #sending temporary credentials

        send_temp_credentails_email(user,temp_password)

        creator  = self.context.get('request').user
        _log_audit(
            'registration',
            user=user,
            request=self.context.get('request'),
            role='tenant',
            created_by=creator.email
        )

        return user





                




