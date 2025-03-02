from utils.models import logs
from django.utils.translation import gettext_lazy as _

def log_create(instance, user=None):
    for field in instance._meta.fields:
        log_type = _('CREATE')
        field_name = field.name
        new_value = getattr(instance, field_name)
        message = _(f"Campo {field_name} definido para {new_value}")
        object_id = instance.pk
        log = logs(log_type=log_type, message=message, module=instance.__class__.__name__, user=user, field=field_name, object_id=object_id, old_value=None, new_value=new_value)
        log.save()

def log_update(instance, user=None):

    try:
        old_instance = instance.__class__.objects.get(pk=instance.pk)
        for field in instance._meta.fields:
            log_type = _('UPDATE')
            field_name = field.name
            print(field_name)
            old_value = getattr(old_instance, field_name)
            print(old_value)
            object_id = instance.pk
            new_value = getattr(instance, field_name)
            print(new_value)
            if old_value != new_value:
                print('entrou')
                message = _(f"Campo {field_name} atualizado de {old_value} para {new_value}")
                log = logs(log_type=log_type, message=message, module=instance.__class__.__name__, user=user, field=field_name, object_id=object_id, old_value=old_value, new_value=new_value)
                log.save()

    except instance.__class__.DoesNotExist:
        pass

def log_delete(instance, user=None):
    for field in instance._meta.fields:
        log_type = _('DELETE')
        field_name = field.name
        old_value = getattr(instance, field_name)
        message = _(f"Campo {field_name} excluído, valor antigo: {old_value}")
        object_id = instance.pk
        log = logs(log_type=log_type, message=message, module=instance.__class__.__name__, user=user, field=field_name, object_id=object_id, old_value=old_value, new_value=None)
        log.save()

def log_custom(log_type=None, message=None, field_name=None,object_id=None, old_value=None, new_value=None, user=None):
    log = logs(log_type=log_type, message=message, module='Custom', user=user, field=field_name, object_id=object_id, old_value=old_value, new_value=new_value)
    log.save()