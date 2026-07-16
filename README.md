## Django Docs RAG Corpus Builder

This project starts from the stable Django docs sections and follows internal links under:

- `https://docs.djangoproject.com/en/stable/topics/`
- `https://docs.djangoproject.com/en/stable/ref/`
- `https://docs.djangoproject.com/en/stable/howto/`

If the sitemap contains matching entries, it will use those as a fast path; otherwise it crawls from the seed URLs above.

It writes one JSON file per page into `data/` using this shape:

```json
{
	"url": "https://docs.djangoproject.com/en/stable/topics/auth/",
	"title": "User authentication in Django",
	"content": "Django comes with a user authentication system..."
}
```

### Run

```bash
.venv/bin/python main.py
```

The script uses built-in defaults for the sitemap, output directory, and worker count.
