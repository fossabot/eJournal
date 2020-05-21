import json
import re
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from sentry_sdk import capture_message

from VLE.models import Field
from VLE.utils.error_handling import VLEMissingRequiredField


# Base 64 image is roughly 37% larger than a plain image
def validate_profile_picture_base64(url_data):
    """Checks if the original size does not exceed 10MB AFTER encoding."""
    if len(url_data) > settings.USER_MAX_FILE_SIZE_BYTES * 1.37:
        raise ValidationError("Max size of file is {} Bytes".format(settings.USER_MAX_FILE_SIZE_BYTES))


def validate_user_file(in_memory_uploaded_file, user):
    """Checks if size does not exceed 10MB. Or the user has reached his maximum storage space."""
    if in_memory_uploaded_file.size > settings.USER_MAX_FILE_SIZE_BYTES:
        raise ValidationError("Max size of file is {} Bytes".format(settings.USER_MAX_FILE_SIZE_BYTES))
    if len(in_memory_uploaded_file.name) > 128:  # reserving 37 for unique key, and the rest (91) as filepath
        raise ValidationError("Maximum filename length is 128, please rename the file.")

    user_files = user.filecontext_set.all()
    # Fast check for allowed user storage space
    if settings.USER_MAX_TOTAL_STORAGE_BYTES - len(user_files) * settings.USER_MAX_FILE_SIZE_BYTES <= \
       in_memory_uploaded_file.size:
        total_user_file_size = sum(user_file.file.size for user_file in user_files)
        if total_user_file_size > settings.USER_MAX_TOTAL_STORAGE_BYTES:
            if user.is_teacher:
                capture_message('Staff user {} file storage of {} exceeds desired limit'.format(
                    user.pk, total_user_file_size), level='error')
            else:
                raise ValidationError('Unsufficient storage space.')


def validate_email_files(files):
    """Checks if total size does not exceed 10MB."""
    if sum(file.size for file in files) > settings.USER_MAX_EMAIL_ATTACHMENT_BYTES:
        raise ValidationError(
            "Maximum email attachments size is {} Bytes.".format(settings.USER_MAX_EMAIL_ATTACHMENT_BYTES))


def validate_password(password):
    """Validates password by length, having a capital letter and a special character."""
    if len(password) < 8:
        raise ValidationError("Password needs to contain at least 8 characters.")
    if password == password.lower():
        raise ValidationError("Password needs to contain at least 1 capital letter.")
    if re.match(r'^[a-zA-Z0-9]+$', password):
        raise ValidationError("Password needs to contain a special character.")


def validate_entry_content(data, field):
    """Validates the given data based on its field type, any validation error will be thrown."""
    if field.required and not (data or data == ''):
        raise VLEMissingRequiredField(field)
    if not data:
        return

    # TODO: improve VIDEO validator
    if field.type == Field.URL or field.type == Field.VIDEO:
        url_validate = URLValidator(schemes=('http', 'https', 'ftp', 'ftps'))
        url_validate(data)

    if field.type == Field.SELECTION:
        if data not in json.loads(field.options):
            raise ValidationError("Selected option is not in the given options")

    if field.type == Field.DATE:
        try:
            datetime.strptime(data, '%Y-%m-%d')
        except ValueError as e:
            raise ValidationError(str(e))

    if field.type == Field.DATETIME:
        try:
            datetime.strptime(data, '%Y-%m-%dT%H:%M:%S')
        except ValueError as e:
            raise ValidationError(str(e))

    # TODO FILE-BUGFIX: Write tests for block
    # TODO FILE-BUGFIX: Test posting from two tabs, in browser setup post for entry, second tab do some (inc new image
    # in RT) now post first (older) tab entry. Do the same but now post a different entry in between, triggering temp
    # file cleanup
    if field.type == Field.RICH_TEXT:
        re_access_ids = re.compile(r'\/files\/[0-9]+\?access_id=([a-zA-Z0-9]+)')
        rt_access_ids = re.findall(re_access_ids, rich_text)
        n_rt_access_ids = len(rt_access_ids)

        # TODO FILE-BUGFIX: Check if unique ids are not enforced anyway at db layer
        if n_rt_access_ids > len(set(rt_access_ids)):
            raise ValidationError("RichText data field is holds duplicate file access ids.")

        files = FileContext.objects.filter(access_id__in=rt_access_ids)

        # TODO FILE-BUGFIX: evaluate if this should not be a value matching checking (all ids matching)
        if files.count() != n_rt_access_ids:
            raise ValidationError("RichText data field holds access ids without matching FileContext.")

        if not all(os.path.exists(f.file.path) for f in files):
            raise ValidationError("RichText data field holds files which do not exist.")
