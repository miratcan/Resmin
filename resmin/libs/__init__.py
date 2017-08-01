import string
import random
from django.conf import settings


def key_generator(size=settings.INVITATION_KEY_LENGTH,
                  chars=string.ascii_uppercase + string.digits, prefix=''):
    key = ''.join(random.choice(chars) for x in range(size))

    if prefix:
        return "%s-%s" % (prefix, key)
    else:
        return key
