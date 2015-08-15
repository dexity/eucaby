from django.conf import settings as conf_settings


def settings(request):
    """Settings parameters."""
    return dict(IS_PROD=conf_settings.ENV_TYPE == 'production')
