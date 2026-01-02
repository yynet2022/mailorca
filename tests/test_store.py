from mailorca.store import STORE

def test_add_simple_email():
    """Test adding a simple plain text email."""
    raw_email = (
        b"From: sender@example.com\r\n"
        b"To: receiver@example.com\r\n"
        b"Subject: Test Email\r\n"
        b"\r\n"
        b"This is a test body."
    )
    
    STORE.add(raw_email)
    
    assert len(STORE.mails) == 1
    mail = STORE.mails[0]
    assert mail["parsed"]["headers"]["Subject"] == "Test Email"
    assert mail["parsed"]["body_text"].strip() == "This is a test body."

def test_add_utf8_email():
    """Test adding an email with UTF-8 headers and body."""
    # Subject: こんにちは (MIME encoded)
    # Body: テストです
    raw_email = (
        b"From: sender@example.com\r\n"
        b"To: receiver@example.com\r\n"
        b"Subject: =?utf-8?b?44GT44KT44Gr44Gh44Gv?=\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"\xe3\x83\x86\xe3\x82\xb9\xe3\x83\x88\xe3\x81\xa7\xe3\x81\x99"
    )

    STORE.add(raw_email)
    
    assert len(STORE.mails) == 1
    mail = STORE.mails[0]
    assert mail["parsed"]["headers"]["Subject"] == "\u3053\u3093\u306b\u3061\u306f"  # こんにちは
    assert mail["parsed"]["body_text"] == "\u30c6\u30b9\u30c8\u3067\u3059"  # テストです

def test_max_history():
    """Test that the store respects max_history."""
    # Temporarily reduce max_history for testing
    original_max = STORE.max_history
    STORE.max_history = 3
    
    try:
        for i in range(5):
            STORE.add(f"Subject: Test {i}\r\n\r\nBody".encode())
            
        assert len(STORE.mails) == 3
        # Should contain Test 4, Test 3, Test 2 (Newest first)
        assert STORE.mails[0]["parsed"]["headers"]["Subject"] == "Test 4"
        assert STORE.mails[2]["parsed"]["headers"]["Subject"] == "Test 2"
        
    finally:
        STORE.max_history = original_max
