from django.contrib.auth import get_user_model
from cpjudge.models import Identity,EmailLoginPolicy
for u in get_user_model().objects.filter(username__in=['C1LIVEA','C1LIVEB','C1LIVEP','C1LIVEQ']):
 print({'id':u.pk,'username':u.username,'active':u.is_active,'college_id_present':bool(Identity.objects.get(user=u).college_id),'usable_password':u.has_usable_password()})
print('email_only',EmailLoginPolicy.objects.filter(email_only=True).exists())
