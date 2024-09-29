# About

- Streamlit dashboard running on a server


## Debug

For Cloud Editor, it looks like the request is blocked so we can unwind

```
streamlit run app.py --server.enableXsrfProtection=false --server.enableCORS=false
```

