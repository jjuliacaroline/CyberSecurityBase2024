### Vulnerable Polls App — Cyber security base 2024
## OWASP list used: 2021

## How to use:
Run the following commands in your terminal:

## Apply migrations (create db tables):
```bash
python3 manage.py migrate
```

## Start the Django development 
```bash
python3 manage.py runserver 
```
## Start shell (optional)
```bash
python3 manage.py shell
```

**Note:** This repository intentionally contains insecure code. Only test these on your local development server.

### FLAW 1: SQL Injection - OWASP A03:2021
**Source:** `polls/views.py` -> `def vote(request, question_id)` (Line 49).  
**Before fix:** The page displays Poll 1 and its choices, even though the ID `0` does not exist, showing the SQL injection vulnerability.  
**After fix:** Page shows `"Question not found"` and does not display any choices or vote form. The injection attempt is blocked.  
**Browser input:** `http://127.0.0.1:8000/polls/0 OR id=1/vote/`

### FLAW 2: Broken Access Control - OWASP A01:2021

**Source:** `polls/views.py` -> `ResultsView.get_object()` (Line 38).  
**Before fix:** The view returns the requested `Question` object by ID without checking publish time. By changing the `pk` in the URL, the user can access results of unpublished or future polls.  
**After fix:** The view is changed to use `get_object_or_404` and `pub_date` filter. Unpublished/future polls now return 404 Not Found instead of showing results.  
**Browser input:** `http://127.0.0.1:8000/polls/<FUTURE_ID>/results/`  

### FLAW 3: Cryptographic Failures - OWASP A02:2021
**Source:** `polls/views.py` -> `def vote(request, question_id)` (line 73).  
**Before fix:** The application uses MD5 (`hashlib.md5`) to hash voter names. MD5 is a weak cryptographic algorithm that is vulnerable to collision attacks and can be easily cracked using rainbow tables or brute force. The hash length is 32 characters.  
**After fix:** The application uses SHA-256 (`hashlib.sha256`) to hash voter names. SHA-256 is a strong cryptographic hash function that is resistant to collision attacks and provides better security. The hash length is 64 characters.  

**How to test:**
1. Vote on a poll with a voter name (e.g."TestUser").
2. Check the database:
```bash
    python3 manage.py dbshell
    SELECT choice_text, voter_name_hashed, LENGTH(voter_name_hashed) as hash_length FROM polls_choice WHERE voter_name_hashed IS NOT NULL;
```

### FLAW 4: Server-Side Request Forgery (SSRF) - OWASP A10:2021
**Source:** `polls/views.py` -> `def verify_voter(request)` (Line 108).  
**Before fix:** The server makes an outgoing GET request to any URL entered by the user in the "Add URL to verify" field. This allows an attacker to make the server request internal or external resources, potentially bypassing network restrictions.  
**After fix:** The server checks the domain of the provided URL against a trusted list (`TRUSTED_DOMAINS = ['127.0.0.1', 'localhost']`). Only requests to trusted domains are allowed. All other URLs are rejected with `"Untrusted domain. Verification failed."`.    

**How to test:**
1. Start a local test server that returns the text `verified`:
   - `echo "verified" > index.html && python3 -m http.server 8001`
2. Start the Django app (in vulnerable mode; `requests.get` active).
3. Vote on a poll so you are redirected to `/polls/verify-voter/?choice_id=<id>&voter_name=<hash>`.
4. In the verification form enter: `http://127.0.0.1:8001/` and submit.
5. Expected: server fetches the URL, sees `verified`, increments the vote and redirects to results.

**Browser input (vulnerable):** Enter any URL such as `http://127.0.0.1:8001/` (internal) or `http://example.com` (external) in the verify form. The server attempts the GET request to all URLs, regardless of domain. Even if the response is not `"verified"`, the network request happens.

**Browser input (fixed):**  
- Enter `http://127.0.0.1:8001/` -> request succeeds (trusted domain).  
- Enter `http://example.com` -> request is blocked immediately, verification fails, and no network request is made.

### FLAW 5: Security Misconfiguration - OWASP A05:2021
**Source:** `mysite/settings.py` (line 22).  
**Before fix:** The application has three critical security misconfigurations:
- `SECRET_KEY = '12345'` -> Hardcoded weak secret key that can be easily guessed.
- `DEBUG = True` -> Debug mode enabled, which exposes sensitive information like stack traces, environment variables, and settings in error pages.
- `ALLOWED_HOSTS = ["*"]` -> Allows any host to access the application, making it vulnerable to Host Header attacks.  
**After fix:** The security settings are properly configured:
- `SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'backup_secure_key')` -> Secret key is loaded from environment variable.
- `DEBUG = False` -> Debug mode disabled for production, preventing information leakage.
- `ALLOWED_HOSTS = ["127.0.0.1", "localhost"]` -> Restricted to trusted domains only.  

**Browser input:** `http://127.0.0.1:8000/polls/FLAW5/` (or any non-existent URL)  
**Before fix:** The page displays a detailed Django debug error page showing:
- Full stack trace
- Request information
- URL patterns
- Settings information
- Message: "You're seeing this error because you have DEBUG = True in your Django settings file"  

**After fix:** The page displays a simple generic error page with just "Not Found" and minimal information. No sensitive details are exposed.  