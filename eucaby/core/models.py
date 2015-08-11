"""Eucaby models."""

from django.contrib.auth import models as auth_models
from django.db import models

from google.appengine.api import memcache

from eucaby_api.utils import utils as api_utils


class UserSettings(models.Model):

    """User settings model."""
    user = models.OneToOneField(auth_models.User)
    settings = models.TextField(default='{}')

    @classmethod
    def user_param(cls, user_id, key):
        """User settings param."""
        def get_param(text_, key_):
            settings = api_utils.json_to_dict(text_)
            return settings.get(key_)

        cache_key = api_utils.create_key('user_id', user_id, 'settings')
        text = memcache.get(cache_key)
        if text:
            return get_param(text, key)
        obj = cls.objects.get(user__id=user_id)
        memcache.set(cache_key, obj.settings)
        return get_param(obj.settings, key)

    class Meta:
        db_table = 'user_settings'
