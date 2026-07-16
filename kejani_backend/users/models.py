import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser,PermissionsMixin
from django.db import models



class UserManager(BaseUserManager):
    """
     Custom manager using email instead of username
    """

    def create_user(self,email,password=None,**extra_fields):
        if not email:
            raise ValueError("The Email field must set ")


        email = self.normalize_email(email)
        extra_fields = setdefault("is_active",True)

        user = self.model(email=email, extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)  
        return user

    def create_superuser(self,email,password,**extra_fields):
        if not password:
            raise ValueError("Superuse must have a password")

        extra_fields.setdefault("is_staff",True)
        extra_fields.setdefault("is_superuser",True)
        extra_fields.setdefault("role","admin")
        extra_fields.setdefault("approval_status","approved")
        extra_fields.setdefault("email_verified",True)


        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True ")


        return self.create_user(email,password,**extra_fields)






class User(AbstractBaseUser,PermissionMixin, SoftDeletableModel):

    username = None

    ROLE_CHOICES = (
        ("admin","Admin"),
        ("landlord","Landlord"),
        ("property_manager","Property Manager"),
        ("tenant","Tenant"),
    )


APPROVAL_STATUS_CHOICES = (
    ("not_required","Not Required"),
    ("pending","Pending"),
    ("approved","Approved"),
    ("rejected","Rejected"),
    ("suspended","Suspended"),
)   


uuid = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
email = models.EmailField(unique=True)

phone = models.CharField(max_length=15,blank=True)
phone_verified = models.BooleanField(default=False)
email_verified = models.BooleanField(default=False)


id_number = models.CharField(max_length=20, blank=True)
estimated_units_range = models.CharField(max_length=10,blank=True)

terms_accepted_at = models.DateTimeField(null=True,blank=True)
onboarding_completed_at = models.DateTimeField(null=True,blank=True)


role  = models.CharField(max_length=20, choices=ROLE_CHOICES)
approval_status = models.CharField(
    max_length=20,
    choices=APPROVAL_STATUS_CHOICES,
    default="not required",
)

is_first_login = models.BooleanField(default=True)
is_demo = models.BooleanField(default=False)

last_login_ip = models.GeneratedIPAdressField(null=True,blank=True)


USERNAME_FIELD = 'email'
REQUIRED_FIELDS = ['first_name','last_name']

objects  = UserManager()


class Meta:
    data = "users"
    ordering =  ['-created_at']


def __str__(self):
    return self.email



class Email verificationToken(SoftDeletableModel):
    """
    One-time email verificationToken
    """

     user  = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_token",
    )
    token = models.UUIDField(default=uuid.uuid4,unique=True)
    is_used =  models.BooleanField(default=False)


    class Meta:
        db_table  = "email_verification_tokens"

    def __str_(self):
        return f"EmailVerification for {self.user.email}"




class PasswordResetToken(SoftDeletableModel):

    """Password reset token """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_token",
    )
    token = models.UUIDField(default=uuid.uuid4,unique=True)
    is_used = models.BooleanField(default=False)



    class Meta:
        db_table = "email_verification_tokens"


    def __str__(self):
        return f"EmailVerification for {self.user.email}"






class PasswordResetToken(SoftDeletableModel):
    """
    password reset token
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",

    )


    token = models.UUIDField(default=uuid.uuid4,unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()


    class Meta:
        db_table = "password_reset_tokes"

    def save(self,*args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args,**kwargs)

    def is_valid(self):
        return (
            not self.is_used
            and self.expires_at > timezone.now()
            and self.user.is_active
            and self.user.on_deleted_at is None
        )   


    def __str__(self):
        return f"passwordReset for {self.user.email}"        




#
#INVITATIONS
#



class PMInvitation(SoftDeletableModel):
    """
    Property Manager Invitation
    """


    STATUS_CHOICES = (
        ("pending","Pending"),
        ("accepted","Accepted"),
        ("expired","Expired"),
        ("declined")
    )



    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pm_invitations_sent",
    )

    property_id = models.IntegerField(null=True,blank=True)
    invite_token = models.UUIDField(default=uuid.uuid4,)

    invited_token = models.UUIDField(default=uuid.uuid4, unique=True)
    invited_email = models.EmailField()
    invited_name = models.CharField(max_length=200)
    invited_by = models.CharField(max_length=15,blank=True)

     
    common_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,
    )


    status  = models.CharField(
        max_length=20,choices=STATUS_CHOICES,
        default="pending",
    )

    expires_at = models.DateTimeField()

    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pm_invitations_receieved",
    )

    class Meta:
        db_table = "pm_invitations"

    def save(self,*args,**kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)





class TenantInvitation(SoftDeletableModel):

    """Tenant Invitation"""

    STATUS_CHOICES =(
        ("pending","Pending"),
        ("accepted","Accepted"),
        ("expired","Expired"),
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_invitations_sent",
    )

   unit_id = models.IntegerField(null=True,blank=True)
   unit_number = models.CharField(max_length=20,blank=True)
   property_name = models.CharField(max_length=200,blank=True)

   invite_token = models.UUIDField(default=uuid.uuid4, unique=True)

   invite_emai = models.EmailField()
   invited_name = models.CharField(max_length=200,blank=True)
   invited_phone = models.CharField(max_length=15,blank=True)


   status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default="pending",
   )


   expires_at = models.DateTimeField()
   
   accepted_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name="tenant_invitations_received",
   )

class Meta:
    db_table = "tenant_invitations"

def save(self,*args, **kwargs):
    if not self.expires_at:
        self.expires_at = timezone.now() + timedelta(days=7) 
    super().save(*args,**kwargs)



def is_valid(self):
    return self.status == "pending" and self.expires_at > timezone.now

 
def __str_(self):
    return f"TenantInvitation for {self.invite_emaail} "



#AUDIT LOG 


class AcessAuditLog(SoftDeletableModel):
    """ Audit log model"""

    EVENT_CHOICES = (
        ("login_success","Login Success"),
        ("login_failed","Login Failed"),
        ("logout","Logout"),
        ("registration","Registration"),
        ("email_verified","Email Verified"),
        ("password_reset_requested","Password Reset Requested"),
        ("password_reset_completed","Password Changed"),
        ("account_approved","Account Approved"),
        ("account_rejected","Account Rejected"),
        ("account_suspended","Account Suspended"),
        ("demo_login","Demo Login"),
        ("invitation_sent","Invitation Sent"),
        ("invitation_accepted","Invitation Accepted"),
    )

 
    event  = models.CharField(max_length=30,choices=EVENT_CHOICES)
     

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,blank=True,on_delete=models.SET_NULL,related_name="audit_logs",        
    )


    ip_address = models.GeneratedField(null=True,blank=True)
    role = models.CharField(max_length=20,blank=True)
    details = models.JSONField(default=dict,blank=True)

    class Meta:
        db_table = "access_audit_log"
        ordering = ["-created"]
     
    def __str__(self):
        return f"{self.event} - {self.user or 'anonymous'} - {self.created_at}"

 









    


