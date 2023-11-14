from app.main import app
from app.core.config import settings

if __name__ == '__main__': 
    app.run(port=8000, debug=settings.DEBUG, auto_reload=True)
