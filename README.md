```bash
1. uv pip install streamlit
2. uv pip install crewai-tools
3. uv pip install twilio
4. pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

```bash
streamlit run src/call_agent/main.py
uvicorn src.call_agent.main:app --reload
```

```bash
git checkout -b development   # Switched to a new branch 'development'
git push -u origin development
git push --force origin development
```