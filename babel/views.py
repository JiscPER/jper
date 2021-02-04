from babel import babel
from .config import LANGUAGES

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(list(LANGUAGES.keys()))