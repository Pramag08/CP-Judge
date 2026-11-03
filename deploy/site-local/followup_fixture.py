"""Temporary native-auth/math fixtures; existing users and domain records stay intact."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from django.contrib.auth.models import User, AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import render_to_string
from django.test import Client
from judge.models import Profile, Language, Problem, Contest, Submission, Judge, RuntimeVersion

credentials=json.loads(Path('/tmp/cpjudge-followup-fixtures.json').read_text())
state=Path('/tmp/cpjudge-followup-state.json')
operation=globals().get('OP','setup')
def serialized(queryset):
    return json.loads(json.dumps(list(queryset.values()),cls=DjangoJSONEncoder))
def domain_counts():
    return {model.__name__:model.objects.count() for model in [Problem,Contest,Submission,Judge,RuntimeVersion]}
if operation in ['setup','render']:
    if operation=='setup':
        assert not state.exists(), 'fixture state already exists'
        before={'users':serialized(User.objects.order_by('pk')),
                'profiles':serialized(Profile.objects.order_by('pk')),
                'domain_counts':domain_counts(), 'fixture_ids':{}}
        for role,data in credentials.items():
            assert not User.objects.filter(username=data['username']).exists()
            user=User.objects.create_user(username=data['username'],password=data['password'],
                        is_active=True,is_staff=role=='staff',is_superuser=role=='staff')
            profile,_=Profile.objects.get_or_create(user=user)
            profile.math_engine='jax'
            profile.about=r'Inline ~\frac{1}{2}+\alpha^2~. Display: $$\int_0^1 x^2\,dx=\frac{1}{3}$$ Matrix: $$\begin{pmatrix}1&2\\3&4\end{pmatrix}$$'
            profile.save(update_fields=['math_engine','about'])
            before['fixture_ids'][role]=user.pk
        fd=os.open(state,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        os.write(fd,json.dumps(before).encode());os.close(fd)
    else:
        before=json.loads(state.read_text())
    req=Client().get('/accounts/login/').wsgi_request
    problem=SimpleNamespace(time_limit=2,memory_limit=262144,language_time_limit=[],language_memory_limit=[],markdown_style='problem')
    desc=r'Synthetic statement fixture; no imported package or judge data. Inline ~x^2+\sqrt{2}~. $$\sum_{i=1}^n i=\frac{n(n+1)}{2}$$ $$\require{color}\color{blue}{\beta+1}$$'
    html=render_to_string('problem/raw.html',{'url':'http://127.0.0.1:8000/','problem':problem,
          'problem_name':'Synthetic statement math — renderer only','description':desc},request=req)
    folder=Path('/app/resources/cpjudge-fixtures');folder.mkdir(exist_ok=True)
    (folder/'b01-followup-statement.html').write_text(html)
    preview=render_to_string('user/preview.html',{'preview_data':desc,'MATH_ENGINE':'jax','REQUIRE_JAX':True},request=req)
    wrapper='<!DOCTYPE html><meta charset="utf-8"><div id="preview">'+preview+'</div>'
    wrapper+='<script src="/static/a09/jquery.min.js"></script><script src="/static/martor-mathjax.js"></script>'
    wrapper+='<script>jQuery(function($){$(document).trigger("martor:preview",[$("#preview")]);});</script>'
    (folder/'b01-followup-preview.html').write_text(wrapper)
    assert domain_counts()==before['domain_counts']
    print(json.dumps({'fixture_ids':before['fixture_ids'],'temporary_accounts':2,'existing_users_saved_privately':len(before['users']),
                      'statement_fixture':'native problem/raw.html with synthetic context; no Problem row/import',
                      'preview_fixture':'native user/preview.html plus actual martor loader',
                      'domain_counts_unchanged':True}))
else:
    before=json.loads(state.read_text())
    oldids=[row['id'] for row in before['users']]
    assert serialized(User.objects.filter(pk__in=oldids).order_by('pk'))==before['users'], 'Existing account data changed'
    pids=[row['id'] for row in before['profiles']]
    assert serialized(Profile.objects.filter(pk__in=pids).order_by('pk'))==before['profiles'], 'Existing profile data changed'
    assert domain_counts()==before['domain_counts']
    participant=User.objects.get(pk=before['fixture_ids']['participant'])
    if operation=='changed':
        assert participant.check_password(credentials['participant']['changed_password'])
        assert not participant.check_password(credentials['participant']['password'])
    elif operation=='reset':
        assert participant.check_password(credentials['participant']['password'])
        assert not participant.check_password(credentials['participant']['changed_password'])
    elif operation=='cleanup':
        for pk in before['fixture_ids'].values():
            assert not Submission.objects.filter(user__user_id=pk).exists()
        User.objects.filter(pk__in=before['fixture_ids'].values()).delete()
        assert serialized(User.objects.order_by('pk'))==before['users']
        assert serialized(Profile.objects.order_by('pk'))==before['profiles']
        for name in ['b01-followup-statement.html','b01-followup-preview.html']:
            (Path('/app/resources/cpjudge-fixtures')/name).unlink()
        state.unlink();Path('/tmp/cpjudge-followup-fixtures.json').unlink()
    else:raise ValueError(operation)
    print(json.dumps({'operation':operation,'existing_users_profiles_identical':True,
                      'domain_counts_unchanged':True,'temporary_accounts_removed':operation=='cleanup'}))
