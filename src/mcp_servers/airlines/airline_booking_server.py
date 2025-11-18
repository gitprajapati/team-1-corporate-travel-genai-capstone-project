#!/usr/bin/env python3
"""
Enhanced Airlines MCP Server - Minimal but Powerful
YASH Travel Policy Compliant
"""

import json
import psycopg2
import psycopg2.extras
from fastmcp import FastMCP
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("airline-booking")

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(
    name="airline-booking",
    instructions="""
    Enhanced Airlines Booking Server for YASH Corporate Travel.
    
    KEY FEATURES:
    - YASH policy-compliant flight searches
    - Domestic and international flights
    - Corporate discount automation
    - Cabin class enforcement by employee grade
    - Preferred airline prioritization
    - Real-time seat availability
    
    POLICY RULES:
    - E1-E8: Economy class only
    - M1-M3: Business class allowed for international
    - Preferred vendors: Higher corporate discounts
    - International travel: BGH approval required
    - Baggage: 1 bag (23kg intl, 15kg domestic)
    """
)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("AIRLINES_DB_HOST"),
    "database": os.getenv("AIRLINES_DB_NAME"),
    "user": os.getenv("AIRLINES_DB_USER"),
    "password": os.getenv("AIRLINES_DB_PASSWORD"),
    "port": os.getenv("AIRLINES_DB_PORT"),
    "sslmode": "require"
}

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def is_business_class_allowed(employee_grade: str, is_international: bool) -> bool:
    """Check if employee grade allows business class"""
    business_allowed_grades = ['M1', 'M2', 'M3']
    return employee_grade in business_allowed_grades and is_international

