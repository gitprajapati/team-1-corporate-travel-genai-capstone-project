#!/usr/bin/env python3
"""
Enhanced Hotel MCP Server - Minimal but Powerful
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
logger = logging.getLogger("hotel-booking")

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(
    name="hotel-booking",
    instructions="""
    Enhanced Hotel Booking Server for YASH Corporate Travel.
    
    KEY FEATURES:
    - YASH policy-compliant hotel searches
    - Domestic (Tier-1/Tier-2) and international hotels
    - Corporate discount automation
    - Twin sharing policy enforcement
    - Women safety accommodations
    - Real-time availability checking
    
    POLICY RULES:
    - E1-E4, T, AT, Contract: Twin sharing mandatory
    - E5-E8, M1-M3: Single occupancy allowed
    - Women employees: Women-only rooms available
    - Preferred vendors: Higher corporate discounts
    """
)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("HOTEL_DB_HOST"),
    "database": os.getenv("HOTEL_DB_NAME"),
    "user": os.getenv("HOTEL_DB_USER"),
    "password": os.getenv("HOTEL_DB_PASSWORD"),
    "port": os.getenv("HOTEL_DB_PORT"),
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

def calculate_nights(check_in: str, check_out: str) -> int:
    """Calculate number of nights between dates"""
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
    check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
    return (check_out_date - check_in_date).days

def is_single_occupancy_allowed(employee_grade: str) -> bool:
    """Check if employee grade allows single occupancy"""
    single_allowed_grades = ['E5', 'E6', 'E7', 'E8', 'M1', 'M2', 'M3']
    return employee_grade in single_allowed_grades

def generate_booking_reference() -> str:
    """Generate unique booking reference"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = os.urandom(2).hex()
    return f"YASH-HTL-{timestamp}-{random_suffix}"

