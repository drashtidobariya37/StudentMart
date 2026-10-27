from app.models import Listing

def test_browse_listings_page(client):
    """Verify catalog displays active listings."""
    response = client.get("/products")
    assert response.status_code == 200
    assert b"B.S. Grewal Higher Engineering Mathematics" in response.data

def test_create_listing_success(seller_client):
    """Verify logged-in student can create a new listing."""
    response = seller_client.post("/sell", data={
        "title": "Casio fx-991EX Scientific Calculator",
        "description": "552 functions approved for all SPPU engineering exams.",
        "category": "Scientific Calculators",
        "condition": "Like New",
        "price": "750",
        "original_price": "1495",
        "college_id": "1",
        "pickup_area": "Main Canteen"
    }, follow_redirects=True)

    assert response.status_code == 200
    new_item = Listing.query.filter_by(title="Casio fx-991EX Scientific Calculator").first()
    assert new_item is not None
    assert new_item.price == 750
    assert new_item.status == "Available"

def test_create_listing_validation_invalid_price(seller_client):
    """Verify listing creation fails with invalid or non-positive price."""
    response = seller_client.post("/sell", data={
        "title": "Broken Draft Tool",
        "description": "Some description that is long enough.",
        "category": "Engineering Drawing & Tools",
        "condition": "Good",
        "price": "-50",  # Invalid price
        "college_id": "1",
        "pickup_area": "Library"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Please specify a valid price" in response.data

def test_edit_listing_ownership_authorization(buyer_client):
    """Verify a student CANNOT edit another user's listing (403 Forbidden)."""
    # Listing 1 belongs to Seller, not Buyer
    response = buyer_client.get("/products/1/edit")
    assert response.status_code == 403

def test_edit_listing_owner_allowed(seller_client):
    """Verify owner can edit their listing."""
    response = seller_client.post("/products/1/edit", data={
        "title": "B.S. Grewal Higher Engineering Mathematics (Updated)",
        "description": "Updated description with all formulas included.",
        "category": "Books & Study Notes",
        "condition": "Like New",
        "price": "420",
        "original_price": "950",
        "pickup_area": "Library Lawn",
        "status": "Available"
    }, follow_redirects=True)

    assert response.status_code == 200
    listing = Listing.query.get(1)
    assert listing.price == 420
    assert "Updated" in listing.title

def test_filter_listings_by_category(client):
    """Verify filtering by category returns matching items only."""
    response = client.get("/products?category=Books+%26+Study+Notes")
    assert response.status_code == 200
    assert b"B.S. Grewal" in response.data

    # Filter with an unrelated category
    response2 = client.get("/products?category=Cycles+%26+Campus+Mobility")
    assert response2.status_code == 200
    assert b"No campus items found" in response2.data

def test_create_listing_with_custom_college_and_condition_notes(seller_client):
    """Verify listing creation supports unlisted custom college and condition notes."""
    response = seller_client.post("/sell", data={
        "title": "Mini Drafter with Sheet Tube (Needs Pivot Knob)",
        "description": "Omega mini drafter for first-year engineering drawing practicals.",
        "category": "Engineering Drawing & Tools",
        "condition": "Needs Repair",
        "condition_notes": "Lock knob is loose; requires M4 screw replacement. Scales intact without cracks.",
        "price": "250",
        "college_name_input": "Shantilal Shah Engineering College, Bhavnagar",
        "pickup_area": "Mechanical Workshop Gate"
    }, follow_redirects=True)

    assert response.status_code == 200
    item = Listing.query.filter_by(title="Mini Drafter with Sheet Tube (Needs Pivot Knob)").first()
    assert item is not None
    assert item.condition == "Needs Repair"
    assert "Lock knob is loose" in item.condition_notes
    assert item.college_name_custom == "Shantilal Shah Engineering College, Bhavnagar"
    assert item.display_college == "Shantilal Shah Engineering College, Bhavnagar"
    # Fallback placeholder is no-photo when seller provided no photos
    assert "no-photo.svg" in item.primary_image_url

def test_filter_listings_by_custom_college(client, seller_client):
    """Verify browse filter matches user-typed college names."""
    # Ensure item with custom college exists
    seller_client.post("/sell", data={
        "title": "Unique Physics Lab Manual for Bhavnagar College",
        "description": "Lab manual with all experiments performed and verified by faculty.",
        "category": "Books & Study Notes",
        "condition": "Good",
        "price": "120",
        "college_name_input": "GEC Bhavnagar Campus",
        "pickup_area": "Physics Lab"
    }, follow_redirects=True)

    # Filter with college search
    response = client.get("/products?college_name=Bhavnagar")
    assert response.status_code == 200
    assert b"Unique Physics Lab Manual" in response.data

def test_filter_listings_by_needs_repair_condition(client, seller_client):
    """Verify condition filter works for 'Needs Repair' and standard conditions."""
    response = client.get("/products?condition=Needs+Repair")
    assert response.status_code == 200
    assert b"Needs Repair" in response.data
