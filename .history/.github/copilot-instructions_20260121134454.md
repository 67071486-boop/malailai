# WeChat Cloud Hosting Flask Counter Service - AI Assistant Guidelines

## Architecture Overview
This is a simple Flask-based counter service for WeChat Cloud Hosting with modular structure:
- **wxcloudrun/**: Main app package with views, DAO, models, and response utilities
- **Single Counter Pattern**: Uses ID=1 for the global counter instance
- **MySQL Integration**: Environment-based database configuration via `config.py`

## Key Patterns & Conventions

### Database Operations
Use DAO pattern consistently:
```python
from wxcloudrun.dao import query_counterbyid, insert_counter, update_counterbyid, delete_counterbyid
# Always query by ID=1 for the single counter
counter = query_counterbyid(1)
```

### Response Formatting
Always use response utilities for consistent API responses:
```python
from wxcloudrun.response import make_succ_response, make_err_response, make_succ_empty_response
return make_succ_response(counter.count)  # Success with data
return make_err_response('error message')  # Error response
return make_succ_empty_response()  # Success without data
```

### API Structure
- `GET /api/count`: Retrieve current count (returns 0 if no counter exists)
- `POST /api/count`: Update counter with `{"action": "inc"}` or `{"action": "clear"}`

### Development Workflow
- **Local Run**: `python run.py <host> <port>` (e.g., `python run.py 127.0.0.1 5000`)
- **Database Config**: Environment variables `MYSQL_USERNAME`, `MYSQL_PASSWORD`, `MYSQL_ADDRESS`
- **Debug Mode**: Set `DEBUG = True` in `config.py` for development

### Code Organization
- **views.py**: Route handlers and business logic
- **dao.py**: Database access layer
- **model.py**: SQLAlchemy models (Counters table)
- **response.py**: Standardized response builders
- **config.py**: Environment and app configuration

## Important Notes
- Counter auto-creates on first increment if not exists
- Clear action deletes the counter record entirely
- All timestamps use `datetime.now()` for created_at/updated_at
- Follow Flask Blueprint pattern if extending routes