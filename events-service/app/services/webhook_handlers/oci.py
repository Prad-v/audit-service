"""OCI Webhook Handler"""

class OCIWebhookHandler:
    def __init__(self, db):
        self.db = db
    
    async def process_webhook(self, payload):
        # Mock event for testing
        mock_event = type("Event", (), {
            "event_id": f"oci-{__import__('datetime').datetime.utcnow().timestamp()}",
            "event_type": "cloud_alert",
            "source": "oci",
            "message": "OCI event"
        })()
        return [mock_event]
