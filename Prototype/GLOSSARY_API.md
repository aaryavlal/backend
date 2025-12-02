# Glossary API Documentation

The Glossary API provides a collaborative knowledge base where students in the same room can add definitions and notes about computing concepts they're learning. Each room maintains its own glossary, allowing students to build a shared reference guide as they progress through modules.

## Features

- **Room-specific**: Each room has its own isolated glossary
- **Collaborative**: All room members can contribute entries
- **Searchable**: Find terms quickly with built-in search
- **Attributed**: Each entry tracks who created it and when
- **CRUD Operations**: Full Create, Read, Update, Delete support
- **Access Control**: Only room members can view/add entries
- **Statistics**: Track glossary size and contributor count

## Database Schema

```sql
CREATE TABLE glossary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    term TEXT NOT NULL,
    definition TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id),
    FOREIGN KEY (author_id) REFERENCES users(id)
);
```

## API Endpoints

### 1. Get Room Glossary

Get all glossary entries for a specific room with optional search.

**Endpoint:** `GET /api/glossary/room/<room_id>`

**Query Parameters:**
- `search` (optional): Search term to filter entries (searches both term and definition)

**Authentication:** Required (JWT)

**Access:** Must be a member of the room

**Response:**
```json
{
  "entries": [
    {
      "id": 1,
      "room_id": 5,
      "term": "Parallel Computing",
      "definition": "A type of computation in which many calculations are carried out simultaneously",
      "author_id": 3,
      "author_name": "student1",
      "created_at": "2025-12-02 10:30:00"
    }
  ],
  "stats": {
    "total_entries": 12,
    "contributors": 4
  },
  "search_term": null
}
```

**Example with Search:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:5000/api/glossary/room/5?search=parallel"
```

### 2. Add Glossary Entry

Add a new glossary entry to a room.

**Endpoint:** `POST /api/glossary/room/<room_id>`

**Authentication:** Required (JWT)

**Access:** Must be a member of the room

**Request Body:**
```json
{
  "term": "Race Condition",
  "definition": "A situation where the system's behavior depends on the sequence or timing of uncontrollable events"
}
```

**Response:**
```json
{
  "message": "Glossary entry added successfully",
  "entry": {
    "id": 15,
    "room_id": 5,
    "term": "Race Condition",
    "definition": "A situation where the system's behavior depends on the sequence or timing of uncontrollable events",
    "author_id": 3,
    "author_name": "student1",
    "created_at": "2025-12-02 11:45:00"
  }
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"term":"Mutex","definition":"A mutual exclusion lock used to prevent race conditions"}' \
  http://localhost:5000/api/glossary/room/5
