# Admin User Setup Guide

This guide explains how to create and manage admin users for the TradeMate admin portal.

## Quick Start

### Step 1: Create a Regular User

First, register a regular user account through the API:

```bash
curl -X POST http://localhost:8000/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trademate.com",
    "username": "Admin User",
    "phone_number": "+923001234567",
    "password": "your-secure-password"
  }'
```

### Step 2: Verify the User (if email verification is enabled)

If email verification is enabled, verify the user with the OTP sent to their email:

```bash
curl -X POST http://localhost:8000/v1/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trademate.com",
    "otp": "123456"
  }'
```

### Step 3: Promote User to Admin

From the server directory, run the make_admin script:

```bash
cd server
python -m scripts.make_admin admin@trademate.com
```

You should see:
```
✓ Successfully promoted 'Admin User' (admin@trademate.com) to admin!

User Details:
  ID: 1
  Name: Admin User
  Email: admin@trademate.com
  Is Admin: True
  Is Verified: True
  Status: active
```

### Step 4: Login and Access Admin Portal

1. **Login to get JWT token:**

```bash
curl -X POST http://localhost:8000/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trademate.com",
    "password": "your-secure-password"
  }'
```

2. **Use the token to access admin endpoints:**

```bash
curl http://localhost:8000/v1/admin/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

3. **Or access the admin portal UI:**

Navigate to `http://localhost:3000` and login with your admin credentials.

## Managing Admins

### List All Admin Users

```bash
cd server
python -m scripts.make_admin --list
```

Output:
```
Admin Users (2):
  👑 Admin User (admin@trademate.com) - ID: 1
  👑 John Doe (john@trademate.com) - ID: 5
```

### Promote Another User to Admin

```bash
python -m scripts.make_admin user@example.com
```

### Check Available Users

If you forget the email, run the script with a non-existent email to see all users:

```bash
python -m scripts.make_admin nonexistent@email.com
```

This will show:
```
❌ Error: User with email 'nonexistent@email.com' not found.

Available users:
  - admin@trademate.com (Admin User) 👑 ADMIN
  - user@example.com (Regular User)
  - john@example.com (John Doe)
```

## Removing Admin Privileges

To remove admin privileges, use the database directly or create a demotion script:

```python
# Quick Python snippet to remove admin
from sqlmodel import Session, select
from database.database import engine
from models.user import User

with Session(engine) as session:
    user = session.exec(select(User).where(User.email_address == "user@example.com")).first()
    if user:
        user.is_admin = False
        session.add(user)
        session.commit()
        print(f"Removed admin privileges from {user.user_name}")
```

## Security Notes

1. **First Admin**: The first admin user must be created manually using the `make_admin.py` script
2. **Admin Check**: All admin endpoints now require `is_admin = True` in the database
3. **JWT Token**: Admin status is NOT stored in the JWT token - it's checked on every request
4. **Database Migration**: The `is_admin` column is automatically added when you restart the server

## Troubleshooting

### "User not found" Error

Make sure the user is registered first:
```bash
python -m scripts.make_admin --list
```

### "Admin privileges required" Error

Your user account doesn't have admin privileges. Use the `make_admin.py` script to promote your account.

### Migration Not Running

If the `is_admin` column isn't being added automatically:

1. Check server logs for migration errors
2. Manually add the column:
```sql
ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
```

## API Endpoints Requiring Admin

All endpoints under `/v1/admin/` require admin privileges:

- `GET /v1/admin/stats` - Dashboard statistics
- `GET /v1/admin/users` - List users
- `POST /v1/admin/users` - Create user
- `PUT /v1/admin/users/{id}` - Update user
- `DELETE /v1/admin/users/{id}` - Delete user
- `GET /v1/admin/chatbot/config` - Get chatbot config
- `PUT /v1/admin/chatbot/config` - Update chatbot config

## Example: Complete Admin Setup Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/v1/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","username":"Admin","phone_number":"+1234567890","password":"SecurePass123"}'

# 2. Verify email (get OTP from email)
curl -X POST http://localhost:8000/v1/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","otp":"123456"}'

# 3. Promote to admin
cd server
python -m scripts.make_admin admin@company.com

# 4. Login and get token
curl -X POST http://localhost:8000/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","password":"SecurePass123"}'

# 5. Access admin portal
# Open browser: http://localhost:3000
# Login with: admin@company.com / SecurePass123
```

---

For more information, see the main README or contact the development team.
