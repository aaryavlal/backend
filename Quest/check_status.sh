#!/bin/bash

# Quest Backend Status Checker
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PORT=8587
DATABASE="$SCRIPT_DIR/database.db"

echo "========================================"
echo "🔍 Quest Backend Status Check"
echo "========================================"

# Check if backend is running (works with or without lsof)
check_port() {
    if command -v lsof &> /dev/null; then
        lsof -ti:$PORT > /dev/null 2>&1
    elif command -v ss &> /dev/null; then
        ss -ltn | grep -q ":$PORT "
    elif command -v netstat &> /dev/null; then
        netstat -ltn | grep -q ":$PORT "
    else
        # Fallback: try to connect
        (echo > /dev/tcp/localhost/$PORT) &>/dev/null
    fi
}

if check_port; then
    echo "✅ Backend is RUNNING on port $PORT"
    if command -v lsof &> /dev/null; then
        echo "   Process IDs: $(lsof -ti:$PORT | tr '\n' ' ')"
    fi
else
    echo "❌ Backend is NOT running on port $PORT"
    echo ""
    echo "To start it, run:"
    echo "  python main.py"
    exit 1
fi

# Test health endpoint
echo ""
echo "🧪 Testing Health Endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/quest/health)

if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Health check passed (HTTP $HTTP_CODE)"
    RESPONSE=$(curl -s http://localhost:$PORT/quest/health)
    echo "   Response: $RESPONSE"
else
    echo "⚠️  Health check returned HTTP $HTTP_CODE"
fi

# Test main Quest endpoint
echo ""
echo "🧪 Testing Quest API..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/quest)

if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Quest API is responding (HTTP $HTTP_CODE)"
    echo ""
    echo "📊 Available endpoints:"
    curl -s http://localhost:$PORT/quest | python3 -m json.tool 2>/dev/null || curl -s http://localhost:$PORT/quest
else
    echo "⚠️  Quest API returned HTTP $HTTP_CODE"
fi

# Check database
echo ""
echo "========================================"
echo "🗄️  Database Status:"
echo "========================================"
if [ -f "$DATABASE" ]; then
    echo "✅ Database found: $DATABASE"
    DB_SIZE=$(du -h "$DATABASE" | cut -f1)
    echo "   Size: $DB_SIZE"

    # Check table counts
    if command -v sqlite3 &> /dev/null; then
        echo ""
        echo "📊 Database Statistics:"
        sqlite3 "$DATABASE" "SELECT 'Users: ' || COUNT(*) FROM users;" 2>/dev/null || echo "   Could not read users table"
        sqlite3 "$DATABASE" "SELECT 'Rooms: ' || COUNT(*) FROM rooms;" 2>/dev/null || echo "   Could not read rooms table"
        sqlite3 "$DATABASE" "SELECT 'Glossary entries: ' || COUNT(*) FROM glossary;" 2>/dev/null || echo "   Could not read glossary table"
    fi
else
    echo "⚠️  Database not found at: $DATABASE"
fi

echo ""
echo "========================================"
echo "🌐 Access Points:"
echo "========================================"
echo "   Health:      http://localhost:$PORT/quest/health"
echo "   Quest API:   http://localhost:$PORT/quest"
echo "   Auth:        http://localhost:$PORT/api/auth"
echo "   Rooms:       http://localhost:$PORT/api/rooms"
echo "   Progress:    http://localhost:$PORT/api/progress"
echo "   Glossary:    http://localhost:$PORT/api/glossary"
echo "   Game Logs:   http://localhost:$PORT/api/game-logs"
echo ""
echo "To stop backend: pkill -f 'python.*main.py'"
echo "To start backend: python main.py"
echo "========================================"

