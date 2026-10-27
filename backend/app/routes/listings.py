from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, session
from app.models import db, Listing, ListingImage, College, Report, User
from app.utils.auth import login_required, get_current_user
from app.utils.security import save_upload_image, rate_limiter, get_client_ip

listings_bp = Blueprint("listings", __name__)

CATEGORIES = [
    "Books & Study Notes",
    "Electronics & Laptops",
    "Lab Equipment & Coats",
    "Scientific Calculators",
    "Hostel Essentials & Appliances",
    "Engineering Drawing & Tools",
    "Cycles & Campus Mobility",
    "Miscellaneous",
]

CONDITIONS = ["New", "Like New", "Good", "Fair", "Needs Repair"]
LISTING_TYPES = ["For Sale", "Free", "Lend/Borrow"]

GUJARAT_CITIES = [
    "Ahmedabad", "Gandhinagar", "Surat", "Vadodara", "Rajkot", "Anand", "Mehsana", "Bhavnagar"
]

ALL_INDIAN_STATES = [
    "Gujarat", "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana",
    "Uttar Pradesh", "Rajasthan", "Madhya Pradesh", "West Bengal", "Punjab", "Haryana",
    "Kerala", "Andhra Pradesh", "Bihar", "Odisha", "Assam", "Goa", "Uttarakhand"
]

@listings_bp.route("/products")
def browse():
    """Browse catalog with filters, search, sorting, and pagination."""
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()
    selected_college_id = request.args.get("college_id", type=int)
    selected_college_name = request.args.get("college_name", "").strip() or request.args.get("college", "").strip()
    selected_condition = request.args.get("condition", "").strip()
    selected_listing_type = request.args.get("listing_type", "").strip()
    selected_state = request.args.get("state", "").strip()
    selected_city = request.args.get("city", "").strip()
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    sort_by = request.args.get("sort", "newest")

    # Default location awareness: if no specific query or all_locations requested
    if not selected_state and not selected_city and not request.args.get("all_locations"):
        selected_state = session.get("location_state", "Gujarat")
        selected_city = session.get("location_city", "")

    # Base query: approved items only
    query = Listing.query.filter(Listing.moderation_status == "Approved")
    query = query.filter(Listing.status.in_(["Available", "Reserved"]))

    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            (Listing.title.ilike(search_filter)) |
            (Listing.description.ilike(search_filter)) |
            (Listing.pickup_area.ilike(search_filter)) |
            (Listing.city.ilike(search_filter))
        )

    if selected_category and selected_category in CATEGORIES:
        query = query.filter(Listing.category == selected_category)

    if selected_college_id:
        query = query.filter(Listing.college_id == selected_college_id)
    elif selected_college_name and selected_college_name.lower() != "all":
        col_term = f"%{selected_college_name}%"
        query = query.outerjoin(College, Listing.college_id == College.id).filter(
            (Listing.college_name_custom.ilike(col_term)) |
            (College.name.ilike(col_term)) |
            (College.short_name.ilike(col_term))
        )

    if selected_condition:
        if selected_condition == "New":
            query = query.filter(Listing.condition.in_(["New", "Brand New"]))
        elif selected_condition in CONDITIONS or selected_condition == "Brand New":
            query = query.filter(Listing.condition == selected_condition)

    if selected_listing_type and selected_listing_type in LISTING_TYPES:
        query = query.filter(Listing.listing_type == selected_listing_type)

    if selected_state and selected_state != "All":
        query = query.filter(Listing.state == selected_state)

    if selected_city and selected_city != "All":
        query = query.filter(Listing.city == selected_city)

    if min_price is not None and min_price >= 0:
        query = query.filter(Listing.price >= min_price)

    if max_price is not None and max_price > 0:
        query = query.filter(Listing.price <= max_price)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(Listing.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Listing.price.desc())
    elif sort_by == "popular":
        query = query.order_by(Listing.view_count.desc())
    else:  # newest
        query = query.order_by(Listing.created_at.desc())

    # Pagination: 12 per page
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    listings = pagination.items

    colleges = College.query.order_by(College.name).all()

    # City & regional counts for location filter chips
    ahmedabad_count = Listing.query.filter_by(city="Ahmedabad", status="Available", moderation_status="Approved").count()
    gandhinagar_count = Listing.query.filter_by(city="Gandhinagar", status="Available", moderation_status="Approved").count()
    surat_count = Listing.query.filter_by(city="Surat", status="Available", moderation_status="Approved").count()
    vadodara_count = Listing.query.filter_by(city="Vadodara", status="Available", moderation_status="Approved").count()
    gujarat_count = Listing.query.filter_by(state="Gujarat", status="Available", moderation_status="Approved").count()
    all_india_count = Listing.query.filter(Listing.status.in_(["Available", "Reserved"]), Listing.moderation_status == "Approved").count()

    return render_template(
        "listings/browse.html",
        listings=listings,
        pagination=pagination,
        categories=CATEGORIES,
        conditions=CONDITIONS,
        listing_types=LISTING_TYPES,
        gujarat_cities=GUJARAT_CITIES,
        all_states=ALL_INDIAN_STATES,
        colleges=colleges,
        search_query=search_query,
        selected_category=selected_category,
        selected_college_id=selected_college_id,
        selected_college_name=selected_college_name,
        selected_condition=selected_condition,
        selected_listing_type=selected_listing_type,
        selected_state=selected_state,
        selected_city=selected_city,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        ahmedabad_count=ahmedabad_count,
        gandhinagar_count=gandhinagar_count,
        surat_count=surat_count,
        vadodara_count=vadodara_count,
        gujarat_count=gujarat_count,
        all_india_count=all_india_count,
        current_user=get_current_user()
    )

