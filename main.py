# remotebox/main.py

from app import create_app
import functools

print = functools.partial(print, flush=True)
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
