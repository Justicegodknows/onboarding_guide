# Administrator Sub-Agent System

## Overview

The Administrator Sub-Agent is a complete administrative interface for managing the VaultMind RAG system. It provides:

- **Exclusive Admin Database**: A separate ChromaDB collection for admin-only documents
- **Dedicated Data Pipeline**: Admin-specific ingestion with chunking and indexing
- **Full Admin Suite**: User management, analytics, system monitoring, and search capabilities
- **Secure Authentication**: JWT-based authentication with role-based access control

## Architecture

### Backend Stack

#### Services
- **AdminRAGService** (`rag_backend/app/services/admin_rag_service.py`)
  - Extends the main RAGService with admin-exclusive ChromaDB collection
  - Supports dual-database retrieval (main + admin)
  - Implements `ingest_admin()`, `retrieve_dual()`, `retrieve_admin_only()`

- **AdminIngestService** (`rag_backend/app/services/admin_ingest_service.py`)
  - Handles document ingestion into admin database
  - Supports: local, folder, and direct data sources
  - Tracks ingestion statistics and errors

#### API Router
- **Admin Router** (`rag_backend/app/routers/admin.py`)
  - Protected endpoints requiring ADMIN role
  - Key endpoints:
    - `POST /api/v1/admin/ingest` - Trigger data ingestion
    - `GET /api/v1/admin/documents` - List admin documents
    - `GET /api/v1/admin/analytics` - Get system analytics
    - `GET /api/v1/admin/status` - System health status
    - `GET /api/v1/admin/users` - List all users
    - `PUT /api/v1/admin/users/{user_id}` - Update user role
    - `POST /api/v1/admin/search/admin-only` - Search admin database only
    - `POST /api/v1/admin/search/dual` - Search both databases

#### Database Models
- **AdminDocument**: Tracks admin-ingested documents
- **AdminIngestLog**: Audit trail for ingestion operations
- **AdminUser**: Extended admin-specific user data and permissions

### Frontend Stack

#### Pages
- `/app/admin/page.tsx` - Dashboard overview
- `/app/admin/ingestion/page.tsx` - Data ingestion interface
- `/app/admin/documents/page.tsx` - List admin documents
- `/app/admin/users/page.tsx` - User management
- `/app/admin/search/page.tsx` - Dual-database search
- `/app/admin/analytics/page.tsx` - Analytics dashboard
- `/app/admin/status/page.tsx` - System status monitoring

#### Components
- **AdminSidebar** - Navigation and logout
- **AdminDashboard** - Main dashboard with statistics
- **Styling** - `admin.css` with complete admin UI design

## Authentication & Authorization

### JWT-Based Access Control
1. Admin users have `role: "ADMIN"` in JWT token
2. `require_admin()` dependency verifies:
   - JWT token validity
   - `ADMIN` role present
   - `AdminUser` record exists and is active
   - Returns admin-specific metadata

### Permission Levels
- **Standard**: Can ingest data, view analytics
- **Super**: Full access (user management, system admin)

```python
# Example JWT payload for admin user
{
  "sub": "admin@vaultmind.local",
  "role": "ADMIN",
  "dept": "IT",
  "display_name": "VaultMind Admin",
  "exp": 1234567890
}
```

## Data Flow

### Ingestion Pipeline

1. **Admin uploads data** via `/admin/ingestion` page
2. **Frontend sends request** to `/api/v1/admin/ingest` with:
   - `source`: "local", "folder", or "direct"
   - `folder_path` (optional): Path to documents
   - `documents` (optional): Direct document objects
3. **AdminIngestService processes**:
   - Loads documents from specified source
   - Calls `AdminRAGService.ingest_admin()`
   - Chunks documents using same settings as main pipeline
   - Indexes to separate ChromaDB collection (`admin_database`)
   - Tags chunks with `data_type: "admin"` metadata
4. **AdminIngestLog records**:
   - Admin email
   - Timestamp
   - Chunk counts (total, ingested, errors)
   - Metadata for auditing
5. **Frontend displays** ingestion results

### Retrieval Modes

#### Admin-Only Search
- Searches only the admin-exclusive ChromaDB collection
- Returns docs tagged with `data_type: "admin"`

#### Dual Search
- Retrieves from both main and admin databases
- Returns results grouped by source
- Admin users get more context for queries