@listings_bp.route("/products/<int:listing_id>")
def detail(listing_id):
    """Product detail page with seller profile card, safe meeting spots, and CTAs."""
    listing = Listing.query.get_or_404(listing_id)

    user = get_current_user()
    if listing.moderation_status != "Approved" and (not user or (user.id != listing.seller_id and not user.is_admin)):
        abort(404)

    # Increment view count
    listing.view_count = (listing.view_count or 0) + 1
    db.session.commit()

    # Related items in the same category or college
    related_items = Listing.query.filter(
        Listing.category == listing.category,
        Listing.id != listing.id,
        Listing.status == "Available",
        Listing.moderation_status == "Approved"
    ).limit(4).all()

    # Seller's other listings
    seller_other_items = Listing.query.filter(
        Listing.seller_id == listing.seller_id,
        Listing.id != listing.id,
        Listing.status == "Available",
        Listing.moderation_status == "Approved"
    ).limit(3).all()

    return render_template(
        "listings/detail.html",
        listing=listing,
        related_items=related_items,
        seller_other_items=seller_other_items,
        current_user=user
    )

@listings_bp.route("/sell", methods=["GET", "POST"])
@login_required
def create():
    """Create a new listing (For Sale, Free Giveaway, or Peer Lending)."""
    user = get_current_user()
    colleges = College.query.order_by(College.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        condition = request.form.get("condition", "").strip()
        condition_notes = request.form.get("condition_notes", "").strip()
        listing_type = request.form.get("listing_type", "For Sale").strip()
        
        state = request.form.get("state", user.preferred_state or "Gujarat").strip()
        city = request.form.get("city", user.preferred_city or "Ahmedabad").strip()
        
        # Lending specific fields
        lend_duration = request.form.get("lend_duration", "").strip()
        lend_deposit_str = request.form.get("lend_deposit", "").strip()
        lend_terms = request.form.get("lend_terms", "").strip()

        # Pricing rules based on listing type
        price = 0
        if listing_type == "For Sale":
            price_val = request.form.get("price", type=int)
            if price_val is None or price_val <= 0:
                flash("Please specify a valid price in INR greater than ₹0 for items for sale.", "warning")
                return render_template("listings/create.html", categories=CATEGORIES, conditions=CONDITIONS, listing_types=LISTING_TYPES, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES, colleges=colleges, user=user)
            price = price_val
        elif listing_type == "Lend/Borrow":
            rental_fee = request.form.get("price", type=int)
            price = rental_fee if rental_fee is not None and rental_fee >= 0 else 0
        else:
            # Free giveaway
            price = 0

        original_price = request.form.get("original_price", type=int)
        
        # Flexible College input (suggestions or custom entry)
        college_input = (request.form.get("college_name_input") or request.form.get("college_name") or "").strip()
        college_id_raw = request.form.get("college_id", type=int)
        pickup_area = request.form.get("pickup_area", "").strip()

        resolved_college_id = college_id_raw
        resolved_custom_college = None

        if college_input:
            matched = College.query.filter(College.name.ilike(college_input)).first()
            if not matched:
                matched = College.query.filter(College.short_name.ilike(college_input)).first()
            if matched:
                resolved_college_id = matched.id
                resolved_custom_college = None
            else:
                resolved_custom_college = college_input
                resolved_college_id = college_id_raw or user.college_id or 1
        elif not resolved_college_id:
            resolved_college_id = user.college_id or 1
            resolved_custom_college = user.college_name_custom

        # Validation
        if not title or len(title) < 5:
            flash("Please enter a descriptive title (at least 5 characters).", "warning")
            return render_template("listings/create.html", categories=CATEGORIES, conditions=CONDITIONS, listing_types=LISTING_TYPES, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES, colleges=colleges, user=user)

        if not description or len(description) < 10:
            flash("Please provide a thorough item description (at least 10 characters).", "warning")
            return render_template("listings/create.html", categories=CATEGORIES, conditions=CONDITIONS, listing_types=LISTING_TYPES, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES, colleges=colleges, user=user)

        if not category or category not in CATEGORIES:
            flash("Please choose a valid category.", "warning")
            return render_template("listings/create.html", categories=CATEGORIES, conditions=CONDITIONS, listing_types=LISTING_TYPES, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES, colleges=colleges, user=user)

        allowed_conditions = set(CONDITIONS) | {"Brand New"}
        if not condition or condition not in allowed_conditions:
            flash("Please select the item's condition.", "warning")
            return render_template("listings/create.html", categories=CATEGORIES, conditions=CONDITIONS, listing_types=LISTING_TYPES, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES, colleges=colleges, user=user)

        if not pickup_area:
            pickup_area = "Campus Main Canteen or Library"

        lend_deposit = None
        if lend_deposit_str:
            try:
                lend_deposit = int(lend_deposit_str)
            except ValueError:
                lend_deposit = None

        listing = Listing(
            title=title,
            description=description,
            category=category,
            condition=condition,
            condition_notes=condition_notes or None,
            listing_type=listing_type,
            price=price,
            original_price=original_price if original_price and original_price > price else None,
            state=state,
            city=city,
            pickup_area=pickup_area,
            lend_duration=lend_duration if listing_type == "Lend/Borrow" else None,
            lend_deposit=lend_deposit if listing_type == "Lend/Borrow" else None,
            lend_terms=lend_terms if listing_type == "Lend/Borrow" else None,
            college_id=resolved_college_id,
            college_name_custom=resolved_custom_college,
            seller_id=user.id,
            status="Available",
            moderation_status="Approved",
            is_demo_sample=False
        )
        db.session.add(listing)
        db.session.flush()

        # Handle uploaded images with cover photo selection
        uploaded_files = request.files.getlist("images")
        primary_image_index = request.form.get("primary_image_index", type=int, default=0)
        saved_paths = []
        for f in uploaded_files:
            if f and f.filename:
                try:
                    rel_path = save_upload_image(f, subfolder="listings")
                    if rel_path:
                        saved_paths.append(rel_path)
                except ValueError as err:
                    flash(f"Image upload warning: {err}", "warning")

        if saved_paths:
            for idx, path in enumerate(saved_paths):
                is_cover = (idx == primary_image_index) or (primary_image_index >= len(saved_paths) and idx == 0)
                db.session.add(ListingImage(
                    listing_id=listing.id,
                    image_path=path,
                    is_primary=is_cover
                ))

        db.session.commit()
        flash("Your item is now live on Student Mart! Fellow campus students can now reach out.", "success")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    return render_template(
        "listings/create.html",
        categories=CATEGORIES,
        conditions=CONDITIONS,
        listing_types=LISTING_TYPES,
        gujarat_cities=GUJARAT_CITIES,
        all_states=ALL_INDIAN_STATES,
        colleges=colleges,
        user=user,
        current_user=user
    )

@listings_bp.route("/products/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit(listing_id):
    """Edit an existing listing (ownership enforced)."""
    listing = Listing.query.get_or_404(listing_id)
    user = get_current_user()

    if listing.seller_id != user.id and not user.is_admin:
        abort(403)

    colleges = College.query.order_by(College.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        condition = request.form.get("condition", "").strip()
        condition_notes = request.form.get("condition_notes", "").strip()
        listing_type = request.form.get("listing_type", listing.listing_type or "For Sale").strip()
        state = request.form.get("state", listing.state or "Gujarat").strip()
        city = request.form.get("city", listing.city or "Ahmedabad").strip()
        
        # College handling
        college_input = (request.form.get("college_name_input") or request.form.get("college_name") or "").strip()
        college_id_raw = request.form.get("college_id", type=int)

        if college_input:
            matched = College.query.filter(College.name.ilike(college_input)).first()
            if not matched:
                matched = College.query.filter(College.short_name.ilike(college_input)).first()
            if matched:
                listing.college_id = matched.id
                listing.college_name_custom = None
            else:
                listing.college_name_custom = college_input
                listing.college_id = college_id_raw or listing.college_id or 1
        elif college_id_raw:
            listing.college_id = college_id_raw
            listing.college_name_custom = None
        
        price = 0
        if listing_type == "For Sale":
            price_val = request.form.get("price", type=int)
            if price_val is None or price_val <= 0:
                flash("Price must be greater than ₹0 for items for sale.", "warning")
                return render_template("listings/edit.html", listing=listing, categories=CATEGORIES, conditions=CONDITIONS, listing_types=LISTING_TYPES, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES, colleges=colleges)
            price = price_val
        elif listing_type == "Lend/Borrow":
            rental_fee = request.form.get("price", type=int)
            price = rental_fee if rental_fee is not None and rental_fee >= 0 else 0
        else:
            price = 0

        original_price = request.form.get("original_price", type=int)
        pickup_area = request.form.get("pickup_area", "").strip()
        status = request.form.get("status", "Available")
        
        lend_duration = request.form.get("lend_duration", "").strip()
        lend_deposit_str = request.form.get("lend_deposit", "").strip()
        lend_terms = request.form.get("lend_terms", "").strip()

        if not title or len(title) < 5:
            flash("Title must be at least 5 characters.", "warning")
            return render_template("listings/edit.html", listing=listing, categories=CATEGORIES, conditions=CONDITIONS, listing_types=LISTING_TYPES, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES, colleges=colleges)

        listing.title = title
        listing.description = description
        listing.category = category
        listing.condition = condition
        listing.condition_notes = condition_notes or None
        listing.listing_type = listing_type
        listing.state = state
        listing.city = city
        listing.price = price
        listing.original_price = original_price if original_price and original_price > price else None
        listing.pickup_area = pickup_area
        if status in ["Available", "Reserved", "Sold"]:
            listing.status = status

        if listing_type == "Lend/Borrow":
            listing.lend_duration = lend_duration
            listing.lend_terms = lend_terms
            if lend_deposit_str:
                try:
                    listing.lend_deposit = int(lend_deposit_str)
                except ValueError:
                    listing.lend_deposit = None
        else:
            listing.lend_duration = None
            listing.lend_deposit = None
            listing.lend_terms = None

        # 1. Handle deletion of existing images
        delete_image_ids = request.form.getlist("delete_image_ids")
        for img_id_str in delete_image_ids:
            try:
                img_id = int(img_id_str)
                img_to_delete = ListingImage.query.filter_by(id=img_id, listing_id=listing.id).first()
                if img_to_delete:
                    db.session.delete(img_to_delete)
            except (ValueError, TypeError):
                pass
        db.session.flush()

        # 2. Handle primary cover selection among existing photos
        primary_existing_id = request.form.get("primary_existing_image_id", type=int)
        if primary_existing_id:
            for img in listing.images:
                img.is_primary = (img.id == primary_existing_id)

        # 3. Handle newly uploaded images
        uploaded_files = request.files.getlist("images")
        newly_added = []
        for f in uploaded_files:
            if f and f.filename:
                try:
                    rel_path = save_upload_image(f, subfolder="listings")
                    if rel_path:
                        new_img = ListingImage(listing_id=listing.id, image_path=rel_path, is_primary=False)
                        db.session.add(new_img)
                        newly_added.append(new_img)
                except ValueError as err:
                    flash(f"Image warning: {err}", "warning")
        db.session.flush()

        # 4. Ensure at least one remaining image is primary if images exist
        all_imgs = ListingImage.query.filter_by(listing_id=listing.id).all()
        if all_imgs and not any(im.is_primary for im in all_imgs):
            all_imgs[0].is_primary = True

        db.session.commit()
        flash("Listing updated successfully.", "success")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    return render_template(
        "listings/edit.html",
        listing=listing,
        categories=CATEGORIES,
        conditions=CONDITIONS,
        listing_types=LISTING_TYPES,
        gujarat_cities=GUJARAT_CITIES,
        all_states=ALL_INDIAN_STATES,
        colleges=colleges,
        current_user=user
    )

@listings_bp.route("/products/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete(listing_id):
    """Delete a listing (ownership enforced)."""
    listing = Listing.query.get_or_404(listing_id)
    user = get_current_user()

    if listing.seller_id != user.id and not user.is_admin:
        abort(403)

    db.session.delete(listing)
    db.session.commit()
    flash("Your listing has been removed.", "info")
    return redirect(url_for("listings.my_listings"))

@listings_bp.route("/products/<int:listing_id>/status", methods=["POST"])
@login_required
def toggle_status(listing_id):
    """Toggle status between Available, Reserved, and Sold."""
    listing = Listing.query.get_or_404(listing_id)
    user = get_current_user()

    if listing.seller_id != user.id and not user.is_admin:
        abort(403)

    new_status = request.form.get("status")
    if new_status in ["Available", "Reserved", "Sold"]:
        listing.status = new_status
        db.session.commit()
        flash(f"Listing status updated to '{new_status}'.", "success")

    return redirect(request.referrer or url_for("listings.my_listings"))

@listings_bp.route("/my-listings")
@login_required
def my_listings():
    """Seller dashboard with tabs for active, reserved, and sold listings."""
    user = get_current_user()
    active_items = Listing.query.filter_by(seller_id=user.id, status="Available").order_by(Listing.created_at.desc()).all()
    reserved_items = Listing.query.filter_by(seller_id=user.id, status="Reserved").order_by(Listing.created_at.desc()).all()
    sold_items = Listing.query.filter_by(seller_id=user.id, status="Sold").order_by(Listing.created_at.desc()).all()

    return render_template(
        "listings/my_listings.html",
        active_items=active_items,
        reserved_items=reserved_items,
        sold_items=sold_items,
        current_user=user
    )

@listings_bp.route("/products/<int:listing_id>/report", methods=["POST"])
@login_required
def report_listing(listing_id):
    """Submit a Trust & Safety report for a listing."""
    listing = Listing.query.get_or_404(listing_id)
    user = get_current_user()

    reason = request.form.get("reason", "").strip()
    details = request.form.get("details", "").strip()

    if not reason or not details:
        flash("Please provide a reason and description for your report.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing_id))

    report = Report(
        reporter_id=user.id,
        listing_id=listing.id,
        reported_user_id=listing.seller_id,
        reason=reason,
        details=details,
        status="PENDING"
    )
    db.session.add(report)
    db.session.commit()

    flash("Thank you for looking out for campus safety. The moderation team has received your report and will review it promptly.", "info")
    return redirect(url_for("listings.detail", listing_id=listing_id))
