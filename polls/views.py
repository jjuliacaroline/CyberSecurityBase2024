import hashlib
import requests
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.db import connection
from .models import Choice, Question
from .forms import VerifyForm


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
    verification_result = None
    choice = None
    voter_name_hashed = None

    choice_id = request.GET.get('choice_id')
    voter_name_hashed = request.GET.get('voter_name')

    if choice_id:
        choice = get_object_or_404(Choice, pk=choice_id)

    if request.method == 'POST':
        form = VerifyForm(request.POST)

        if form.is_valid():
            choice_id = form.cleaned_data["id"]
            verification_url = form.cleaned_data["verify_url"]

            if not verification_url.startswith(('http://', 'https://')):
                verification_url = 'http://' + verification_url

            choice = get_object_or_404(Choice, id=choice_id)

            if request.method == 'POST':
                form = VerifyForm(request.POST)

                if form.is_valid():
                    choice_id = form.cleaned_data["id"]
                    verification_url = form.cleaned_data["verify_url"]

                    try:
                        #A10:2021 – Server-Side Request Forgery (SSRF)
                        response = requests.get(verification_url)
                        #A10:2021 Fix 
                        # from urllib.parse import urlparse

                        # TRUSTED_DOMAINS = ['trusteddomain', 'anothertrusteddomain']

                        # parsed_url = urlparse(verification_url)
                        # if parsed_url.netloc not in TRUSTED_DOMAINS:
                        #     verification_result = "Invalid domain."
                        # else:
                        #     response = requests.get(verification_url)
                        
                        verify_result = response.text

                        if "Verified" in verify_result:
                            choice.votes += 1
                            choice.save()

                        verification_result = "Verification succeeded."

                    except requests.exceptions.RequestException:
                        verification_result = "Verification failed. Proceeding to results..."

                    return redirect('polls:results', pk=choice.question.id)

                else:
                    verification_result = "Invalid form data."
    else:
        form = VerifyForm()

    return render(request, 'polls/verify_vote.html', {
        'form': form,
        'verification_result': verification_result,
        'choice': choice,
        'voter_name_hashed': voter_name_hashed,
    })