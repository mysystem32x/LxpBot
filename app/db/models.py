from tortoise import fields, models

class User(models.Model):
    """Модель пользователя"""
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    email = fields.CharField(max_length=255)
    password = fields.CharField(max_length=255)
    id_student = fields.CharField(max_length=100, null=True)
    firstName = fields.CharField(max_length=100, null=True)
    lastName = fields.CharField(max_length=100, null=True)
    phoneNumber = fields.CharField(max_length=20, null=True)
    role = fields.CharField(max_length=255, null=True)

    avatar = fields.CharField(max_length=500, null=True)  # URL аватарки
    created_at = fields.DatetimeField(auto_now_add=True)
    createdAt = fields.CharField(max_length=255, null=True)

    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "users"
class UserSettings(models.Model):
    """Настройки пользователя"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='settings')
    reminders_enabled = fields.BooleanField(default=True)
    remind_24h = fields.BooleanField(default=True)
    remind_3h = fields.BooleanField(default=True)
    remind_1h = fields.BooleanField(default=True)
    remind_daily = fields.BooleanField(default=False)
    reminder_time = fields.TimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "user_settings"

class SentReminder(models.Model):
    """Отправленные напоминания"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='sent_reminders')
    task_id = fields.CharField(max_length=100)
    reminder_type = fields.CharField(max_length=10)
    sent_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "sent_reminders"
        unique_together = (('user_id', 'task_id', 'reminder_type'),)