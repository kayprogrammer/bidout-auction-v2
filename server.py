from app.main import app
from app.core.config import settings

if __name__ == '__main__': 
    app.run(host="0.0.0.0", port=8000, debug=settings.DEBUG, auto_reload=settings.DEBUG)
