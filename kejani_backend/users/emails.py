"""
Email sending utilities for the users app.
All emails are sent via Django's send_mail (backed by console in dev, SendGrid in prod).
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def _send(subject, template_name, context, recipient_list):
    """Internal helper — renders an HTML template and sends."""
    context.setdefault('frontend_url', settings.FRONTEND_URL)
    html_message = render_to_string(f'emails/{template_name}.html', context)
    plain_message = strip_tags(html_message)
    
    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
    )
    msg.attach_alternative(html_message, "text/html")
    
    # Anymail / Resend-specific features for analytics & tracking
    msg.tags = [template_name]
    msg.metadata = {"template": template_name}
    # Note: Resend does not support track_clicks or track_opens
    
    msg.send(fail_silently=False)


def send_verification_email(user, token):
    """Send email verification link after landlord / PM registration."""
    _send(
        subject='KE-JANI — Verify Your Email Address',
        template_name='email_verification',
        context={
            'user': user,
            'verification_url': (
                f'{settings.FRONTEND_URL}/auth/verify-email?token={token}'
            ),
        },
        recipient_list=[user.email],
    )


def send_admin_new_registration_alert(user):
    """Notify admin@ke-jani.com of a new landlord / PM registration."""
    _send(
        subject=f'KE-JANI — New {user.get_role_display()} Registration',
        template_name='admin_new_registration',
        context={'user': user},
        recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
    )


def send_approval_email(user):
    """Inform user their account has been approved."""
    _send(
        subject='KE-JANI — Your Account Has Been Approved!',
        template_name='account_approved',
        context={
            'user': user,
            'login_url': f'{settings.FRONTEND_URL}/auth/signin',
        },
        recipient_list=[user.email],
    )


def send_rejection_email(user, reason=''):
    """Inform user their account has been rejected."""
    _send(
        subject='KE-JANI — Account Registration Update',
        template_name='account_rejected',
        context={'user': user, 'reason': reason},
        recipient_list=[user.email],
    )


def send_temp_credentials_email(user, temp_password):
    """Send temporary login credentials to an admin-created tenant."""
    _send(
        subject='KE-JANI — Your Account Has Been Created',
        template_name='temp_credentials',
        context={
            'user': user,
            'temp_password': temp_password,
            'login_url': f'{settings.FRONTEND_URL}/auth/signin',
        },
        recipient_list=[user.email],
    )


def send_pm_invitation_email(invitation):
    """Send PM invite link from a landlord."""
    _send(
        subject='KE-JANI — You\'ve Been Invited as a Property Manager',
        template_name='pm_invitation',
        context={
            'invitation': invitation,
            'register_url': (
                f'{settings.FRONTEND_URL}/auth/invite/pm'
                f'?invite={invitation.invite_token}'
            ),
        },
        recipient_list=[invitation.invited_email],
    )


def send_tenant_invitation_email(invitation):
    """Send tenant invite link from a landlord / PM."""
    _send(
        subject='KE-JANI — You\'ve Been Invited to Join',
        template_name='tenant_invitation',
        context={
            'invitation': invitation,
            'register_url': (
                f'{settings.FRONTEND_URL}/auth/invite/tenant/{invitation.invite_token}'
            ),
        },
        recipient_list=[invitation.invited_email],
    )


def send_password_reset_email(user, token):
    """Send password reset link."""
    _send(
        subject='KE-JANI — Password Reset Request',
        template_name='password_reset',
        context={
            'user': user,
            'reset_url': (
                f'{settings.FRONTEND_URL}/auth/reset-password?token={token}'
            ),
        },
        recipient_list=[user.email],
    )


def send_welcome_email(user):
    """Welcome email after tenant completes invite registration."""
    _send(
        subject='KE-JANI — Welcome!',
        template_name='welcome',
        context={
            'user': user,
            'login_url': f'{settings.FRONTEND_URL}/auth/signin',
        },
        recipient_list=[user.email],
    )
