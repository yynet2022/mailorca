def test_read_main(client):
    """Test the main list page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "MailOrca" in response.text


def test_api_empty_list(client):
    """Test the API returns empty list initially."""
    response = client.get("/api/mails")
    assert response.status_code == 200
    assert response.json() == []


def test_api_list_with_mail(client):
    """Test the API returns added mail."""
    from mailorca.store import STORE

    # Manually add a mail
    STORE.add(b"Subject: API Test\r\n\r\nBody")

    response = client.get("/api/mails")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["parsed"]["headers"]["Subject"] == "API Test"
    assert "raw" not in data[0]  # raw data should be excluded in list API
