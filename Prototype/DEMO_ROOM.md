# 🎯 Static Demo Room Feature

## Overview

The backend now includes a **permanent demo room** with code `DEMO01` that is always available and never gets deleted.

## Key Features

### 1. Always Available
- **Room Code**: `DEMO01`
- **Room Name**: "Demo Room - Always Available"
- Created automatically when the server starts
- Cannot be deleted by admins
- Perfect for testing and demonstrations

### 2. Auto-Reset Instead of Delete
When all 6 modules are completed in the demo room:
- ✅ All room progress is **reset** (nodes turn off)
- ✅ All member progress is **cleared** 
- ✅ Members stay in the room
- ✅ Everyone can start over immediately
- ❌ Room is **NOT** deleted

Regular rooms still delete when complete as normal.

## Usage

### For Students:
1. Register/Login
2. Join room with code: `DEMO01`
3. Complete modules
4. When all complete, progress resets automatically
5. Continue testing without needing to rejoin!

### For Admins:
- The demo room is created automatically on server startup
- No need to create it manually
- Cannot be deleted through the API
- Always shows up in room list

## API Behavior

### Joining Demo Room:
```bash
POST /api/rooms/join
{
  "room_code": "DEMO01"
}
```

### Completing Modules in Demo Room:
When the last member completes module 6:

**Response:**
```json
{
  "message": "Congratulations! All modules complete. Demo room has been reset!",
  "room_progress": {
    "module_complete": true,
    "room_complete": true,
    "is_demo": true
  }
}
```

Note the `is_demo: true` flag indicating it's the demo room.

### Regular Rooms:
**Response when complete:**
```json
{
  "message": "Congratulations! All modules complete. Room has been closed.",
  "room_progress": {
    "module_complete": true,
    "room_complete": true
  }
}
```

## Technical Details

### Code Changes:

**models/room.py:**
- Added `DEMO_ROOM_CODE` constant: `"DEMO01"`
- Added `ensure_demo_room_exists()` method
- Added `is_demo_room()` check method
- Added `reset_demo_room()` method
- Modified `delete_room()` to protect demo room
- Modified `check_and_update_room_progress()` to reset instead of delete

**app.py:**
- Calls `ensure_demo_room_exists()` on startup
- Prints demo room code to console

**routes/progress.py:**
- Updated completion messages for demo room
- Returns `is_demo: true` flag

### Database:
The demo room is stored like any other room but:
- `room_code = "DEMO01"`
- `created_by = 0` (system)
- Protected from deletion

## Frontend Integration

Update your frontend to handle the demo room:

```javascript
async function completeModule(moduleNumber) {
  const data = await apiCall('/api/progress/complete', 'POST', { 
    module_number: moduleNumber 
  });
  
  if (data.room_progress && data.room_progress.room_complete) {
    if (data.room_progress.is_demo) {
      // Demo room - reloaded but stay in room
      alert('🎉 All modules complete! Demo room has been reset. Try again!');
      loadRoomProgress(); // Refresh to show reset state
    } else {
      // Regular room - deleted
      alert('🎉 All modules complete! Room has been closed.');
      window.location.reload(); // Room is gone, reload page
    }
  }
}
```

## Benefits

### For Testing:
- ✅ No need to keep creating new rooms
- ✅ Instant reset for quick testing cycles
- ✅ Multiple testers can join same permanent room
- ✅ Great for demonstrations and tutorials

### For Users:
- ✅ Easy-to-remember code: `DEMO01`
- ✅ Always available for quick tests
- ✅ No admin needed to create room
- ✅ Can practice multiple times

## Server Startup

When you start the Flask server, you'll see:

```
✅ Database initialized successfully
✅ Flask app initialized
✅ Demo room available: DEMO01
 * Running on http://0.0.0.0:5000
```

## Room List Response

The demo room appears in the room list like any other:

```json
{
  "rooms": [
    {
      "id": 1,
      "room_code": "DEMO01",
      "name": "Demo Room - Always Available",
      "created_by": 0,
      "creator_name": null,
      "member_count": 3,
      "created_at": "2024-11-19 12:00:00"
    },
    {
      "id": 2,
      "room_code": "A1B2C3",
      "name": "Computer Science 101",
      "created_by": 1,
      "creator_name": "admin",
      "member_count": 5,
      "created_at": "2024-11-19 13:00:00"
    }
  ]
}
```

## Testing the Demo Room

### Quick Test:
```bash
# Join the demo room
curl -X POST http://localhost:5000/api/rooms/join \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"room_code":"DEMO01"}'

# Complete all modules (1-6)
for i in {1..6}; do
  curl -X POST http://localhost:5000/api/progress/complete \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -d "{\"module_number\":$i}"
done

# Check that progress was reset
curl -X GET http://localhost:5000/api/progress/my-progress \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Notes

- The demo room code `DEMO01` is hardcoded and cannot be changed without modifying the source
- If you want a different code, change `DEMO_ROOM_CODE` in `models/room.py`
- The demo room persists across server restarts
- Member list is preserved on reset (members don't get kicked out)
- Individual user progress is cleared, but membership remains

## Future Enhancements

Possible additions:
- Multiple demo rooms with different codes
- Admin panel to configure demo room behavior
- Scheduled auto-reset (e.g., every hour)
- Demo room analytics/statistics
- Custom welcome message for demo room
