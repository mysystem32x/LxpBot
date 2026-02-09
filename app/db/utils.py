from .models import UserSettings

async def get_or_create_user_settings(user_id: int) -> UserSettings:
    """Получает или создает настройки для пользователя"""
    settings, created = await UserSettings.get_or_create(
        user_id=user_id,
        defaults={
            'reminders_enabled': True,
            'remind_24h': True,
            'remind_3h': True,
            'remind_1h': True,
            'remind_daily': False,
            'reminder_time': None
        }
    )
    return settings

async def toggle_setting(user_id: int, setting_name: str) -> bool:
    """Переключает настройку"""
    settings = await get_or_create_user_settings(user_id)
    current_value = getattr(settings, setting_name)
    setattr(settings, setting_name, not current_value)
    await settings.save()
    return not current_value

async def get_user_settings(user_id: int) -> dict:
    """Возвращает все настройки пользователя"""
    settings = await get_or_create_user_settings(user_id)
    return {
        'reminders_enabled': settings.reminders_enabled,
        'remind_24h': settings.remind_24h,
        'remind_3h': settings.remind_3h,
        'remind_1h': settings.remind_1h,
        'remind_daily': settings.remind_daily,
        'reminder_time': settings.reminder_time
    }