from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend import models

def test_send_whatsapp_campaign(test_client: TestClient, db_session):
    """Test the WhatsApp campaign endpoint with a mocked API call."""
    # --- Setup: Create a user, a campaign, and a contact in the test DB ---
    user = models.User(email="testuser@example.com")
    db_session.add(user)
    db_session.commit()
    
    waba = models.WhatsAppAccount(
        user_id=user.id,
        whatsapp_business_account_id="waba-123",
        phone_number_id="phone-456",
        access_token="test_token"
    )
    campaign = models.Campaign(
        name="Test WhatsApp Campaign",
        body="Hello {name}",
        type="whatsapp",
        user_id=user.id
    )
    contact = models.Contact(name="John Doe", phone="1234567890")
    db_session.add_all([waba, campaign, contact])
    db_session.commit()

    # --- Mock the external call ---
    # This patch intercepts any `httpx.AsyncClient.post` call made during the test
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # --- Act: Call the API endpoint ---
        response = test_client.post(f"/whatsapp/send-campaign?campaign_id={campaign.id}")

        # --- Assert ---
        assert response.status_code == 200
        assert "started for user testuser@example.com" in response.json()["status"]
        
        # Verify that our mocked httpx post was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "graph.facebook.com" in call_args.args[0]
        assert "Hello John Doe" in call_args.kwargs["json"]["text"]["body"]