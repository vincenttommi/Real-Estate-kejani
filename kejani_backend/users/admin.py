from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    AcessAuditLog,EmailVerificationToken,
    PMInvitation,
    PasswordResetToken,
    TenantInvitation,
    User,
)




@dmin.register(User)
class User(BaseUserAdmin):
    """
    UserAdmin documentation string
    """

    list_display  = (
        'email','first_name','last_name','role',
        'approval_status','email_verified','is_active','is_demon'
    )
    list_filter  = ("role","approval_status","email_verified","is_active","is_demo")
    search_fields = ("email","first_name","last_name","phone")
    ordering = ("-created_at",)

    fieldsets = (
    (None,{'fields':('email','password')}),
    ('Personal info',{'fields':('first_name','last_name','phone','uuid')}),
    ('Role & Status', {'fields':('role','approval_status','email_verified','phone_verified')}),
    ('Flags',{'fields':('is_first_login','is_demo')}),
    ('Security',{'fields':('last_login_ip','last_login')}),
    ('Permissions',{'fields':('is_active','is_staff','is_superuser','groups','user_permissions')}),
    ('Soft Delete',{'fields':('deleted_at',)}),

    )
   
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'role', 'password1', 'password2',
            ),
        }),
    )
    
readonly_fields  = ('uuid','last_login_ip','last_login')





@admin.register(EmailVerificationToken)
class EmailVerificationToken(admin.ModelAdmin):
    """
  Email VerificationTokenAdmin documentation string.
    """
    list_display = ('user','token','is_used','created_at')
    list_filter = ('is_used',)
    search_fields = ('user__email',)


@admin.Register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    PasswordResetTokenAdmin documentation string    

    """

    list_display  = ('user','token','is_used','expires_at','created_at')
    list_filter = ('is_used',)
    search_fields = ('user_email',)





@admin.register(PMInvitation)
class PMInvitationAdmin(admin.ModelAdmin):
    """
    PMInvitationAdmin documentation String.
    """

    list_display = (
        'invited_email','invited_name','invited_by','status',
        'commission_rate','expires_at',
    )
    list_filter  = ('status',)
    search_fields = ('invited_email','ivited_name')


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    list_display =(
        'invited_email','invited_name','invited_by','property_name','unit_number','status','expires_at',
    )