```python
# Example dual retrieval
admin_rag = AdminRAGService()
results = admin_rag.retrieve_dual(
    query="system configuration",
    top_k=6
)
# Returns:
# {
#   "main": [...],  # Results from main database
#   "admin": [...]  # Results from admin database
# }
```

## Key Features

### 1. Exclusive Admin Database
```
./chroma_db           # Main RAG database
./chroma_db_admin     # Admin-exclusive database (separate persistence)
```

### 2. Dual Database Retrieval
Admin users can query both databases simultaneously:
- Better context for decision-making
- Access to sensitive admin documents
- Main database remains unchanged

### 3. Comprehensive Audit Trail
Every ingestion operation is logged:
```
admin_ingest_logs table:
- admin_email
- ingest_type
- timestamps (started, completed)
- chunk statistics
- error messages
```

### 4. User Management
- Promote/demote users between ADMIN/USER roles
- Set admin permission levels (standard/super)
- View all users and their status

### 5. Analytics Dashboard
- Total admin documents
- Total chunks indexed
- Recent ingestion activity
- System status monitoring

## Security Considerations

### Authentication
- JWT tokens with role-based claims
- Admin-specific dependency verification
- Active status check

### Authorization
- All admin endpoints protected by `require_admin()` dependency
- Users cannot bypass role checks
- Database-level verification of admin status

### Data Isolation
- Admin documents stored in separate ChromaDB collection
- Separate metadata namespace
- Tagged with `data_type: "admin"` for filtering

### Audit Trail
- Every ingestion logged to `admin_ingest_logs`
- Admin email recorded
- Timestamp and statistics tracked
- Error messages stored for debugging

## Usage Examples

### Create Admin User at Startup
```python
# In main.py lifespan()
admin_user = AdminUser(
    auth_user_id=admin_auth_id,
    admin_level="super",
    permissions='["ingest", "manage_users", "view_analytics"]',
    is_active=True,
)
db.add(admin_user)
db.commit()
```

### Ingest Admin Data
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"source": "local"}'
```

### Search Dual Databases
```bash
curl "http://localhost:8000/api/v1/admin/search/dual?query=budget" \
  -H "Authorization: Bearer <token>"
```

### Update User Role
```bash
curl -X PUT http://localhost:8000/api/v1/admin/users/5 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "ADMIN", "admin_level": "standard", "is_active": true}'
```

## Accessing the Admin Panel

1. **Login** with admin credentials:
   - Email: `admin@vaultmind.local`
   - Password: `admin123`
   - OR: `euzadmin` / `admin`

2. **Navigate** to `/admin` after login

3. **Dashboard** shows system statistics and recent activity

## Environment & Configuration

### Database Files
```
./chroma_db/              # Main RAG vector store
./chroma_db_admin/        # Admin-exclusive vector store
```

### No Additional Configuration Required
- Uses same embedding model as main RAG (NVIDIA NIM)
- Uses same chunking parameters
- Same authentication infrastructure

## Error Handling

### Common Errors

**"Admin access required"**
- User doesn't have ADMIN role in JWT
- Solution: Promote user via user management

**"Admin account is inactive"**
- AdminUser record exists but `is_active = False`
- Solution: Check database, update is_active to True

**"Failed to fetch documents"**
- Network or authentication issue
- Solution: Verify token is valid and fresh

**"Ingestion failed: Folder not found"**
- Specified folder path doesn't exist
- Solution: Verify path and permissions

## Future Enhancements

Potential features for expansion:
- Real-time analytics dashboard
- Document versioning and rollback
- Scheduled ingestion tasks
- Export/backup capabilities
- Advanced permission management
- API rate limiting per admin
- Encrypted document storage
- Multi-language support

## Support & Troubleshooting

### Logs
Check backend logs for admin operation details:
```bash
# View recent ingest logs
sqlite3 chroma_db/chroma.sqlite3 "SELECT * FROM admin_ingest_logs ORDER BY started_at DESC LIMIT 10;"
```

### Database Queries
```python
# Check admin users
admin_users = db.query(AdminUser).all()

# View ingest logs
logs = db.query(AdminIngestLog).filter(
    AdminIngestLog.status == 'error'
).all()

# List admin documents
docs = db.query(AdminDocument).all()
```

### System Health
Visit `/admin/status` page to check:
- Overall system status
- Database connectivity
- Vector store health
- Last update timestamp
