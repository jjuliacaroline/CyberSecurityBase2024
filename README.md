# Vulnerable Polls App — Cyber security base 2024

**OWASP list used:** 2021

## How to use:

Run the following commands in your terminal:

# Apply migrations (create db tables):
```bash
python3 manage.py migrate
```

# Start the Django development 
```bash
python3 manage.py runserver 
```
# Start shell (optional)
```bash
python3 manage.py shell
```

**Note:** Only test these on your **local development server**.

### FLAW 1: SQL Injection - OWASP A03:2021

**Source:** `polls/views.py` -> `def vote(request, question_id)`. 
**Before fix:** The page displays Poll 1 and its choices, even though the ID `0` does not exist, showing the SQL injection vulnerability.  
**After fix:** Page shows `"Question not found"` and does not display any choices or vote form. The injection attempt is blocked.  
**Browser input:** `http://127.0.0.1:8000/polls/0 OR id=1/vote/`

### FLAW 2: Broken Access Control (OWASP A01:2021)

**Source:** `polls/views.py` -> `ResultsView.get_object()`  
**Before fix:** The view returns the requested `Question` object by ID without checking publish time. By changing the `pk` in the URL, the user can access results of unpublished or future polls.  
**After fix:** The view is changed to use `get_object_or_404` and `pub_date` filter. Unpublished/future polls now return 404 Not Found instead of showing results.  
**Browser input:** `http://127.0.0.1:8000/polls/<FUTURE_ID>/results/`  
