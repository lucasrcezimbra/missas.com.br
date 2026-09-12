def test_sentry_scrubs_shared_secret_headers_and_configuration(settings):
    event = {
        "request": {
            "headers": {"X-API-Key": "header-credential", "Accept": "application/json"}
        },
        "extra": {
            "nested": {
                "HTTP_X_API_KEY": "meta-credential",
                "MISSAS_API_SHARED_SECRET": "config-credential",
            }
        },
    }
    settings.SENTRY_EVENT_SCRUBBER.scrub_event(event)
    assert "credential" not in repr(event)
    assert event["request"]["headers"]["Accept"] == "application/json"
