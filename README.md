## How to use:

Run the following commands in your terminal:

# Apply migrations (create db tables)**:
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

### Demonstrate FLAW 1 (SQL Injection - OWASP A03:2021)

**Expected behaviour:** The page displays Poll 1 and its choices, even though the ID `0` does not exist, showing the SQL injection vulnerability.
**Fixed behaviour:** Page shows `"Question not found"` and does not display any choices or vote form. The injection attempt is blocked.
**Note:** Only test this on your **local development server**.
**Browser input:** http://127.0.0.1:8000/polls/0 OR id=1/vote/