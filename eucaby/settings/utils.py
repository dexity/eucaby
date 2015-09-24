from eucaby_api import config

CONFIG_MAP = {
    config.DEV_APP_ID: 'eucaby.settings.development',
    config.PRD_APP_ID: 'eucaby.settings.production',
    'testing': 'eucaby.settings.testing',
    'default': 'eucaby.settings.devappserver'
}


def get_settings_module(gae_project_id):
    try:
        return CONFIG_MAP[gae_project_id]
    except KeyError:
        return CONFIG_MAP['default']
