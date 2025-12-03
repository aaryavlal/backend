#!/usr/bin/env python3
"""
Admin Room Management Script
Fetches all active rooms and allows deletion of non-demo rooms
"""
import requests
import sys

BASE_URL = "http://localhost:5000"

def login_as_admin(username="admin", password="admin123"):
    """Login as admin and return auth token"""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": username,
            "password": password
        })

        if response.status_code != 200:
            print(f"❌ Login failed: {response.json().get('error', 'Unknown error')}")
            return None

        return response.json()['access_token']
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def fetch_active_rooms(token):
    """Fetch all active rooms"""
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/api/rooms/active", headers=headers)

        if response.status_code != 200:
            print(f"❌ Failed to fetch rooms: {response.json().get('error', 'Unknown error')}")
            return None

        return response.json()['rooms']
    except Exception as e:
        print(f"❌ Error fetching rooms: {e}")
        return None

def delete_room(token, room_id):
    """Delete a single room"""
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.delete(f"{BASE_URL}/api/rooms/{room_id}", headers=headers)
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}

def bulk_delete_rooms(token, room_ids):
    """Bulk delete multiple rooms"""
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            f"{BASE_URL}/api/rooms/bulk-delete",
            headers=headers,
            json={"room_ids": room_ids}
        )

        if response.status_code != 200:
            print(f"❌ Bulk delete failed: {response.json().get('error', 'Unknown error')}")
            return None

        return response.json()
    except Exception as e:
        print(f"❌ Error during bulk delete: {e}")
        return None

def display_rooms(rooms):
    """Display rooms in a formatted table"""
    if not rooms:
        print("\n📭 No rooms found.")
        return

    print("\n" + "=" * 100)
    print(f"{'ID':<5} {'Room Code':<12} {'Name':<30} {'Members':<10} {'Progress':<12} {'Can Delete':<12}")
    print("=" * 100)

    for room in rooms:
        room_id = room['id']
        code = room['room_code']
        name = room['name'][:28] + '..' if len(room['name']) > 30 else room['name']
        members = str(room['member_count'])
        progress = f"{room['progress_percentage']:.0f}%"
        can_delete = "✅ Yes" if room['can_delete'] else "🔒 No (Demo)"

        print(f"{room_id:<5} {code:<12} {name:<30} {members:<10} {progress:<12} {can_delete:<12}")

    print("=" * 100)

def main():
    """Main function to manage rooms"""
    print("=" * 60)
    print("🔧 ADMIN ROOM MANAGEMENT TOOL")
    print("=" * 60)

    # Login
    print("\n🔐 Logging in as admin...")
    token = login_as_admin()

    if not token:
        print("❌ Failed to authenticate. Exiting.")
        sys.exit(1)

    print("✅ Login successful!")

    # Fetch rooms
    print("\n📊 Fetching active rooms...")
    rooms = fetch_active_rooms(token)

    if rooms is None:
        print("❌ Failed to fetch rooms. Exiting.")
        sys.exit(1)

    print(f"✅ Found {len(rooms)} room(s)")
    display_rooms(rooms)

    # Filter deletable rooms
    deletable_rooms = [r for r in rooms if r['can_delete']]

    if not deletable_rooms:
        print("\n✅ No rooms to delete (only demo room exists).")
        sys.exit(0)

    # Ask if user wants to delete
    print(f"\n🗑️  Found {len(deletable_rooms)} deletable room(s) (excluding demo room)")
    print("\nOptions:")
    print("  1. Delete ALL non-demo rooms")
    print("  2. Delete specific rooms by ID")
    print("  3. Exit without deleting")

    choice = input("\nEnter your choice (1/2/3): ").strip()

    if choice == '1':
        # Bulk delete all
        room_ids = [r['id'] for r in deletable_rooms]

        confirm = input(f"\n⚠️  Are you sure you want to delete {len(room_ids)} room(s)? (yes/no): ").strip().lower()

        if confirm == 'yes':
            print("\n🗑️  Deleting rooms...")
            result = bulk_delete_rooms(token, room_ids)

            if result:
                print(f"\n✅ {result['message']}")
                print(f"   Deleted: {result['summary']['deleted_count']}")
                print(f"   Protected: {result['summary']['protected_count']}")
                print(f"   Failed: {result['summary']['failed_count']}")

                if result['deleted']:
                    print("\n   Deleted rooms:")
                    for room in result['deleted']:
                        print(f"   - {room['name']} ({room['room_code']})")
        else:
            print("❌ Deletion cancelled.")

    elif choice == '2':
        # Delete specific rooms
        print("\nEnter room IDs to delete (comma-separated, e.g., 2,3,4):")
        ids_input = input("Room IDs: ").strip()

        try:
            room_ids = [int(id.strip()) for id in ids_input.split(',')]

            # Validate IDs
            valid_ids = [r['id'] for r in deletable_rooms]
            invalid_ids = [id for id in room_ids if id not in valid_ids]

            if invalid_ids:
                print(f"⚠️  Invalid or non-deletable room IDs: {invalid_ids}")
                room_ids = [id for id in room_ids if id in valid_ids]

            if not room_ids:
                print("❌ No valid rooms to delete.")
            else:
                confirm = input(f"\n⚠️  Delete {len(room_ids)} room(s)? (yes/no): ").strip().lower()

                if confirm == 'yes':
                    print("\n🗑️  Deleting rooms...")
                    result = bulk_delete_rooms(token, room_ids)

                    if result:
                        print(f"\n✅ {result['message']}")
                        print(f"   Deleted: {result['summary']['deleted_count']}")

                        if result['deleted']:
                            print("\n   Deleted rooms:")
                            for room in result['deleted']:
                                print(f"   - {room['name']} ({room['room_code']})")
                else:
                    print("❌ Deletion cancelled.")
        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by commas.")

    else:
        print("\n👋 Exiting without changes.")

    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to the server.")
        print("   Make sure Flask is running on http://localhost:5000")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
