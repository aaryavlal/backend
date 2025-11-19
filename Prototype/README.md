# Parallel Computing Education Platform - Backend

A Flask-based REST API for the Parallel Computing educational platform with community room-based learning.

## 🎯 Features

- **User Authentication**: JWT-based authentication with bcrypt password hashing
- **Community Rooms**: Admin-created rooms with unique codes for collaborative learning
- **Progress Tracking**: Individual and room-wide module completion tracking
- **Automatic Room Management**: Rooms automatically delete when all 6 modules are completed
- **Role-Based Access**: Student and Admin roles with appropriate permissions

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)

## 🚀 Installation

1. **Clone or download the project**

2. **Create a virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your own values
```

5. **Initialize the database**:
```bash
python database.py
```

6. **Run the application**:
```bash
python app.py
```

The server will start on `http://localhost:5000`

## 📁 Project Structure

```
parallel-computing-backend/
├── app.py                 # Main Flask application
├── database.py            # SQLite database configuration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── models/
│   ├── user.py           # User model
│   └── room.py           # Room model
└── routes/
    ├── auth.py           # Authentication routes
    ├── rooms.py          # Room management routes
    └── progress.py       # Progress tracking routes
```

## 🗄️ Database Schema

### Tables

1. **users**: User accounts
   - id, username, email, password, role, current_room_id, created_at

2. **rooms**: Learning rooms
   - id, room_code, name, created_by, created_at

3. **user_progress**: Individual module completion
   - id, user_id, module_number, completed_at

4. **room_members**: Room membership (many-to-many)
   - id, room_id, user_id, joined_at

5. **room_progress**: Room-wide module completion
   - id, room_id, module_number, completed_at

## 🔌 API Endpoints

### Authentication (`/api/auth`)

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "student1",
  "email": "student1@example.com",
  "password": "password123"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "student1",
  "password": "password123"
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### Rooms (`/api/rooms`)

#### Create Room (Admin Only)
```http
POST /api/rooms
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Computer Science 101"
}
```

#### Get All Rooms
```http
GET /api/rooms
Authorization: Bearer <token>
```

#### Get Room Details
```http
GET /api/rooms/<room_id>
Authorization: Bearer <token>
```

#### Join Room
```http
POST /api/rooms/join
Authorization: Bearer <token>
Content-Type: application/json

{
  "room_code": "A1B2C3"
}
```

#### Leave Room
```http
POST /api/rooms/<room_id>/leave
Authorization: Bearer <token>
```

#### Get Room Members
```http
GET /api/rooms/<room_id>/members
Authorization: Bearer <token>
```

#### Get Room Progress
```http
GET /api/rooms/<room_id>/progress
Authorization: Bearer <token>
```

#### Delete Room (Admin Only)
```http
DELETE /api/rooms/<room_id>
Authorization: Bearer <admin_token>
```

### Progress (`/api/progress`)

#### Complete Module
```http
POST /api/progress/complete
Authorization: Bearer <token>
Content-Type: application/json

{
  "module_number": 1
}
```

#### Get My Progress
```http
GET /api/progress/my-progress
Authorization: Bearer <token>
```

#### Get User Progress
```http
GET /api/progress/user/<user_id>
Authorization: Bearer <token>
```

## 🎮 Usage Flow

### For Students:

1. **Register** an account
2. **Login** to receive JWT token
3. **Join a room** using the room code provided by admin
4. **Complete modules** (1-6) at your own pace
5. Watch as room nodes **light up** when ALL members complete each module
6. Room **automatically closes** when all 6 modules are complete

### For Admins:

1. **Register** with admin role (set in database directly)
2. **Create rooms** with unique codes
3. **Share room codes** with students
4. **Monitor progress** across all rooms
5. **Delete rooms** if needed

## 🔒 Security Features

- Password hashing with bcrypt
- JWT token-based authentication
- Role-based access control
- SQL injection prevention with parameterized queries
- CORS enabled for cross-origin requests

## 🧪 Testing with cURL

### Register a user:
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","email":"student1@example.com","password":"pass123"}'
```

### Login:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"pass123"}'
```

### Complete a module:
```bash
curl -X POST http://localhost:5000/api/progress/complete \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"module_number":1}'
```

## 🌟 Key Features Explained

### Community Room System

- **Admin-Only Creation**: Only users with admin role can create rooms
- **Unique Room Codes**: 6-character alphanumeric codes for easy sharing
- **Collaborative Progress**: Nodes light up when ALL room members complete a module
- **Auto-Deletion**: Rooms automatically delete upon full completion (all 6 modules)
- **Real-time Stats**: Track individual and collective progress

### Module Completion Logic

1. Student completes a module → Individual progress recorded
2. Backend checks if ALL room members completed that module
3. If yes → Room progress updated (node lights up)
4. If all 6 modules complete → Room automatically deleted

## 🐛 Troubleshooting

**Database locked error**: Make sure only one instance of the app is running

**JWT errors**: Check that your token hasn't expired (7-day expiration by default)

**Permission denied**: Ensure you're using an admin token for admin-only endpoints

## 📝 Environment Variables

- `SECRET_KEY`: Flask secret key for sessions
- `JWT_SECRET_KEY`: Secret key for JWT token encoding
- `DATABASE_PATH`: Path to SQLite database file (default: database.db)

## 🤝 Contributing

This is a prototype backend. Future enhancements could include:
- WebSocket support for real-time progress updates
- Email notifications when rooms complete modules
- Analytics dashboard for admins
- Module content management
- Quiz/assessment integration

## 📄 License

Educational prototype - feel free to use and modify as needed.
