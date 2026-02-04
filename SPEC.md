# Location Detail Page Specification

## Overview

The Location detail page displays all schedules (Masses and Confessions) at a specific physical location. Locations are places like hospital chapels, cemeteries, or secondary church buildings that belong to a parish.

## URL Structure

```
/<slug:state>/<slug:city>/local/<slug:slug>/
```

Following the same hierarchy as other URLs in the project. Examples:
- `/rn/natal/local/capela-do-hospital/`
- `/sp/sao-paulo/local/cemiterio-da-consolacao/`

## Data Model

### Location Model

```python
class Location(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=254)
    slug = models.SlugField(max_length=254, unique=True)
    address = models.CharField(max_length=512)
    google_maps_response = models.JSONField()
    google_maps_place_id = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)

    class Meta:
        unique_together = [("name", "address")]
```

### Relationships

- A Location can have many Schedules (via `Schedule.location` foreign key)
- All Schedules at a Location belong to the same Parish (assumption)
- The Parish is determined from the schedules, not stored directly on Location

## User Flow

### From Parish Detail Page
1. User is on Parish detail page
2. User sees a schedule with a location (name/address)
3. User clicks the location link
4. User lands on Location detail page showing all schedules at that location

### From City Page (Parishes by City)
1. User is on city page viewing schedules filtered by day/time
2. User sees a schedule card with a location (name/address)
3. User clicks the location link
4. User lands on Location detail page showing all schedules at that location

## Page Content

### Breadcrumbs
- State > City > **Location name** (not parish name)
- Example: `Rio Grande do Norte > Natal > Capela do Hospital`

### Header Section (`.parish-header`)
- **Location name** as page title (h2)
- **Address** with Google Maps link (opens in new tab)
- **Parish link**: "Parte de [Parish Name]" linking back to the parent Parish detail page

### Schedules Section
- **Title**: "Horários de Missas e Confissões"
- **Grouped by type**: Mass schedules first, then Confession schedules
- **Each schedule card shows**:
  - Day of week
  - Start time (and end time if available)
  - Observation (if any)
  - Verification status and date (if verified)
  - Source with link (if available)

### Empty State
- When no schedules exist for the location, show a message: "Este local ainda não possui horários cadastrados em nosso sistema."

## View Function

```python
def local_detail(request, state, city, slug):
    location = get_object_or_404(Location, slug=slug)
    schedules = (
        Schedule.objects.filter(
            location=location,
            parish__city__slug=city,
            parish__city__state__slug=state,
        )
        .select_related("parish", "parish__city", "parish__city__state", "source")
        .order_by("type", "day", "start_time")
    )

    if not schedules.exists():
        raise Http404("Location not found in this city")

    parish = schedules.first().parish

    return render(
        request,
        "local_detail.html",
        {
            "location": location,
            "parish": parish,
            "schedules": schedules,
            "Schedule": Schedule,
        },
    )
```

## Template

File: `missas/core/templates/local_detail.html`

Extends `base.html` and uses the same styling as `parish_detail.html`:
- `.parish-header` for the header section
- `.schedules-section` for the schedules list
- Bootstrap cards for individual schedules
- FontAwesome icons for visual elements

## Links to Location Detail Page

Location links appear in two templates where schedules are displayed.

### From Parish Detail Page (`parish_detail.html`)

When a schedule has a Location object, the location name and address become a clickable link:

```html
{% if schedule.location %}
    <a href="{% url 'local_detail' state=parish.city.state.slug city=parish.city.slug slug=schedule.location.slug %}">
        {% if schedule.location_name %}{{ schedule.location_name }} - {% endif %}
        {{ schedule.location.address }}
    </a>
{% elif schedule.location_name %}
    {{ schedule.location_name }}
{% endif %}
```

### From City Page (`cards.html`)

The schedule cards on the city page also link to the location detail:

```html
{% if schedule.location_name or schedule.location %}
    <div class="row">
        <div class="col-auto">
            <i class="fa-solid fa-location-dot"></i>
            {% if schedule.location %}
                <a href="{% url 'local_detail' state=schedule.parish.city.state.slug city=schedule.parish.city.slug slug=schedule.location.slug %}">
                    {% if schedule.location_name %}{{ schedule.location_name }} - {% endif %}
                    {{ schedule.location.address }}
                </a>
            {% elif schedule.location_name %}
                {{ schedule.location_name }}
            {% endif %}
        </div>
    </div>
{% endif %}
```

## CSS

Links inside `.parish-header` are styled white with underline for visibility on the blue gradient background:

```css
.parish-header a {
    color: var(--white);
    text-decoration: underline;
}
.parish-header a:hover {
    color: var(--light-blue);
}
```

## Tests

File: `missas/core/tests/test_view_local_detail.py`

### Test Cases

1. **test_status_code_and_template** - Returns 200 and uses `local_detail.html`
2. **test_page_title** - Page title contains location name
3. **test_shows_location_address** - Location address displayed with Google Maps link
4. **test_shows_parish_link** - Link to parent parish detail page is present
5. **test_shows_schedules** - All schedules at the location are displayed
6. **test_shows_confessions** - Confessions displayed in separate section
7. **test_breadcrumbs_show_location_name** - Breadcrumbs display location name (not parish name)
8. **test_returns_404_when_location_not_found** - Returns 404 for non-existent slug
9. **test_returns_404_when_state_does_not_match** - Returns 404 when state slug doesn't match
10. **test_returns_404_when_city_does_not_match** - Returns 404 when city slug doesn't match

## Files Modified/Created

### Modified
- `missas/core/models.py` - Add `slug` field to Location model
- `missas/urls.py` - Add URL pattern for location detail
- `missas/core/views.py` - Add `local_detail` view function
- `missas/core/templates/parish_detail.html` - Make location clickable
- `missas/core/templates/cards.html` - Make location clickable on city page
- `missas/static/styles.css` - Add styles for links in header

### Created
- `missas/core/templates/local_detail.html` - New template
- `missas/core/tests/test_view_local_detail.py` - New test file
- Database migration for Location.slug field

## Migration Strategy

Since Location already exists in production with data:

1. Add slug field as nullable first
2. Generate slugs for existing locations (from name, ensuring uniqueness)
3. Make slug field non-nullable and unique
4. Or: Use a single migration with a default value generator

## Future Considerations

- SEO meta tags for location pages
- Structured data (JSON-LD) for location information
- Canonical URL handling if location can be accessed via multiple routes
- Location search/listing page
