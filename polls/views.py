import hashlib
import requests
from urllib.parse import urlparse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.db import connection
from .models import Choice, Question
from .forms import VerifyForm


TRUSTED_DOMAINS = ['127.0.0.1', 'localhost']

class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

    #FLAW 2- Vulnerability OWASP - A01:2021-Broken Access Control
    def get_object(self):
        q_id = self.kwargs['pk']
        return Question.objects.get(id=q_id)
    #FLAW-2-Fix A01:2021 -Broken Access Control
    #def get_object(self):
    #    q_id = self.kwargs['pk']
    #    return get_object_or_404(Question, id=q_id, pub_date__lte=timezone.now())

def vote(request, question_id):
    q = None
    #FLAW-1-Vulnerability OWASP - A03:2021 – Injection
    try:
        with connection.cursor() as c:
            c.execute(f"SELECT * FROM polls_question WHERE id = {question_id}")
            q = c.fetchone()
    except Exception:
        q = None

    #FLAW-1-FIX OWASP - A03:2021 – Injection
    #with connection.cursor() as c:
    #    c.execute("SELECT * FROM polls_question WHERE id = %s", [question_id,])
    #    q = c.fetchone()

    if not q:
        return render(request, 'polls/detail.html', {
            'err_msg': "Question not found",
            'question': None,
        })
    question = Question(id=q[0], question_text=q[1], pub_date=q[2])

    if request.method == 'POST':
        try:
            selected_choice = question.choice_set.get(pk=request.POST['choice'])
            voter_name = request.POST.get('voter_name', 'anonymous')
            #A02:2021 – Cryptographic Failures - weak algorithm
            voter_name_hashed = hashlib.md5(voter_name.encode()).hexdigest()
            #Fix A02: 
            #voter_name_hashed = hashlib.sha256(voter_name.encode()).hexdigest()
            selected_choice.voter_name_hashed = voter_name_hashed
        except (KeyError, Choice.DoesNotExist):
            return render(request, 'polls/detail.html', {
                'question': question,
                'error_message': "You didn't select a choice.",
            })
        else:
            selected_choice.votes += 1
            selected_choice.save()

            return HttpResponseRedirect(f"/polls/verify-voter/?choice_id={selected_choice.id}&voter_name={voter_name_hashed}")
        
    return render(request, 'polls/detail.html', {
        'question': question
    })

def verify_voter(request):
    print(f"DEBUG: Method={request.method}, POST_DATA={request.POST}")
    verification_result = None
    choice = None
    choice_id = request.GET.get('choice_id') or request.POST.get('choice_id')
    voter_name_hashed = request.GET.get('voter_name')

    if choice_id and choice_id != 'None' and choice_id.strip():
        choice = get_object_or_404(Choice, pk=choice_id)
    else:
        choice_id = None

    if choice_id:
        choice = get_object_or_404(Choice, pk=choice_id)

    if request.method == 'POST':
        form = VerifyForm(request.POST)
        if form.is_valid():
            verification_url = form.cleaned_data["verify_url"]

            if not verification_url.startswith(('http://', 'https://')):
                verification_url = 'http://' + verification_url

            #FLAW-4-FIX OWASP - A10:2021 – Server-Side Request Forgery (SSRF)
            parsed_url = urlparse(verification_url)
            domain = parsed_url.netloc.split(':')[0].lower()

            if domain not in TRUSTED_DOMAINS:
                verification_result = "Untrusted domain. Verification failed."
            else:
                print(f"DEBUG: Domain '{domain}' is trusted, attempting request...")
                try:
                    print(f"DEBUG: About to make request to: {verification_url}")
                    response = requests.get(verification_url, timeout=5)
                    print(f"DEBUGGING URL: {verification_url}, STATUS: {response.status_code}, RESPONSE TEXT: '{response.text}'")

                    verify_result = response.text

                    if "verified" in verify_result.strip().lower():
                        if choice:
                            choice.votes += 1
                            choice.save()
                            verification_result = "Verification successful."
                            return HttpResponseRedirect(reverse('polls:results', args=(choice.question.id,)))
                        else:
                            verification_result = "Verification successful, nothing to update."
                    else:
                        verification_result = "Verification failed. Invalid response content."
                except requests.exceptions.RequestException:
                    verification_result = "Verification failed. Could not reach the URL."
        else:
            if request.POST.get('verify_url', '').strip():
                verification_result = "Invalid URL. Please enter a valid URL."
    else:
        form = VerifyForm()

    print(f"DEBUG: Final verification_result = '{verification_result}'")
    return render(request,'polls/verify_vote.html', {
        'form': form,
        'verification_result': verification_result,
        'choice': choice,
        'choice_id': choice_id,
        'voter_name_hashed': voter_name_hashed,
    })