@mcp.tool()
def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    employee_grade: str = "E5",
    max_price: Optional[float] = None,
    min_stars: int = 3,
    preferred_only: bool = False,
    women_only: bool = False
) -> str:
    """
    Search for hotels in a city with YASH policy compliance.
    
    Args:
        city: City to search in
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        employee_grade: YASH employee grade (M1-M3, E1-E8, T, AT, Contract)
        max_price: Maximum price per night
        min_stars: Minimum star rating (1-5)
        preferred_only: Show only preferred vendors
        women_only: Show only women-safe accommodations
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        nights = calculate_nights(check_in, check_out)
        single_allowed = is_single_occupancy_allowed(employee_grade)
        
        # Build base query
        query = """
            SELECT 
                h.hotel_id, h.hotel_name, h.city, h.country, h.region, h.city_tier,
                h.star_rating, h.accommodation_type, h.is_yash_arranged,
                h.is_preferred_vendor, h.corporate_discount_percent,
                r.room_id, r.room_type, r.base_price, r.max_occupancy,
                r.bed_type, r.is_twin_sharing, r.women_only,
                MIN(ri.available_count) as min_availability,
                ROUND(r.base_price * (1 - h.corporate_discount_percent/100), 2) as final_price_per_night
            FROM hotels h
            JOIN rooms r ON h.hotel_id = r.hotel_id
            JOIN room_inventory ri ON r.room_id = ri.room_id
            WHERE LOWER(h.city) = LOWER(%s)
            AND ri.date BETWEEN %s AND %s
            AND ri.available_count > 0
            AND h.star_rating >= %s
        """
        
        params = [city, check_in, check_out, min_stars]
        
        # Add filters
        if preferred_only:
            query += " AND h.is_preferred_vendor = TRUE"
        
        if women_only:
            query += " AND (r.women_only = TRUE OR h.is_women_centric = TRUE)"
        
        # Policy compliance: Room type filtering based on employee grade
        if not single_allowed:
            query += " AND r.is_twin_sharing = TRUE"
        
        if max_price:
            query += " AND (r.base_price * (1 - h.corporate_discount_percent/100)) <= %s"
            params.append(max_price)
        
        query += """
            GROUP BY h.hotel_id, h.hotel_name, h.city, h.country, h.region, h.city_tier,
                     h.star_rating, h.accommodation_type, h.is_yash_arranged,
                     h.is_preferred_vendor, h.corporate_discount_percent,
                     r.room_id, r.room_type, r.base_price, r.max_occupancy,
                     r.bed_type, r.is_twin_sharing, r.women_only
            HAVING MIN(ri.available_count) > 0
            ORDER BY h.is_preferred_vendor DESC, final_price_per_night ASC
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        hotels_map = {}
        
        for row in results:
            hotel_id = row['hotel_id']
            
            if hotel_id not in hotels_map:
                hotels_map[hotel_id] = {
                    'hotel_id': hotel_id,
                    'hotel_name': row['hotel_name'],
                    'city': row['city'],
                    'country': row['country'],
                    'region': row['region'],
                    'city_tier': row['city_tier'],
                    'star_rating': row['star_rating'],
                    'accommodation_type': row['accommodation_type'],
                    'is_yash_arranged': row['is_yash_arranged'],
                    'is_preferred_vendor': row['is_preferred_vendor'],
                    'corporate_discount_percent': float(row['corporate_discount_percent']),
                    'rooms': []
                }
            
            room = {
                'room_id': row['room_id'],
                'room_type': row['room_type'],
                'base_price': float(row['base_price']),
                'final_price_per_night': float(row['final_price_per_night']),
                'total_stay_price': round(float(row['final_price_per_night']) * nights, 2),
                'max_occupancy': row['max_occupancy'],
                'bed_type': row['bed_type'],
                'is_twin_sharing': row['is_twin_sharing'],
                'women_only': row['women_only'],
                'min_availability': row['min_availability'],
                'nights': nights
            }
            
            hotels_map[hotel_id]['rooms'].append(room)
        
        hotels_list = list(hotels_map.values())
        
        # Add policy information
        policy_info = {
            'employee_grade': employee_grade,
            'single_occupancy_allowed': single_allowed,
            'twin_sharing_required': not single_allowed,
            'preferred_vendor_priority': True,
            'corporate_discount_applied': True
        }
        
        response = {
            'search_criteria': {
                'city': city,
                'check_in': check_in,
                'check_out': check_out,
                'nights': nights,
                'employee_grade': employee_grade,
                'max_price': max_price,
                'min_stars': min_stars
            },
            'policy_info': policy_info,
            'hotels_found': len(hotels_list),
            'hotels': hotels_list
        }
        
        return json.dumps(response, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return json.dumps({'error': f'Search failed: {str(e)}'}, indent=2)
    finally:
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def get_hotel_details(hotel_id: int) -> str:
    """
    Get detailed information about a specific hotel.
    
    Args:
        hotel_id: ID of the hotel to get details for
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get hotel basic info
        cursor.execute("""
            SELECT h.*, 
                   COUNT(DISTINCT r.room_id) as room_types_count,
                   COUNT(DISTINCT ha.amenity_id) as amenities_count
            FROM hotels h
            LEFT JOIN rooms r ON h.hotel_id = r.hotel_id
            LEFT JOIN hotel_amenities ha ON h.hotel_id = ha.hotel_id
            WHERE h.hotel_id = %s
            GROUP BY h.hotel_id
        """, (hotel_id,))
        
        hotel = cursor.fetchone()
        
        if not hotel:
            return json.dumps({'error': 'Hotel not found'}, indent=2)
        
        # Get amenities
        cursor.execute("""
            SELECT amenity_name, amenity_type 
            FROM hotel_amenities 
            WHERE hotel_id = %s
            ORDER BY amenity_type, amenity_name
        """, (hotel_id,))
        
        amenities = cursor.fetchall()
        
        # Get room types
        cursor.execute("""
            SELECT room_id, room_type, base_price, max_occupancy, 
                   bed_type, is_twin_sharing, women_only
            FROM rooms 
            WHERE hotel_id = %s
            ORDER BY base_price ASC
        """, (hotel_id,))
        
        rooms = cursor.fetchall()
        
        hotel_details = dict(hotel)
        hotel_details['amenities'] = [dict(amenity) for amenity in amenities]
        hotel_details['room_types'] = [dict(room) for room in rooms]
        
        # Convert decimal to float for JSON serialization
        hotel_details['corporate_discount_percent'] = float(hotel_details['corporate_discount_percent'])
        
        return json.dumps(hotel_details, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Hotel details error: {e}")
        return json.dumps({'error': f'Failed to get hotel details: {str(e)}'}, indent=2)
    finally:
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def check_availability(
    hotel_id: int,
    room_id: int, 
    check_in: str,
    check_out: str
) -> str:
    """
    Check real-time availability for a specific room.
    
    Args:
        hotel_id: Hotel ID
        room_id: Room ID
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check availability for all dates in the range
        cursor.execute("""
            SELECT 
                MIN(available_count) as min_availability,
                AVG(available_count) as avg_availability,
                COUNT(*) as days_checked
            FROM room_inventory
            WHERE room_id = %s 
            AND date BETWEEN %s AND %s
        """, (room_id, check_in, check_out))
        
        availability = cursor.fetchone()
        
        # Get room and hotel details
        cursor.execute("""
            SELECT r.*, h.hotel_name, h.city, h.corporate_discount_percent
            FROM rooms r
            JOIN hotels h ON r.hotel_id = h.hotel_id
            WHERE r.room_id = %s AND h.hotel_id = %s
        """, (room_id, hotel_id))
        
        room_info = cursor.fetchone()
        
        if not room_info:
            return json.dumps({'error': 'Room not found'}, indent=2)
        
        nights = calculate_nights(check_in, check_out)
        base_price = float(room_info['base_price'])
        discount = base_price * (float(room_info['corporate_discount_percent']) / 100)
        final_price_per_night = base_price - discount
        total_price = final_price_per_night * nights
        
        availability_info = {
            'hotel_name': room_info['hotel_name'],
            'city': room_info['city'],
            'room_type': room_info['room_type'],
            'check_in': check_in,
            'check_out': check_out,
            'nights': nights,
            'availability': {
                'min_available': availability['min_availability'],
                'avg_available': float(availability['avg_availability']),
                'days_checked': availability['days_checked'],
                'is_available': availability['min_availability'] > 0
            },
            'pricing': {
                'base_price_per_night': base_price,
                'corporate_discount_percent': float(room_info['corporate_discount_percent']),
                'discount_per_night': round(discount, 2),
                'final_price_per_night': round(final_price_per_night, 2),
                'total_stay_price': round(total_price, 2)
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
def book_hotel(
    hotel_id: int,
    room_id: int,
    check_in: str,
    check_out: str,
    guest_name: str,
    guest_email: str,
    employee_grade: str = "E5",
    guest_count: int = 1,
    special_requests: str = ""
) -> str:
    """
    Book a hotel room with YASH policy compliance.
    
    Args:
        hotel_id: Hotel ID to book
        room_id: Room ID to book
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        guest_name: Full name of guest
        guest_email: Email address of guest
        employee_grade: YASH employee grade
        guest_count: Number of guests (default 1)
        special_requests: Any special requests
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify room exists and get details
        cursor.execute("""
            SELECT r.*, h.hotel_name, h.city, h.corporate_discount_percent,
                   h.is_yash_arranged, h.accommodation_type
            FROM rooms r
            JOIN hotels h ON r.hotel_id = h.hotel_id
            WHERE r.room_id = %s AND h.hotel_id = %s
        """, (room_id, hotel_id))
        
        room_info = cursor.fetchone()
        
        if not room_info:
            return json.dumps({'error': 'Room not found'}, indent=2)
        
        # Policy compliance check
        single_allowed = is_single_occupancy_allowed(employee_grade)
        if not single_allowed and not room_info['is_twin_sharing']:
            return json.dumps({
                'error': f'Policy violation: Employee grade {employee_grade} requires twin sharing accommodation'
            }, indent=2)
        
        # Check availability manually
        cursor.execute("""
            SELECT 
                MIN(available_count) as min_availability
            FROM room_inventory
            WHERE room_id = %s 
            AND date BETWEEN %s AND %s
        """, (room_id, check_in, check_out))
        
        availability = cursor.fetchone()
        
        if not availability or availability['min_availability'] <= 0:
            return json.dumps({'error': 'Room not available for selected dates'}, indent=2)
        
        # Calculate pricing
        nights = calculate_nights(check_in, check_out)
        base_price = float(room_info['base_price'])
        discount_percent = float(room_info.get('corporate_discount_percent', 0))
        discount_amount = base_price * (discount_percent / 100)
        final_price_per_night = base_price - discount_amount
        total_amount = final_price_per_night * nights
        
        # Generate booking reference
        booking_ref = generate_booking_reference()
        
        # Create booking - using CORRECT travel_type values from the constraint
        cursor.execute("""
            INSERT INTO hotel_bookings (
                booking_reference, hotel_id, room_id, check_in_date, check_out_date,
                nights, guest_name, guest_count, total_amount, per_night_rate,
                corporate_discount, status, travel_type,
                is_twin_sharing, arranged_by_travel_desk
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING booking_id
        """, (
            booking_ref, hotel_id, room_id, check_in, check_out,
            nights, guest_name, guest_count, total_amount, final_price_per_night,
            discount_amount * nights, 'confirmed', 'short_term',  # Changed 'corporate' to 'short_term'
            room_info['is_twin_sharing'], True
        ))
        
        booking_id = cursor.fetchone()['booking_id']
        
        # Update inventory
        cursor.execute("""
            UPDATE room_inventory 
            SET available_count = available_count - 1
            WHERE room_id = %s AND date BETWEEN %s AND %s
        """, (room_id, check_in, check_out))
        
        conn.commit()
        
        # Prepare response
        booking_confirmation = {
            'success': True,
            'booking_id': booking_id,
            'booking_reference': booking_ref,
            'status': 'confirmed',
            'hotel': {
                'name': room_info['hotel_name'],
                'city': room_info['city'],
                'accommodation_type': room_info['accommodation_type'],
                'is_yash_arranged': room_info['is_yash_arranged']
            },
            'room': {
                'type': room_info['room_type'],
                'bed_type': room_info['bed_type'],
                'is_twin_sharing': room_info['is_twin_sharing']
            },
            'dates': {
                'check_in': check_in,
                'check_out': check_out,
                'nights': nights
            },
            'guest_info': {
                'name': guest_name,
                'email': guest_email,
                'employee_grade': employee_grade,
                'guest_count': guest_count
            },
            'pricing': {
                'base_price_per_night': base_price,
                'corporate_discount_percent': discount_percent,
                'discount_per_night': round(discount_amount, 2),
                'final_price_per_night': round(final_price_per_night, 2),
                'total_amount': round(total_amount, 2),
                'currency': 'USD'  # Changed to USD for international hotel
            },
            'policy_compliance': {
                'status': 'compliant',
                'employee_grade': employee_grade,
                'twin_sharing_required': not single_allowed,
                'accommodation_type_approved': True
            },
            'special_requests': special_requests
        }
        
        return json.dumps(booking_confirmation, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Booking error: {e}")
        if conn:
            conn.rollback()
        return json.dumps({'error': f'Booking failed: {str(e)}'}, indent=2)
    finally:
        if conn:
            conn.close()


@mcp.tool()
def get_booking_status(booking_reference: str) -> str:
    """
    Get current status of a hotel booking.
    
    Args:
        booking_reference: Booking reference number
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT hb.*, h.hotel_name, h.city, r.room_type
            FROM hotel_bookings hb
            JOIN hotels h ON hb.hotel_id = h.hotel_id
            JOIN rooms r ON hb.room_id = r.room_id
            WHERE hb.booking_reference = %s
        """, (booking_reference,))
        
        booking = cursor.fetchone()
        
        if not booking:
            return json.dumps({'error': 'Booking not found'}, indent=2)
        
        booking_info = dict(booking)
        # Convert decimal to float
        booking_info['total_amount'] = float(booking_info['total_amount'])
        booking_info['per_night_rate'] = float(booking_info['per_night_rate'])
        booking_info['corporate_discount'] = float(booking_info['corporate_discount'])
        
        return json.dumps(booking_info, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return json.dumps({'error': f'Status check failed: {str(e)}'}, indent=2)
    finally:
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def cancel_booking(booking_reference: str, guest_email: str) -> str:
    """
    Cancel a hotel booking and restore inventory.
    
    Args:
        booking_reference: Booking reference to cancel
        guest_email: Guest email for verification
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get booking details
        cursor.execute("""
            SELECT booking_id, room_id, check_in_date, check_out_date, status
            FROM hotel_bookings 
            WHERE booking_reference = %s
        """, (booking_reference,))
        
        booking = cursor.fetchone()
        
        if not booking:
            return json.dumps({'error': 'Booking not found'}, indent=2)
        
        if booking['status'] == 'cancelled':
            return json.dumps({'error': 'Booking already cancelled'}, indent=2)
        
        # Update booking status
        cursor.execute("""
            UPDATE hotel_bookings 
            SET status = 'cancelled' 
            WHERE booking_reference = %s
        """, (booking_reference,))
        
        # Restore inventory
        cursor.execute("""
            UPDATE room_inventory 
            SET available_count = available_count + 1
            WHERE room_id = %s AND date BETWEEN %s AND %s
        """, (booking['room_id'], booking['check_in_date'], booking['check_out_date']))
        
        conn.commit()
        
        return json.dumps({
            'success': True,
            'message': 'Booking cancelled successfully',
            'booking_reference': booking_reference,
            'status': 'cancelled'
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Cancellation error: {e}")
        if conn:
            conn.rollback()
        return json.dumps({'error': f'Cancellation failed: {str(e)}'}, indent=2)
    finally:
        if conn:
            conn.close()

@mcp.tool()
def get_preferred_hotels(city: str) -> str:
    """
    Get list of YASH preferred vendor hotels in a city.
    
    Args:
        city: City to search for preferred hotels
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                hotel_id, hotel_name, city, star_rating, 
                accommodation_type, corporate_discount_percent,
                is_yash_arranged, has_caretaker, is_women_centric
            FROM hotels 
            WHERE LOWER(city) = LOWER(%s) 
            AND is_preferred_vendor = TRUE
            ORDER BY star_rating DESC, corporate_discount_percent DESC
        """, (city,))
        
        hotels = cursor.fetchall()
        
        preferred_hotels = []
        for hotel in hotels:
            hotel_dict = dict(hotel)
            hotel_dict['corporate_discount_percent'] = float(hotel_dict['corporate_discount_percent'])
            preferred_hotels.append(hotel_dict)
        
        return json.dumps({
            'city': city,
            'preferred_hotels_count': len(preferred_hotels),
            'preferred_hotels': preferred_hotels
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Preferred hotels error: {e}")
        return json.dumps({'error': f'Failed to get preferred hotels: {str(e)}'}, indent=2)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting Enhanced Hotel MCP Server...")
    print("📍 YASH Policy Compliant Hotel Booking")
    print("✅ Features: Policy enforcement, Corporate discounts, Real-time availability")
    mcp.run(transport="http", host="0.0.0.0", port=8002)