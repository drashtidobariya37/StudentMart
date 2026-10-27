"""
Student Mart - Database Seeder
Populates verified Gujarat campuses (Ahmedabad, Gandhinagar, Surat, Vadodara, Anand) alongside national universities,
realistic student accounts, authentic campus items (For Sale, Free Giveaways, Lend/Borrow),
active Urgent Need requests with student help offers, notifications, chat threads, and escrow orders.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.models import (
    db, College, User, Listing, ListingImage, UrgentRequest, UrgentOffer,
    Notification, Conversation, Message, Order, PaymentRecord, Report
)

def populate_seed_records(app=None):
    """Populates initial colleges, demo accounts, sample listings, and urgent requests."""
    if app is None:
        app = create_app()
    with app.app_context():
        print("[1/7] Seeding Gujarat Priority & National College Campuses...")
        colleges_data = [
            # Gujarat Campuses (Ahmedabad & Gandhinagar Focus)
            {
                "name": "Nirma University, Ahmedabad",
                "short_name": "Nirma Univ",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "domain": "nirmauni.ac.in",
                "campus_zones": "Student Activity Centre (SAC), Central Library Porch, Canteen Lawn, Technology Block Quad"
            },
            {
                "name": "DA-IICT (Dhirubhai Ambani Institute of ICT), Gandhinagar",
                "short_name": "DA-IICT",
                "city": "Gandhinagar",
                "state": "Gujarat",
                "domain": "daiict.ac.in",
                "campus_zones": "Resource Centre Entrance, Cafeteria Quadrangle, Lab Building 1, Open Air Theatre"
            },
            {
                "name": "IIT Gandhinagar (IITGn), Palaj",
                "short_name": "IIT Gandhinagar",
                "city": "Gandhinagar",
                "state": "Gujarat",
                "domain": "iitgn.ac.in",
                "campus_zones": "Central Arcade, Student Mess Lawn, Academic Block 4 Canteen, Gate 1 Security"
            },
            {
                "name": "PDEU (Pandit Deendayal Energy University), Gandhinagar",
                "short_name": "PDEU",
                "city": "Gandhinagar",
                "state": "Gujarat",
                "domain": "pdeu.ac.in",
                "campus_zones": "Performing Arts Block, Central Library, High Rise Hostel Gate, Food Court"
            },
            {
                "name": "L.D. College of Engineering (LDCE), Ahmedabad",
                "short_name": "LDCE Ahmedabad",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "domain": "ldce.ac.in",
                "campus_zones": "Main Building Porch, Central Library Steps, Canteen Lawn, Mechanical Workshop"
            },
            {
                "name": "Vishwakarma Government Engineering College (VGEC), Chandkheda",
                "short_name": "VGEC Ahmedabad",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "domain": "vgecg.ac.in",
                "campus_zones": "Admin Block Quadrangle, Department of Computer Engg, Main Canteen, Library Gate"
            },
            {
                "name": "Ahmedabad University (AU), Navrangpura",
                "short_name": "Ahmedabad Univ",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "domain": "ahduni.edu.in",
                "campus_zones": "University Centre Plaza, GICT Building, Library Steps, Amrut Mody School"
            },
            {
                "name": "Maharaja Sayajirao University of Baroda (MSU), Vadodara",
                "short_name": "MSU Baroda",
                "city": "Vadodara",
                "state": "Gujarat",
                "domain": "msubaroda.ac.in",
                "campus_zones": "Faculty of Tech & Engg Dome, Hansa Mehta Library, Kalabhavan Canteen, Pavate Hall"
            },
            {
                "name": "SVNIT (Sardar Vallabhbhai National Institute of Tech), Surat",
                "short_name": "SVNIT Surat",
                "city": "Surat",
                "state": "Gujarat",
                "domain": "svnit.ac.in",
                "campus_zones": "Student Activity Center (SAC), Central Library Lawn, Mega Hostel Mess, Main Gate"
            },
            {
                "name": "BVM Engineering College, Vallabh Vidyanagar, Anand",
                "short_name": "BVM Anand",
                "city": "Anand",
                "state": "Gujarat",
                "domain": "bvmengineering.ac.in",
                "campus_zones": "Main Academic Quadrangle, Central Library, Moti Canteen, Hostel Block B"
            },
            # National Reference Campuses
            {
                "name": "IIT Bombay, Powai",
                "short_name": "IIT Bombay",
                "city": "Mumbai",
                "state": "Maharashtra",
                "domain": "iitb.ac.in",
                "campus_zones": "Student Activity Center (SAC), Main Gate Security, Central Library Lawn, Hostel 12 Mess"
            },
            {
                "name": "COEP Technological University, Pune",
                "short_name": "COEP Tech",
                "city": "Pune",
                "state": "Maharashtra",
                "domain": "coeptech.ac.in",
                "campus_zones": "Central Library Steps, Main Boat Club Canteen, Academic Complex Quadrangle"
            },
            {
                "name": "RV College of Engineering, Bengaluru",
                "short_name": "RVCE",
                "city": "Bengaluru",
                "state": "Karnataka",
                "domain": "rvce.edu.in",
                "campus_zones": "Krishna Block Canteen, Central Library Portico, Sports Complex Entrance"
            },
            {
                "name": "Delhi Technological University (DTU), Delhi",
                "short_name": "DTU",
                "city": "New Delhi",
                "state": "Delhi",
                "domain": "dtu.ac.in",
                "campus_zones": "Mech Canteen, Open Air Theatre (OAT), Central Library Plaza"
            }
        ]

        colleges = {}
        for cdata in colleges_data:
            col = College(**cdata)
            db.session.add(col)
            colleges[cdata["short_name"]] = col
        db.session.commit()

        print("[2/7] Seeding Verified Gujarat & National Student Accounts...")
        # 1. Administrator
        admin = User(
            email="admin@studentmart.campus",
            display_name="Platform Admin",
            college_id=colleges["Nirma Univ"].id,
            course_year="Faculty Advisor / Chief Moderator",
            student_id_roll="ADMIN-001",
            phone="+919876500001",
            preferred_state="Gujarat",
            preferred_city="Ahmedabad",
            is_verified_student=True,
            is_email_verified=True,
            is_google_authenticated=False,
            is_admin=True
        )
        admin.set_password("Admin@123")
        db.session.add(admin)

        # 2. Gujarat Seller: Aarav Sharma (Nirma University, Ahmedabad)
        seller_aarav = User(
            email="aarav.sharma@nirmauni.ac.in",
            display_name="Aarav Sharma",
            college_id=colleges["Nirma Univ"].id,
            course_year="B.Tech Computer Engg - 3rd Year",
            student_id_roll="22BCE145",
            phone="+919876510001",
            preferred_state="Gujarat",
            preferred_city="Ahmedabad",
            bio="3rd year CS student at Nirma University. Sharing previous semester GTU math books, drafters, and hostel appliances.",
            is_verified_student=True,
            is_email_verified=True,
            is_google_authenticated=False,
            is_admin=False
        )
        seller_aarav.set_password("Student@123")
        db.session.add(seller_aarav)

        # 3. Gujarat Buyer: Sneha Patel (DA-IICT, Gandhinagar)
        buyer_sneha = User(
            email="sneha.patel@daiict.ac.in",
            display_name="Sneha Patel",
            college_id=colleges["DA-IICT"].id,
            course_year="B.Tech ICT - 2nd Year",
            student_id_roll="202301089",
            phone="+919876520002",
            preferred_state="Gujarat",
            preferred_city="Gandhinagar",
            bio="2nd year ICT student at DA-IICT Gandhinagar. Always looking for scientific calculators, notes, and lab components.",
            is_verified_student=True,
            is_email_verified=True,
            is_google_authenticated=False,
            is_admin=False
        )
        buyer_sneha.set_password("Student@123")
        db.session.add(buyer_sneha)

        # 4. Gujarat Student: Rohit Mehta (LDCE, Ahmedabad)
        student_rohit = User(
            email="rohit.mehta@ldce.ac.in",
            display_name="Rohit Mehta",
            college_id=colleges["LDCE Ahmedabad"].id,
            course_year="B.E. Mechanical Engg - 3rd Year",
            student_id_roll="210280119042",
            phone="+919876530003",
            preferred_state="Gujarat",
            preferred_city="Ahmedabad",
            bio="Mechanical Engineering student at LDCE. Happy to lend drafters and workshop kits to juniors.",
            is_verified_student=True,
            is_email_verified=True,
            is_google_authenticated=False,
            is_admin=False
        )
        student_rohit.set_password("Student@123")
        db.session.add(student_rohit)

        # 5. Gujarat Student: Priya Desai (IIT Gandhinagar)
        student_priya = User(
            email="priya.desai@iitgn.ac.in",
            display_name="Priya Desai",
            college_id=colleges["IIT Gandhinagar"].id,
            course_year="B.Tech Electrical Engg - 4th Year",
            student_id_roll="20110145",
            phone="+919876540004",
            preferred_state="Gujarat",
            preferred_city="Gandhinagar",
            bio="Final year EE student at IIT Gandhinagar. Graduating soon and passing down hostel gear and lab coats.",
            is_verified_student=True,
            is_email_verified=True,
            is_google_authenticated=False,
            is_admin=False
        )
        student_priya.set_password("Student@123")
        db.session.add(student_priya)

        # 6. Gujarat Student: Tanvi Joshi (MSU Baroda, Vadodara)
        student_tanvi = User(
            email="tanvi.joshi@msubaroda.ac.in",
            display_name="Tanvi Joshi",
            college_id=colleges["MSU Baroda"].id,
            course_year="B.E. Civil Engg - 2nd Year",
            student_id_roll="MSU22CV054",
            phone="+919876550005",
            preferred_state="Gujarat",
            preferred_city="Vadodara",
            bio="Civil Engineering student at Faculty of Tech & Engg, MSU Baroda. Friendly campus lender.",
            is_verified_student=True,
            is_email_verified=True,
            is_google_authenticated=False,
            is_admin=False
        )
        student_tanvi.set_password("Student@123")
        db.session.add(student_tanvi)

        # 7. National Student: Rohan Verma (IIT Bombay)
        student_rohan = User(
            email="rohan.verma@iitb.ac.in",
            display_name="Rohan Verma",
            college_id=colleges["IIT Bombay"].id,
            course_year="B.Tech Computer Science - 3rd Year",
            student_id_roll="210050089",
            phone="+919876560006",
            preferred_state="Maharashtra",
            preferred_city="Mumbai",
            bio="IIT Bombay CSE student. Sharing advanced reference books and electronics accessories.",
            is_verified_student=True,
            is_email_verified=True,
            is_google_authenticated=False,
            is_admin=False
        )
        student_rohan.set_password("Student@123")
        db.session.add(student_rohan)

        db.session.commit()

        print("[3/7] Seeding Authentic Gujarat & National Marketplace Listings...")
        listings_seed = [
            # 1. Casio Calculator (Ahmedabad - Nirma)
            {
                "title": "Casio fx-991EX ClassWiz Non-Programmable Scientific Calculator",
                "description": (
                    "Original Casio fx-991EX scientific calculator with natural textbook display. "
                    "Features 552 functions, matrix, equation, and vector calculations. "
                    "Permitted in GTU, Nirma University, and Gujarat semester engineering examinations. "
                    "Clean condition with hard protective slide-on cover, fresh solar battery, and original quick reference card."
                ),
                "listing_type": "For Sale",
                "price": 750,
                "original_price": 1495,
                "category": "Scientific Calculators",
                "condition": "Like New",
                "seller": seller_aarav,
                "college": colleges["Nirma Univ"],
                "state": "Gujarat",
                "city": "Ahmedabad",
                "pickup_area": "Technology Block Canteen or SAC steps",
                "placeholder_img": "img/products/calculator.jpg",
                "status": "Available",
                "view_count": 52
            },
            # 2. B.S. Grewal Math Textbook (Gandhinagar - DA-IICT)
            {
                "title": "Higher Engineering Mathematics by Dr. B.S. Grewal (44th Edition)",
                "description": (
                    "Standard engineering mathematics reference textbook covering differential equations, Laplace transforms, "
                    "linear algebra, numerical techniques, and complex variables. "
                    "44th revised edition. Clean binding, zero torn pages, neat pencil notes in Unit 2 only. "
                    "Essential textbook for GTU and Indian autonomous engineering universities."
                ),
                "listing_type": "For Sale",
                "price": 450,
                "original_price": 950,
                "category": "Books & Study Notes",
                "condition": "Good",
                "seller": buyer_sneha,
                "college": colleges["DA-IICT"],
                "state": "Gujarat",
                "city": "Gandhinagar",
                "pickup_area": "Resource Centre Entrance or Cafeteria Lawn",
                "placeholder_img": "img/products/maths-book.jpg",
                "status": "Available",
                "view_count": 89
            },
            # 3. GTU 5th Sem DBMS Exam Notes (Ahmedabad - LDCE) -> FREE GIVEAWAY
            {
                "title": "GTU 5th Sem Computer Engineering DBMS Handwritten Notes & Question Bank",
                "description": (
                    "Complete handwritten semester notes for Database Management Systems (DBMS). "
                    "Includes ER-diagrams, Relational Algebra, SQL queries, Normalization (1NF to BCNF) with solved examples, "
                    "and previous 5 years GTU solved question papers. Cleanly handwritten in A4 spiral register. "
                    "Giving away for free to support junior batch students preparing for university exams!"
                ),
                "listing_type": "Free",
                "price": 0,
                "original_price": 300,
                "category": "Books & Study Notes",
                "condition": "Like New",
                "seller": student_rohit,
                "college": colleges["LDCE Ahmedabad"],
                "state": "Gujarat",
                "city": "Ahmedabad",
                "pickup_area": "Central Library Steps or Mech Workshop Porch",
                "placeholder_img": "img/products/notes-dbms.jpg",
                "status": "Available",
                "view_count": 115
            },
            # 4. Engineering Mini Drafter (Ahmedabad - VGEC) -> LEND / BORROW
            {
                "title": "Omega Precision Mini Drafter with Sheet Tube (Exam Week Borrowing)",
                "description": (
                    "Heavy duty engineering drawing mini drafter with steel rod mechanism and transparent acrylic scale. "
                    "Comes with waterproof drawing sheet container tube. "
                    "Available for peer lending during mid-sem or end-sem exam practicals. "
                    "Return expected in intact scratch-free condition with original knobs intact."
                ),
                "listing_type": "Lend/Borrow",
                "price": 50,  # token fee
                "original_price": 850,
                "lend_duration": "1 week / Exam duration",
                "lend_deposit": 400,
                "lend_terms": "Deposit returned immediately upon safe return after practical. Keep sheet clips safe.",
                "category": "Engineering Drawing & Tools",
                "condition": "Like New",
                "seller": seller_aarav,
                "college": colleges["VGEC Ahmedabad"],
                "state": "Gujarat",
                "city": "Ahmedabad",
                "pickup_area": "Department of Computer Engg or Main Canteen",
                "placeholder_img": "img/products/drafter.jpg",
                "status": "Available",
                "view_count": 42
            },
            # 5. Lab Coat with Safety Goggles (Gandhinagar - IITGn)
            {
                "title": "White Cotton Chemistry & Physics Lab Coat (Size L) with Safety Goggles",
                "description": (
                    "Standard unisex full-sleeve laboratory coat made of 100% thick white cotton with three utility pockets. "
                    "Size Large (Chest 42 inches). Washed, sanitized, and neatly pressed. "
                    "Includes a transparent anti-fog laboratory safety goggle. Mandatory for chemistry and workshop practicals."
                ),
                "listing_type": "For Sale",
                "price": 220,
                "original_price": 500,
                "category": "Lab Equipment & Coats",
                "condition": "Good",
                "seller": student_priya,
                "college": colleges["IIT Gandhinagar"],
                "state": "Gujarat",
                "city": "Gandhinagar",
                "pickup_area": "Academic Block 4 Canteen or Central Arcade",
                "placeholder_img": "img/products/lab-coat.jpg",
                "status": "Available",
                "view_count": 67
            },
            # 6. Arduino Starter Kit (Gandhinagar - DA-IICT)
            {
                "title": "Arduino Uno R3 Starter Kit with Breadboard, Sensors & Jumper Wires",
                "description": (
                    "Complete embedded systems project kit including genuine ATmega328P Arduino Uno R3, "
                    "830-point solderless breadboard, ultrasonic sensor HC-SR04, servo motor SG90, 16x2 I2C LCD, "
                    "DHT11 temperature sensor, LEDs, resistors, and 65 male-female jumper wires. "
                    "Perfect for IoT, Microcontroller (MCU) lab, and third-year minor capstone projects."
                ),
                "listing_type": "For Sale",
                "price": 850,
                "original_price": 1800,
                "category": "Electronics & Laptops",
                "condition": "Like New",
                "seller": buyer_sneha,
                "college": colleges["DA-IICT"],
                "state": "Gujarat",
                "city": "Gandhinagar",
                "pickup_area": "Resource Centre Entrance",
                "placeholder_img": "img/products/arduino.jpg",
                "status": "Available",
                "view_count": 94
            },
            # 7. Hostel Kettle & Study Lamp (Ahmedabad - Nirma)
            {
                "title": "Prestige 1.5L Stainless Steel Electric Kettle & LED Desk Study Lamp",
                "description": (
                    "Automatic shut-off electric kettle (1500W, 1.5 Litres) suitable for tea, instant Maggi, and boiling water in hostel rooms. "
                    "Includes an eye-friendly 3-brightness touch LED study lamp with flexible neck and USB rechargeable battery. "
                    "Both appliances tested and in working condition. Used for 1 year in Nirma Boys Hostel."
                ),
                "listing_type": "For Sale",
                "price": 600,
                "original_price": 1450,
                "category": "Hostel Essentials & Appliances",
                "condition": "Good",
                "seller": seller_aarav,
                "college": colleges["Nirma Univ"],
                "state": "Gujarat",
                "city": "Ahmedabad",
                "pickup_area": "Hostel Gate 1 or Student Activity Centre",
                "placeholder_img": "img/products/kettle-lamp.jpg",
                "status": "Available",
                "view_count": 55
            },
            # 8. Digital Multimeter (Surat - SVNIT) -> LEND / BORROW
            {
                "title": "Mastech Digital Multimeter with Needle Probes & Continuity Buzzer",
                "description": (
                    "High accuracy autoranging digital multimeter for electrical and electronics labs. "
                    "Measures AC/DC voltage, current, resistance, capacitance, diode check, and audio continuity test. "
                    "Available for peer borrowing for senior project circuit debugging and circuit testing."
                ),
                "listing_type": "Lend/Borrow",
                "price": 0,  # Free peer lend
                "original_price": 750,
                "lend_duration": "3 days / Project weekend",
                "lend_deposit": 300,
                "lend_terms": "Please handle probes carefully and do not short high voltage lines. Return with 9V battery intact.",
                "category": "Lab Equipment & Coats",
                "condition": "Good",
                "seller": student_rohit,
                "college": colleges["SVNIT Surat"],
                "state": "Gujarat",
                "city": "Surat",
                "pickup_area": "Student Activity Center (SAC)",
                "placeholder_img": "img/products/multimeter.jpg",
                "status": "Available",
                "view_count": 31
            },
            # 9. Operating Systems Dinosaur Book (Ahmedabad - AU)
            {
                "title": "Operating System Concepts by Silberschatz, Galvin & Gagne (9th Edition)",
                "description": (
                    "The gold standard OS textbook for Computer Science engineering courses. "
                    "Covers processes, threads, CPU scheduling, synchronization, deadlocks, memory management, and file systems. "
                    "Very clean condition with no water damage. Essential for GATE CSE and university exams."
                ),
                "listing_type": "For Sale",
                "price": 500,
                "original_price": 1100,
                "category": "Books & Study Notes",
                "condition": "Good",
                "seller": student_rohit,
                "college": colleges["Ahmedabad Univ"],
                "state": "Gujarat",
                "city": "Ahmedabad",
                "pickup_area": "University Centre Plaza",
                "placeholder_img": "img/products/os-book.jpg",
                "status": "Available",
                "view_count": 48
            },
            # 10. Campus Bicycle (Gandhinagar - PDEU)
            {
                "title": "Hero Sprint 26T Single Speed Campus Bicycle with Cable Lock",
                "description": (
                    "Comfortable campus commuter bicycle with rigid steel frame, side stand, front basket, and bell. "
                    "Tires in good condition, recently serviced brakes. Comes with a 4-digit number combination steel cable lock. "
                    "Ideal for commuting between PDEU hostels and academic blocks."
                ),
                "listing_type": "For Sale",
                "price": 1800,
                "original_price": 4500,
                "category": "Cycles & Campus Mobility",
                "condition": "Good",
                "seller": student_priya,
                "college": colleges["PDEU"],
                "state": "Gujarat",
                "city": "Gandhinagar",
                "pickup_area": "High Rise Hostel Gate or Performing Arts Block",
                "placeholder_img": "img/products/bicycle.jpg",
                "status": "Available",
                "view_count": 78
            },
            # 11. National Listing (IIT Bombay)
            {
                "title": "Introduction to Algorithms by Cormen, Leiserson, Rivest, Stein (CLRS 3rd Ed)",
                "description": (
                    "The comprehensive algorithmic bible. Covers asymptotic notation, divide-and-conquer, dynamic programming, "
                    "greedy algorithms, B-trees, graph algorithms, NP-completeness. Hardcover Indian edition in pristine condition."
                ),
                "listing_type": "For Sale",
                "price": 650,
                "original_price": 1395,
                "category": "Books & Study Notes",
                "condition": "Like New",
                "seller": student_rohan,
                "college": colleges["IIT Bombay"],
                "state": "Maharashtra",
                "city": "Mumbai",
                "pickup_area": "Central Library Lawn or Hostel 12 Mess",
                "placeholder_img": "img/products/algorithms-book.jpg",
                "status": "Available",
                "view_count": 130
            }
        ]

        created_listings = []
        for ldata in listings_seed:
            placeholder_img = ldata.pop("placeholder_img")
            listing = Listing(
                is_demo_sample=True,
                moderation_status="Approved",
                **ldata
            )
            db.session.add(listing)
            db.session.flush()

            img = ListingImage(
                listing_id=listing.id,
                image_path=placeholder_img,
                is_primary=True
            )
            db.session.add(img)
            created_listings.append(listing)

        db.session.commit()

        print("[4/7] Seeding Functional Urgent Need Requests (Gujarat & India)...")
        now = datetime.utcnow()
        urgent_seed = [
            # 1. Critical Need: Casio Calculator within 1 hour (Ahmedabad)
            {
                "user": student_rohit,
                "college": colleges["LDCE Ahmedabad"],
                "title": "Need Casio fx-991EX Calculator for GTU Practical Exam at 11 AM",
                "description": (
                    "My scientific calculator stopped working right before our 11 AM GTU practical exam today! "
                    "Need a working Casio fx-991EX or 991MS for 2 hours in Block 3. "
                    "Will return immediately after the exam in perfect condition. Can pay rental fee or return with snacks!"
                ),
                "category": "Scientific Calculators",
                "quantity": 1,
                "urgency": "Within 1 hour",
                "state": "Gujarat",
                "city": "Ahmedabad",
                "college_name_custom": "LDCE Ahmedabad",
                "budget": 100,
                "preferred_pickup": "Central Library steps or Block 3 entrance",
                "status": "Active",
                "moderation_status": "Approved",
                "is_demo_sample": True,
                "expires_at": now + timedelta(minutes=50)
            },
            # 2. Urgent Need: White Lab Coat Today (Gandhinagar)
            {
                "user": student_priya,
                "college": colleges["IIT Gandhinagar"],
                "title": "Urgently need White Cotton Lab Coat (Size M or L) for Chemistry Lab today",
                "description": (
                    "Forgot my lab coat back in my home city. Lab instructor has strict rules and won't allow practical entry at 2:30 PM without one. "
                    "Looking to borrow or buy second-hand immediately."
                ),
                "category": "Lab Equipment & Coats",
                "quantity": 1,
                "urgency": "Today",
                "state": "Gujarat",
                "city": "Gandhinagar",
                "college_name_custom": "IIT Gandhinagar",
                "budget": 150,
                "preferred_pickup": "Academic Block 4 Canteen",
                "status": "Active",
                "moderation_status": "Approved",
                "is_demo_sample": True,
                "expires_at": now + timedelta(hours=4)
            },
            # 3. Urgent Need: Notes for Tomorrow Exam (Ahmedabad)
            {
                "user": seller_aarav,
                "college": colleges["Nirma Univ"],
                "title": "Need 5th Sem Computer Engineering DBMS Question Bank & Notes for Tomorrow",
                "description": (
                    "Preparing for tomorrow's mid-sem test. Looking for handwritten notes or xerox question bank for Modules 3 and 4 (Transactions & Normalization). "
                    "Seeking friendly peer borrow or quick photocopy."
                ),
                "category": "Books & Study Notes",
                "quantity": 1,
                "urgency": "Tomorrow",
                "state": "Gujarat",
                "city": "Ahmedabad",
                "college_name_custom": "Nirma University",
                "budget": 0,  # Free help
                "preferred_pickup": "Nirma SAC Lawn or Technology Canteen",
                "status": "Active",
                "moderation_status": "Approved",
                "is_demo_sample": True,
                "expires_at": now + timedelta(hours=22)
            },
            # 4. Urgent Need: 65W Laptop Charger (Gandhinagar)
            {
                "user": buyer_sneha,
                "college": colleges["DA-IICT"],
                "title": "Urgent: Lenovo 65W Type-C Laptop Charger for Capstone Presentation",
                "description": (
                    "My laptop battery is at 12% and our capstone demo is scheduled at 4:30 PM today in Lab 2. "
                    "Need a 65W USB Type-C compatible charger to borrow for 2-3 hours."
                ),
                "category": "Electronics & Laptops",
                "quantity": 1,
                "urgency": "Today",
                "state": "Gujarat",
                "city": "Gandhinagar",
                "college_name_custom": "DA-IICT Gandhinagar",
                "budget": 100,
                "preferred_pickup": "Resource Centre Entrance",
                "status": "Active",
                "moderation_status": "Approved",
                "is_demo_sample": True,
                "expires_at": now + timedelta(hours=5)
            }
        ]

        created_urgent = []
        for udata in urgent_seed:
            u_user = udata.pop("user")
            req = UrgentRequest(user_id=u_user.id, **udata)
            db.session.add(req)
            db.session.flush()
            created_urgent.append(req)

        # Add a student offer to the first urgent request
        sample_offer = UrgentOffer(
            urgent_request_id=created_urgent[0].id,
            responder_id=seller_aarav.id,
            message="Hi Rohit! I am near the Central Library with my Casio 991EX. I can hand it to you in 5 minutes at the library porch. Take good care of it!",
            price_offered=50,
            is_free_help=False,
            pickup_suggestion="Central Library porch",
            status="Pending"
        )
        db.session.add(sample_offer)

        # In-app notification for the requester
        notif1 = Notification(
            user_id=student_rohit.id,
            title="New Help Offer on your Urgent Request",
            message="Aarav Sharma offered to bring a Casio 991EX to the Central Library porch!",
            link=f"/urgent/{created_urgent[0].id}",
            category="urgent"
        )
        db.session.add(notif1)
        db.session.commit()

        print("[5/7] Seeding Buyer-Seller Private Messaging Threads...")
        # Conversation between Sneha (buyer) and Aarav (seller) regarding Casio Calculator
        conv = Conversation(
            listing_id=created_listings[0].id,
            buyer_id=buyer_sneha.id,
            seller_id=seller_aarav.id
        )
        db.session.add(conv)
        db.session.flush()

        messages_data = [
            (buyer_sneha.id, "Hi Aarav, is this Casio 991EX calculator still available? Does it include the plastic slide-on cover?"),
            (seller_aarav.id, "Hello Sneha! Yes, it's available. The protective hard cover is included and it has fresh solar backup."),
            (buyer_sneha.id, "Great! Can we meet today at the Technology Canteen around 3:30 PM?"),
            (seller_aarav.id, "3:30 PM at the Tech Canteen works perfectly. I will bring the calculator and user manual.")
        ]

        for sender_id, text_content in messages_data:
            msg = Message(
                conversation_id=conv.id,
                sender_id=sender_id,
                content=text_content,
                is_read=True
            )
            db.session.add(msg)
        db.session.commit()

        print("[6/7] Seeding Campus Escrow Orders...")
        # Order for B.S. Grewal math book
        math_listing = created_listings[1]
        order = Order(
            order_number="SM-ORD-2026-GUJ01",
            listing_id=math_listing.id,
            buyer_id=seller_aarav.id,
            seller_id=buyer_sneha.id,
            amount=450,
            status="PENDING",
            payment_method="DEMO_ESCROW",
            payment_status="HELD_IN_ESCROW",
            pickup_location="DA-IICT Resource Centre Entrance",
            notes="Meeting after 4 PM lecture to inspect book pages and binding."
        )
        db.session.add(order)
        db.session.flush()

        payment = PaymentRecord(
            order_id=order.id,
            gateway="CAMPUS_DEMO_ESCROW",
            gateway_order_id="ESC_DEMO_99881",
            amount=450,
            currency="INR",
            status="PAID",
            is_verified=True,
            verification_notes="Simulated student marketplace escrow hold."
        )
        db.session.add(payment)

        # Notify buyer and seller
        db.session.add(Notification(
            user_id=seller_aarav.id,
            title="Order Placed - Escrow Active",
            message=f"Your order for '{math_listing.title[:30]}...' is pending campus handoff.",
            link=f"/orders/{order.id}",
            category="order"
        ))
        db.session.commit()

        print("[7/7] Seeding Trust & Safety Moderation Reports...")
        report = Report(
            reporter_id=buyer_sneha.id,
            listing_id=created_listings[0].id,
            reported_user_id=seller_aarav.id,
            reason="Sample Test Report for Demonstration",
            details="Verifying that report routing works correctly into the Admin Moderation portal.",
            status="PENDING"
        )
        db.session.add(report)
        db.session.commit()

        print("\n" + "=" * 70)
        print(" SUCCESS: Student Mart Gujarat-Focused Database Successfully Seeded!")
        print("=" * 70)
        print(" Gujarat Priority Hubs: Ahmedabad & Gandhinagar (Nirma, DA-IICT, IITGn, LDCE, PDEU)")
        print(" Features Seeded:")
        print("   - 4 Active Urgent Need Requests (with timer countdown & student offers)")
        print("   - 11 Verified Campus Listings (For Sale, Free Giveaways, Lend/Borrow)")
        print("   - 7 Verified Student & Admin Accounts")
        print("   - Private Buyer-Seller Chat Thread & Escrow Order")
        print(" 1-Click Evaluation Credentials:")
        print("   Admin:   admin@studentmart.campus / Admin@123")
        print("   Seller:  aarav.sharma@nirmauni.ac.in / Student@123 (Ahmedabad)")
        print("   Buyer:   sneha.patel@daiict.ac.in / Student@123 (Gandhinagar)")
        print("=" * 70)

def seed_database():
    """Drops existing tables, creates fresh schema, and seeds complete initial data."""
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        populate_seed_records()

def ensure_seed_data():
    """Safely seeds colleges and initial records if database is empty without dropping existing data."""
    if College.query.count() == 0:
        print("[INIT] Empty database detected. Auto-populating initial college hubs and demo accounts...")
        populate_seed_records()

if __name__ == "__main__":
    seed_database()
