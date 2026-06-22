from django.conf  import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.utils import timezone

from core.common import SoftDeletableModel,TimeStampedModel





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












    


