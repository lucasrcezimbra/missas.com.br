# GitHub Copilot Instructions for Missas.com.br

## Project Overview
This is a Django web application that manages Catholic parishes and their Mass/confession schedules across Brazilian cities and states. The platform helps Catholic faithful find Mass times and confession schedules by providing a searchable database of parishes and their services.

## Technology Stack
- **Backend**: Django 5.2.4 with Python 3.12+
- **Database**: PostgreSQL with psycopg2-binary
- **Frontend**: Bootstrap 5, HTMX, FontAwesome
- **Package Management**: Poetry
- **Testing**: pytest with pytest-django
- **Code Quality**: pre-commit hooks, ruff linter
- **Deployment**: Gunicorn, Whitenoise for static files
- **Monitoring**: Sentry for error tracking
- **Data Collection**: Scrapy for web scraping, LLM integration for WhatsApp automation

## Architecture and Domain Models

### Core Models Hierarchy
```
State (Brazilian states like RN, SP)
  └── City (municipalities like Natal, São Paulo)
      └── Parish (Catholic churches/parishes)
          ├── Contact (phone, email, WhatsApp, social media)
          └── Schedule (Mass/confession times by day of week)
```

### Key Domain Concepts
- **Parish**: Catholic church with specific location and services
- **Schedule**: Mass or confession times with day, start/end time, and location
- **Source**: Origin of schedule data (website scraping, WhatsApp contact)
- **Contact**: Communication channels for parishes
- **Verification**: Schedules can be verified with dates to ensure accuracy

## Code Style and Conventions

### Django Patterns
- Function-based views are prefered
- Follow Django's model naming conventions
- Use Django's built-in authentication (extended AbstractUser)
- Implement proper model managers and querysets
- Use model-utils for field tracking and common patterns

### Python Style
- Follow ruff linting rules (configured in pyproject.toml)
- Avoid type hints
- Prefer Portuguese for user-facing strings and comments
- Use English for code identifiers and technical documentation

### Database Design
- Use proper foreign key relationships with CASCADE/RESTRICT as appropriate
- Implement unique_together constraints for business logic
- Use slug fields for URL-friendly identifiers
- Include created_at/updated_at timestamps on main models

### Frontend Patterns
- Use HTMX for dynamic interactions
- Follow Bootstrap 5 component patterns
- Implement responsive design for mobile users
- Use FontAwesome icons consistently

## Development Workflow

### Commands
- `make install`: Set up development environment
- `make dev`: Start development server with Docker PostgreSQL
- `make test`: Run pytest test suite
- `make lint`: Run pre-commit hooks and code quality checks
- `make coverage`: Generate test coverage reports

### Git Commit Process
- When `git commit` fails due to pre-commit issues, you must fix the reported problems before committing
- Run `make lint` or the specific pre-commit hooks to identify and fix code style issues
- Common issues include formatting (ruff), import sorting, and code quality checks

### Pull Request Guidelines
- Every time a PR has UI changes, you must add `[render preview]` to the title
- This triggers the preview deployment so changes can be reviewed visually
- Example: `[render preview] Add new parish contact form` or `[WIP] [render preview] Parish page redesign`
- Every time you make a UI change, run the application, take a screenshot using Playwright MCP using resolution 1920×1080, and add the image to the PR comments.

### Testing
- Write tests in `tests/` directories or `test_*.py` files
- Use model-bakery for test data generation
- Mock external services and APIs
- Test both happy path and edge cases

### Database Management
- Use Django migrations for schema changes
- Create fixtures for seed data (states, cities, sources)
- Use `make dbdump`/`make dbload` for data backup/restore

## Brazilian Context

### Geographic Data
- States use official Brazilian state codes (RN for Rio Grande do Norte, SP for São Paulo)
- Cities should include state context for disambiguation
- Use proper Portuguese names and accents

### Catholic Domain Knowledge
- Mass types: Daily masses, Sunday masses, special celebrations
- Confession schedules: Often different days/times than masses
- Parish hierarchy: Some parishes may have multiple churches/locations
- Schedule variations: Different schedules for holidays, Lent, etc.

### Language and Localization
- Primary language: Portuguese (Brazil)
- Time format: 24-hour format preferred
- Date format: DD/MM/YYYY for user display
- Phone numbers: Brazilian format with country code +55

## Data Sources and Automation

### Web Scraping
- Use Scrapy for extracting parish data from diocesan websites
- Store scraped data in JSONL format
- Implement respectful scraping with delays

### WhatsApp Integration
- Semi-automated process for collecting schedule updates
- LLM integration for parsing unstructured messages
- Manual confirmation required for data accuracy

### Data Quality
- Implement verification workflows for schedule accuracy
- Track data sources for transparency
- Regular updates and verification of parish information

## Security Considerations
- Protect contact information (especially WhatsApp numbers)
- Use Django's CSRF protection
- Implement proper user authentication for admin functions
- Store sensitive configuration in environment variables

## Performance Optimization
- Use Django's caching framework
- Implement database indexing for search operations
- Optimize static file serving with Whitenoise
- Consider pagination for large parish lists

## Deployment and Production
- Docker Compose for local development
- Environment-based configuration with python-decouple
- Static file collection and compression
- Database migrations in deployment pipeline
- Sentry integration for production monitoring

## Common Tasks and Patterns

When implementing new features:
1. Start with model design and migrations
2. Write comprehensive tests
3. Implement admin interface if needed
4. Create user-facing views and templates
5. Add appropriate URL patterns
6. Update fixtures if needed for testing

When debugging issues:
1. Check Django logs and Sentry for errors
2. Verify database constraints and relationships
3. Test with realistic Brazilian parish data
4. Ensure mobile responsiveness
5. Validate Portuguese language handling
