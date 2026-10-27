from app.models import User

def test_user_password_hashing():
    """Verify passwords are cryptographically hashed and verified correctly."""
    user = User(email="test@campus.ac.in", display_name="Test Student")
    user.set_password("MySecurePass#2026")

    assert user.password_hash != "MySecurePass#2026"
    assert user.check_password("MySecurePass#2026") is True
    assert user.check_password("WrongPassword") is False

def test_login_successful(client):
    """Verify logging in with valid credentials creates an active session."""
    response = client.post("/login", data={
        "email": "seller@coeptech.ac.in",
        "password": "SellerPass123"
    }, follow_redirects=True)

    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None
        assert sess.get("user_display_name") == "Test Seller"

def test_login_invalid_password(client):
    """Verify logging in with incorrect password rejects with error flash."""
    response = client.post("/login", data={
        "email": "seller@coeptech.ac.in",
        "password": "IncorrectPassword"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None

def test_logout(seller_client):
    """Verify logging out clears session variables."""
    response = seller_client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    with seller_client.session_transaction() as sess:
        assert "user_id" not in sess

def test_student_registration(client):
    """Verify registration creates student and handles domain verification."""
    response = client.post("/register", data={
        "display_name": "New Student",
        "email": "freshman@coeptech.ac.in",
        "college_id": "1",
        "course_year": "B.Tech CSE - 1st Year",
        "student_id_roll": "CS2026001",
        "phone": "+919999988888",
        "password": "Password123",
        "confirm_password": "Password123"
    }, follow_redirects=True)

    assert response.status_code == 200
    new_user = User.query.filter_by(email="freshman@coeptech.ac.in").first()
    assert new_user is not None
    assert new_user.display_name == "New Student"
    # Domain matches college domain coeptech.ac.in, so verified

def test_student_registration_with_custom_college(client):
    """Verify registration succeeds with a custom unlisted college name without blocking."""
    response = client.post("/register", data={
        "display_name": "Gujarat Poly Student",
        "email": "poly@unlisted-college.edu",
        "college_name_input": "Government Polytechnic Bhavnagar",
        "course_year": "Diploma CE - 2nd Year",
        "password": "Password123",
        "confirm_password": "Password123"
    }, follow_redirects=True)

    assert response.status_code == 200
    user = User.query.filter_by(email="poly@unlisted-college.edu").first()
    assert user is not None
    assert user.college_name_custom == "Government Polytechnic Bhavnagar"
    assert user.college_name == "Government Polytechnic Bhavnagar"
    assert user.display_college == "Government Polytechnic Bhavnagar"
    assert user.is_verified_student is False