def generate_booking_reference() -> str:
    """Generate unique booking reference"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = os.urandom(2).hex()
    return f"YASH-AIR-{timestamp}-{random_suffix}"

def get_allowed_cabin_classes(employee_grade: str, is_international: bool) -> List[str]:
    """Get allowed cabin classes based on employee grade and travel type"""
    if is_business_class_allowed(employee_grade, is_international):
        return ['economy', 'premium_economy', 'business']
    else:
        return ['economy', 'premium_economy']

@mcp.tool()
def search_flights(
    origin: str,
    destination: str,
    travel_date: str,
    employee_grade: str = "E5",
    cabin_class: str = "economy",
    preferred_only: bool = False,
    max_price: Optional[float] = None
) -> str:
    """
    Search for flights with YASH policy compliance.
    
    Args:
        origin: Departure city
        destination: Arrival city  
        travel_date: Travel date (YYYY-MM-DD)
        employee_grade: YASH employee grade
        cabin_class: Preferred cabin class
        preferred_only: Show only preferred airlines
        max_price: Maximum ticket price
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if route is international
        cursor.execute("""
            SELECT DISTINCT orig.country as origin_country, dest.country as dest_country
            FROM airports orig, airports dest
            WHERE LOWER(orig.city) = LOWER(%s) AND LOWER(dest.city) = LOWER(%s)
        """, (origin, destination))
        
        route_info = cursor.fetchone()
        if not route_info:
            return json.dumps({'error': 'Route not found'}, indent=2)
        
        is_international = route_info['origin_country'] != route_info['dest_country']
        
        # Policy compliance: Check allowed cabin classes
        allowed_classes = get_allowed_cabin_classes(employee_grade, is_international)
        if cabin_class not in allowed_classes:
            return json.dumps({
                'error': f'Policy violation: Employee grade {employee_grade} not allowed {cabin_class} class for {"international" if is_international else "domestic"} travel. Allowed: {", ".join(allowed_classes)}'
            }, indent=2)
        
        # Build search query
        query = """
            SELECT 
                f.flight_id, f.flight_number, f.departure_time, f.arrival_time,
                f.duration_minutes, f.aircraft_type, f.is_direct,
                al.airline_code, al.airline_name, al.is_preferred_vendor,
                al.corporate_discount_percent, al.quality_rating,
                orig.airport_code as origin_code, orig.city as origin_city,
                dest.airport_code as dest_code, dest.city as dest_city,
                fi.base_price, fi.available_seats,
                ba.checked_bags, ba.checked_bag_weight_kg,
                ROUND(fi.base_price * (1 - al.corporate_discount_percent/100), 2) as final_price,
                CASE 
                    WHEN orig.country != dest.country THEN 'international'
                    ELSE 'domestic'
                END as travel_type
            FROM flights f
            JOIN airlines al ON f.airline_id = al.airline_id
            JOIN airports orig ON f.origin_airport_id = orig.airport_id
            JOIN airports dest ON f.destination_airport_id = dest.airport_id
            JOIN flight_inventory fi ON f.flight_id = fi.flight_id
            LEFT JOIN baggage_allowance ba ON al.airline_id = ba.airline_id AND fi.cabin_class = ba.cabin_class
            WHERE LOWER(orig.city) = LOWER(%s)
            AND LOWER(dest.city) = LOWER(%s)
            AND fi.flight_date = %s
            AND fi.cabin_class = %s
            AND fi.available_seats > 0
        """
        
        params = [origin, destination, travel_date, cabin_class]
        
        # Add filters
        if preferred_only:
            query += " AND al.is_preferred_vendor = TRUE"
        
        if max_price:
            query += " AND (fi.base_price * (1 - al.corporate_discount_percent/100)) <= %s"
            params.append(max_price)
        
        query += " ORDER BY al.is_preferred_vendor DESC, final_price ASC"
        
        cursor.execute(query, params)
        flights = cursor.fetchall()
        
        # Format results
        formatted_flights = []
        for flight in flights:
            flight_data = {
                'flight_id': flight['flight_id'],
                'flight_number': f"{flight['airline_code']}{flight['flight_number']}",
                'airline': flight['airline_name'],
                'airline_code': flight['airline_code'],
                'route': f"{flight['origin_city']} ({flight['origin_code']}) → {flight['dest_city']} ({flight['dest_code']})",
                'departure_time': str(flight['departure_time']),
                'arrival_time': str(flight['arrival_time']),
                'duration_minutes': flight['duration_minutes'],
                'duration_hours': f"{flight['duration_minutes'] // 60}h {flight['duration_minutes'] % 60}m",
                'aircraft': flight['aircraft_type'],
                'is_direct': flight['is_direct'],
                'cabin_class': cabin_class,
                'base_price': float(flight['base_price']),
                'corporate_discount_percent': float(flight['corporate_discount_percent']),
                'final_price': float(flight['final_price']),
                'available_seats': flight['available_seats'],
                'is_preferred_vendor': flight['is_preferred_vendor'],
                'quality_rating': float(flight['quality_rating']),
                'travel_type': flight['travel_type'],
                'baggage': {
                    'checked_bags': flight['checked_bags'],
                    'checked_bag_weight_kg': flight['checked_bag_weight_kg']
                }
            }
            formatted_flights.append(flight_data)
        
        # Policy information
        policy_info = {
            'employee_grade': employee_grade,
            'travel_type': 'international' if is_international else 'domestic',
            'allowed_cabin_classes': allowed_classes,
            'selected_cabin_class': cabin_class,
            'business_class_allowed': is_business_class_allowed(employee_grade, is_international),
            'approval_required': is_international,
            'preferred_vendors_recommended': True
        }
        
        response = {
            'search_criteria': {
                'origin': origin,
                'destination': destination,
                'travel_date': travel_date,
                'employee_grade': employee_grade,
                'cabin_class': cabin_class,
                'is_international': is_international
            },
            'policy_info': policy_info,
            'flights_found': len(formatted_flights),
            'flights': formatted_flights
        }
        
        return json.dumps(response, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Flight search error: {e}")
        return json.dumps({'error': f'Flight search failed: {str(e)}'}, indent=2)
    finally:
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def get_flight_details(flight_id: int, travel_date: str) -> str:
    """
    Get detailed information about a specific flight.
    
    Args:
        flight_id: Flight ID
        travel_date: Travel date (YYYY-MM-DD)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                f.flight_id, f.flight_number, f.departure_time, f.arrival_time,
                f.duration_minutes, f.aircraft_type, f.is_direct,
                al.airline_code, al.airline_name, al.is_preferred_vendor,
                al.corporate_discount_percent, al.quality_rating, al.on_time_performance,
                orig.airport_code as origin_code, orig.airport_name as origin_airport, orig.city as origin_city,
                dest.airport_code as dest_code, dest.airport_name as dest_airport, dest.city as dest_city,
                fi.cabin_class, fi.base_price, fi.available_seats, fi.price_multiplier,
                ba.checked_bags, ba.checked_bag_weight_kg, ba.carry_on_bags, ba.carry_on_weight_kg,
                ROUND(fi.base_price * (1 - al.corporate_discount_percent/100), 2) as final_price
            FROM flights f
            JOIN airlines al ON f.airline_id = al.airline_id
            JOIN airports orig ON f.origin_airport_id = orig.airport_id
            JOIN airports dest ON f.destination_airport_id = dest.airport_id
            JOIN flight_inventory fi ON f.flight_id = fi.flight_id
            LEFT JOIN baggage_allowance ba ON al.airline_id = ba.airline_id AND fi.cabin_class = ba.cabin_class
            WHERE f.flight_id = %s AND fi.flight_date = %s
        """, (flight_id, travel_date))
        
        flight = cursor.fetchone()
        
        if not flight:
            return json.dumps({'error': 'Flight not found'}, indent=2)
        
        flight_details = dict(flight)
        
        # Convert decimal to float for JSON
        flight_details['base_price'] = float(flight_details['base_price'])
        flight_details['final_price'] = float(flight_details['final_price'])
        flight_details['corporate_discount_percent'] = float(flight_details['corporate_discount_percent'])
        flight_details['quality_rating'] = float(flight_details['quality_rating'])
        flight_details['on_time_performance'] = float(flight_details['on_time_performance'])
        flight_details['price_multiplier'] = float(flight_details['price_multiplier'])
        
        return json.dumps(flight_details, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Flight details error: {e}")
        return json.dumps({'error': f'Failed to get flight details: {str(e)}'}, indent=2)
    finally:
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def check_availability(flight_id: int, travel_date: str, cabin_class: str = "economy") -> str:
    """
    Check real-time seat availability for a flight.
    
    Args:
        flight_id: Flight ID
        travel_date: Travel date (YYYY-MM-DD)
        cabin_class: Cabin class to check
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                fi.available_seats, fi.base_price, fi.price_multiplier,
                al.airline_name, al.corporate_discount_percent,
                f.flight_number, orig.city as origin_city, dest.city as dest_city,
                ba.checked_bags, ba.checked_bag_weight_kg
            FROM flight_inventory fi
            JOIN flights f ON fi.flight_id = f.flight_id
            JOIN airlines al ON f.airline_id = al.airline_id
            JOIN airports orig ON f.origin_airport_id = orig.airport_id
            JOIN airports dest ON f.destination_airport_id = dest.airport_id
            LEFT JOIN baggage_allowance ba ON al.airline_id = ba.airline_id AND fi.cabin_class = ba.cabin_class
            WHERE fi.flight_id = %s AND fi.flight_date = %s AND fi.cabin_class = %s
        """, (flight_id, travel_date, cabin_class))
        
        availability = cursor.fetchone()
        
        if not availability:
            return json.dumps({'error': 'Flight availability not found'}, indent=2)
        
        base_price = float(availability['base_price'])
        discount = base_price * (float(availability['corporate_discount_percent']) / 100)
        final_price = base_price - discount
        
        availability_info = {
            'flight_number': f"{availability['airline_name']} {availability['flight_number']}",
            'route': f"{availability['origin_city']} → {availability['dest_city']}",
            'travel_date': travel_date,
            'cabin_class': cabin_class,
            'availability': {
                'available_seats': availability['available_seats'],
                'is_available': availability['available_seats'] > 0
            },
            'pricing': {
                'base_price': base_price,
                'corporate_discount_percent': float(availability['corporate_discount_percent']),
                'discount_amount': round(discount, 2),
                'final_price': round(final_price, 2),
                'price_multiplier': float(availability['price_multiplier'])
            },
            'baggage': {
                'checked_bags': availability['checked_bags'],
                'checked_bag_weight_kg': availability['checked_bag_weight_kg']
            }
        }
        
        return json.dumps(availability_info, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Availability check error: {e}")
        return json.dumps({'error': f'Availability check failed: {str(e)}'}, indent=2)
    finally:
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def book_flight(
    flight_id: int,
    travel_date: str,
    passenger_name: str,
    passenger_email: str,
    employee_grade: str = "E5",
    cabin_class: str = "economy",
    seat_preference: str = "No Preference",
    special_requests: str = ""
) -> str:
    """
    Book a flight with YASH policy compliance.
    
    Args:
        flight_id: Flight ID to book
        travel_date: Travel date (YYYY-MM-DD)
        passenger_name: Full name of passenger
        passenger_email: Email address of passenger
        employee_grade: YASH employee grade
        cabin_class: Cabin class to book
        seat_preference: Seat preference
        special_requests: Any special requests
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First, try to find the traveler by email
        cursor.execute("SELECT traveler_id FROM travelers WHERE email = %s", (passenger_email,))
        traveler_result = cursor.fetchone()
        
        traveler_id = None
        if traveler_result:
            traveler_id = traveler_result['traveler_id']
        else:
            # If traveler not found by email, create a new traveler record
            logger.info(f"Traveler not found with email {passenger_email}, creating new traveler...")
            cursor.execute("""
                INSERT INTO travelers (traveler_code, first_name, last_name, email, employee_id, employee_grade, is_corporate, company_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING traveler_id
            """, (
                f"EMP-TEMP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                passenger_name.split()[0] if passenger_name else "Unknown",
                passenger_name.split()[-1] if passenger_name and ' ' in passenger_name else "Unknown",
                passenger_email,
                f"TEMP-{datetime.now().strftime('%H%M%S')}",
                employee_grade,
                True,
                'YASH Technologies'
            ))
            traveler_id = cursor.fetchone()['traveler_id']
            logger.info(f"Created new traveler with ID: {traveler_id}")
        
        # Get flight details and check policy compliance - FIXED QUERY
        cursor.execute("""
            SELECT 
                f.flight_id, f.flight_number, f.airline_id,
                al.airline_name, al.corporate_discount_percent,
                orig.country as origin_country, dest.country as dest_country,
                fi.base_price, fi.available_seats, fi.inventory_id, fi.cabin_class,
                orig.city as origin_city, dest.city as dest_city
            FROM flights f
            JOIN airlines al ON f.airline_id = al.airline_id
            JOIN airports orig ON f.origin_airport_id = orig.airport_id
            JOIN airports dest ON f.destination_airport_id = dest.airport_id
            JOIN flight_inventory fi ON f.flight_id = fi.flight_id
            WHERE f.flight_id = %s AND fi.flight_date = %s AND fi.cabin_class = %s
        """, (flight_id, travel_date, cabin_class))
        
        flight_info = cursor.fetchone()
        
        if not flight_info:
            logger.error(f"Flight {flight_id} not found for date {travel_date} in cabin class {cabin_class}")
            return json.dumps({'error': f'Flight {flight_id} not found for date {travel_date} in cabin class {cabin_class}'}, indent=2)
        
        logger.info(f"Found flight: {flight_info['airline_name']} {flight_info['flight_number']}")
        
        # Check availability
        if flight_info['available_seats'] <= 0:
            return json.dumps({'error': 'No seats available'}, indent=2)
        
        # Policy compliance check
        is_international = flight_info['origin_country'] != flight_info['dest_country']
        allowed_classes = get_allowed_cabin_classes(employee_grade, is_international)
        
        if cabin_class not in allowed_classes:
            return json.dumps({
                'error': f'Policy violation: Employee grade {employee_grade} not allowed {cabin_class} class for {"international" if is_international else "domestic"} travel. Allowed: {", ".join(allowed_classes)}'
            }, indent=2)
        
        # Calculate pricing
        base_price = float(flight_info['base_price'])
        discount_percent = float(flight_info['corporate_discount_percent'])
        discount_amount = base_price * (discount_percent / 100)
        final_price = base_price - discount_amount
        
        # Create booking - SIMPLIFIED to match actual schema
        cursor.execute("""
            INSERT INTO flight_bookings (
                traveler_id, flight_id, booking_date, travel_date, cabin_class, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING booking_id
        """, (
            traveler_id, flight_id, datetime.now(), travel_date, cabin_class, 'confirmed'
        ))
        
        booking_id = cursor.fetchone()['booking_id']
        logger.info(f"Created booking with ID: {booking_id}")
        
        # Create approval record if international travel
        if is_international:
            cursor.execute("""
                INSERT INTO booking_approvals (
                    booking_id, approver_name, status, approval_date
                ) VALUES (%s, %s, %s, %s)
            """, (booking_id, 'BGH Approval Required', 'pending', datetime.now()))
            logger.info(f"Created international travel approval record for booking {booking_id}")
        
        # Update inventory
        cursor.execute("""
            UPDATE flight_inventory 
            SET available_seats = available_seats - 1
            WHERE inventory_id = %s
        """, (flight_info['inventory_id'],))
        
        # Add seat preference and special requests if supported by schema
        try:
            cursor.execute("""
                INSERT INTO booking_details (
                    booking_id, seat_preference, special_requests
                ) VALUES (%s, %s, %s)
            """, (booking_id, seat_preference, special_requests))
        except Exception as detail_error:
            logger.warning(f"Could not add booking details: {detail_error}")
            # Continue without details if table doesn't exist
        
        conn.commit()
        logger.info(f"Booking {booking_id} committed successfully")
        
        # Generate booking reference
        booking_ref = f"YASH-BK-{booking_id:06d}"
        
        # Prepare response
        booking_confirmation = {
            'success': True,
            'booking_id': booking_id,
            'booking_reference': booking_ref,
            'status': 'confirmed',
            'flight': {
                'airline': flight_info['airline_name'],
                'flight_number': flight_info['flight_number'],
                'route': f"{flight_info['origin_city']} → {flight_info['dest_city']}",
                'travel_date': travel_date,
                'cabin_class': cabin_class,
                'is_international': is_international
            },
            'passenger_info': {
                'name': passenger_name,
                'email': passenger_email,
                'employee_grade': employee_grade
            },
            'pricing': {
                'base_fare': round(base_price, 2),
                'corporate_discount_percent': discount_percent,
                'discount_amount': round(discount_amount, 2),
                'final_price': round(final_price, 2),
                'currency': 'INR'
            },
            'policy_compliance': {
                'status': 'compliant',
                'employee_grade': employee_grade,
                'cabin_class_approved': True,
                'approval_required': is_international,
                'approval_level': 'BGH' if is_international else 'None',
                'allowed_cabin_classes': allowed_classes
            },
            'preferences': {
                'seat_preference': seat_preference,
                'special_requests': special_requests
            },
            'next_steps': [
                'Check email for booking confirmation',
                'Complete web check-in 48 hours before flight',
                'Carry valid ID proof for airport security'
            ] + (['International travel approval pending from BGH'] if is_international else [])
        }
        
        return json.dumps(booking_confirmation, indent=2, default=str)
        
    except psycopg2.Error as db_error:
        logger.error(f"Database error during booking: {db_error}")
        if conn:
            conn.rollback()
        return json.dumps({'error': f'Database error: {str(db_error)}'}, indent=2)
    except Exception as e:
        logger.error(f"Booking error: {e}")
        if conn:
            conn.rollback()
        return json.dumps({'error': f'Booking failed: {str(e)}'}, indent=2)
    finally:
        if conn:
            conn.close()
            
@mcp.tool()
def get_booking_status(booking_id: int) -> str:
    """
    Get current status of a flight booking.
    
    Args:
        booking_id: Booking ID number
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                fb.booking_id, fb.booking_date, fb.status,
                t.first_name, t.last_name, t.email, t.employee_grade,
                al.airline_name, f.flight_number,
                orig.city as origin_city, dest.city as dest_city,
                fi.flight_date, fi.cabin_class, fi.base_price,
                ba.status as approval_status
            FROM flight_bookings fb
            JOIN travelers t ON fb.traveler_id = t.traveler_id
            JOIN flights f ON fb.flight_id = f.flight_id
            JOIN airlines al ON f.airline_id = al.airline_id
            JOIN airports orig ON f.origin_airport_id = orig.airport_id
            JOIN airports dest ON f.destination_airport_id = dest.airport_id
            JOIN flight_inventory fi ON f.flight_id = fi.flight_id
            LEFT JOIN booking_approvals ba ON fb.booking_id = ba.booking_id
            WHERE fb.booking_id = %s
        """, (booking_id,))
        
        booking = cursor.fetchone()
        
        if not booking:
            return json.dumps({'error': 'Booking not found'}, indent=2)
        
        booking_info = dict(booking)
        # Convert decimal to float
        if booking_info['base_price']:
            booking_info['base_price'] = float(booking_info['base_price'])
        
        return json.dumps(booking_info, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return json.dumps({'error': f'Status check failed: {str(e)}'}, indent=2)
    finally:
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def get_preferred_airlines(route_type: str = "both") -> str:
    """
    Get list of YASH preferred airlines.
    
    Args:
        route_type: "domestic", "international", or "both"
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT airline_code, airline_name, country, corporate_discount_percent,
                   quality_rating, on_time_performance, is_preferred_vendor
            FROM airlines 
            WHERE is_preferred_vendor = TRUE
        """
        
        if route_type == "domestic":
            query += " AND is_domestic_approved = TRUE"
        elif route_type == "international":
            query += " AND is_international_approved = TRUE"
        
        query += " ORDER BY corporate_discount_percent DESC, quality_rating DESC"
        
        cursor.execute(query)
        airlines = cursor.fetchall()
        
        preferred_airlines = []
        for airline in airlines:
            airline_dict = dict(airline)
            airline_dict['corporate_discount_percent'] = float(airline_dict['corporate_discount_percent'])
            airline_dict['quality_rating'] = float(airline_dict['quality_rating'])
            airline_dict['on_time_performance'] = float(airline_dict['on_time_performance'])
            preferred_airlines.append(airline_dict)
        
        return json.dumps({
            'route_type': route_type,
            'preferred_airlines_count': len(preferred_airlines),
            'preferred_airlines': preferred_airlines
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Preferred airlines error: {e}")
        return json.dumps({'error': f'Failed to get preferred airlines: {str(e)}'}, indent=2)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("✈️ Starting Enhanced Airlines MCP Server...")
    print("📍 YASH Policy Compliant Flight Booking")
    print("✅ Features: Policy enforcement, Corporate discounts, Real-time availability")
    mcp.run(transport="http", host="0.0.0.0", port=8001)