```

### 3. Get Single Entry

Get a specific glossary entry by ID.

**Endpoint:** `GET /api/glossary/<entry_id>`

**Authentication:** Required (JWT)

**Access:** Must be a member of the room that owns the entry

**Response:**
```json
{
  "entry": {
    "id": 15,
    "room_id": 5,
    "term": "Race Condition",
    "definition": "A situation where the system's behavior depends on the sequence or timing of uncontrollable events",
    "author_id": 3,
    "author_name": "student1",
    "created_at": "2025-12-02 11:45:00"
  }
}
```

### 4. Update Entry

Update an existing glossary entry.

**Endpoint:** `PUT /api/glossary/<entry_id>`

**Authentication:** Required (JWT)

**Access:** Must be the entry author or an admin

**Request Body:**
```json
{
  "term": "Race Condition (updated)",
  "definition": "A situation where the system's behavior depends on the sequence or timing of uncontrollable events. Common in multi-threaded applications."
}
```

Note: Both fields are optional - you can update just the term, just the definition, or both.

**Response:**
```json
{
  "message": "Glossary entry updated successfully",
  "entry": {
    "id": 15,
    "room_id": 5,
    "term": "Race Condition (updated)",
    "definition": "A situation where the system's behavior depends on the sequence or timing of uncontrollable events. Common in multi-threaded applications.",
    "author_id": 3,
    "author_name": "student1",
    "created_at": "2025-12-02 11:45:00"
  }
}
```

### 5. Delete Entry

Delete a glossary entry.

**Endpoint:** `DELETE /api/glossary/<entry_id>`

**Authentication:** Required (JWT)

**Access:** Must be the entry author or an admin

**Response:**
```json
{
  "message": "Glossary entry deleted successfully"
}
```

### 6. Get Glossary Statistics

Get statistics for a room's glossary.

**Endpoint:** `GET /api/glossary/room/<room_id>/stats`

**Authentication:** Required (JWT)

**Access:** Must be a member of the room

**Response:**
```json
{
  "total_entries": 24,
  "contributors": 6
}
```

## Error Responses

All endpoints return standard error responses:

**400 Bad Request:**
```json
{
  "error": "Term is required"
}
```

**403 Forbidden:**
```json
{
  "error": "You must be a member of this room to view its glossary"
}
```

**404 Not Found:**
```json
{
  "error": "Room not found"
}
```

**401 Unauthorized:**
```json
{
  "error": "Authorization token required"
}
```

## Frontend Integration Examples

### Display Glossary with Search

```javascript
// Fetch glossary entries
async function loadGlossary(roomId, searchTerm = '') {
  const url = searchTerm
    ? `/api/glossary/room/${roomId}?search=${encodeURIComponent(searchTerm)}`
    : `/api/glossary/room/${roomId}`;

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json();

  // Display entries
  data.entries.forEach(entry => {
    console.log(`${entry.term}: ${entry.definition}`);
    console.log(`Added by ${entry.author_name} on ${entry.created_at}`);
  });

  // Display stats
  console.log(`Total: ${data.stats.total_entries} entries from ${data.stats.contributors} contributors`);
}

// Search functionality
const searchInput = document.getElementById('glossary-search');
searchInput.addEventListener('input', (e) => {
  loadGlossary(roomId, e.target.value);
});
```

### Add New Entry

```javascript
async function addGlossaryEntry(roomId, term, definition) {
  const response = await fetch(`/api/glossary/room/${roomId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ term, definition })
  });

  const data = await response.json();

  if (response.ok) {
    alert('Entry added successfully!');
    loadGlossary(roomId); // Refresh the list
  } else {
    alert(`Error: ${data.error}`);
  }
}

// Form submission
const form = document.getElementById('add-glossary-form');
form.addEventListener('submit', (e) => {
  e.preventDefault();
  const term = document.getElementById('term-input').value;
  const definition = document.getElementById('definition-input').value;
  addGlossaryEntry(roomId, term, definition);
});
```

### Simple HTML Form Example

```html
<!-- Search Box -->
<div class="glossary-search">
  <input type="text" id="glossary-search" placeholder="Search glossary...">
</div>

<!-- Add Entry Form -->
<form id="add-glossary-form">
  <input type="text" id="term-input" placeholder="Term" required>
  <textarea id="definition-input" placeholder="Definition" required></textarea>
  <button type="submit">Add to Glossary</button>
</form>

<!-- Display Entries -->
<div id="glossary-list">
  <!-- Entries will be inserted here dynamically -->
</div>

<!-- Stats Display -->
<div class="glossary-stats">
  <span id="total-entries">0</span> entries from
  <span id="total-contributors">0</span> contributors
</div>
```

## Notes

- **Persistence**: Glossary entries are NOT deleted when room progress is reset, as they represent collaborative knowledge that should persist
- **Deletion**: Glossary entries ARE deleted when the entire room is deleted
- **Access Control**: Only room members can view and contribute to a room's glossary
- **Edit Rights**: Only the original author or admins can edit/delete entries
- **Search**: Case-insensitive search across both terms and definitions
- **Ordering**: Entries are returned alphabetically by term

## Use Cases

1. **Module Vocabulary**: Students can add computing terms they encounter while learning
2. **Team Notes**: Quick reference for concepts discussed in the room
3. **Study Guide**: Build a shared study resource as the team progresses
4. **Knowledge Sharing**: More advanced students can help define complex topics
5. **Progress Documentation**: Track what concepts the team has covered
