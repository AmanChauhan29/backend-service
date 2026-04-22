# 🍕 Food Ordering Backend System - Production Grade API

> A comprehensive, production-ready backend for food ordering systems with advanced features like **multi-tenancy, role-based access control, JWT authentication, rate limiting, and audit logging**.

## Perfect For:

✅ **Frontend Engineers** learning to build real-world applications  
✅ **College Students** getting hands-on API integration experience  
✅ **React/Vue/Angular Developers** needing a production-grade backend  
✅ **Learning Multi-role Systems** (Admin, Restaurant Owner, Customer)  
✅ **Understanding Tenant-Based Architecture** in SaaS applications  
✅ **Building Enterprise-Grade UIs** with complex permission hierarchies  

> **No API limits. No charges. Deploy anywhere. Learn everything.**

---

## 🚀 Quick Start

### Step 1: Clone the Repository
```bash
git clone https://github.com/AmanChauhan29/backend-service.git
cd backend-service
```

### Step 2: Set Up Virtual Environment
```bash
python -m venv .venv

# On Windows
.\.venv\Scripts\Activate

# On macOS/Linux
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```env
PROJECT_NAME=Food Ordering Backend
MONGO_URI=mongodb://localhost:27017
DB_NAME=food_ordering
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
SMTP_HOST=your-smtp-host
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password
FRONTEND_VERIFY_URL=http://localhost:3000/verify
REDIS_URL=redis://localhost:6379
```

### Step 5: Run the Application
```bash
python main.py
```

The API will be available at `http://localhost:8000`  
Interactive API docs: `http://localhost:8000/docs`

---

## 📚 What You'll Learn

### 🔐 **Authentication & Authorization**
- **JWT-based authentication** with access and refresh tokens
- **Email verification** workflow for secure registration
- **Password reset functionality** via email
- **Token rotation and reuse detection** for enhanced security
- **Multi-session management** with per-session tracking
- **Role-Based Access Control (RBAC)** implementation

### 🏪 **Multi-Role System Architecture**
Learn how enterprise systems handle different user roles with granular permissions:

| Role | Capabilities | Perfect for Learning |
|------|--------------|---------------------|
| **🔑 Superadmin** | System-wide control, user management, restaurant approval, audit logs | Admin dashboards, User management UIs |
| **🏢 Restaurant Admin** | Restaurant & menu management, order handling, team management | Restaurant owner portals, Dashboard views |
| **👤 User (Customer)** | Browse restaurants, place orders, track order status, manage profile | Customer-facing applications, Order tracking |

### 🏗️ **Multi-Tenancy & Data Isolation**
- Restaurant-level data isolation
- User-level data segregation
- Permission-based query filtering
- Secure cross-tenant access prevention

### 📦 **Complete Order Management**
- Order lifecycle management (pending → delivered)
- Real-time status updates
- Order history and filtering
- Cancellation policies and tracking

### 🔔 **Email Notifications**
- Email verification during signup
- Password reset emails
- Integration-ready notification system

### 📊 **Audit Logging**
- Track all system actions
- Before/after state snapshots
- User activity monitoring
- System compliance and security auditing

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend Application                   │
│              (React, Vue, Angular, etc.)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│         FastAPI Server (main.py)                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Routes Layer (routes/)                           │   │
│  │ - Auth Routes     - Admin Routes                 │   │
│  │ - User Routes     - Restaurant Routes            │   │
│  │ - Menu Routes     - Order Routes                 │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Services Layer (services/)                       │   │
│  │ - Authentication & Token Management              │   │
│  │ - Authorization & Permission Checking            │   │
│  │ - Business Logic Implementation                  │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Core Middleware (core/)                          │   │
│  │ - JWT Authentication                             │   │
│  │ - Rate Limiting (10 req/60s)                     │   │
│  │ - Request ID Tracing                             │   │
│  │ - Exception Handling                             │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Database Models (models/)                        │   │
│  │ - User Models     - Restaurant Models            │   │
│  │ - Order Models    - Menu Models                  │   │
│  │ - Auth Models     - Audit Models                 │   │
│  └──────────────────────────────────────────────────┘   │
└────────────┬─────────────────────────────┬──────────────┘
             ▼                             ▼
    ┌──────────────────┐       ┌──────────────────┐
    │    MongoDB       │       │      Redis       │
    │  (Data Store)    │       │  (Rate Limiting, │
    │                  │       │   Caching)       │
    └──────────────────┘       └──────────────────┘
```

---

## 📡 Complete API Endpoints Reference

### 🔓 **Authentication Endpoints** (`/api/v1/auth/`)

#### User Registration
```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe"
}

Response: { "id": "...", "email": "user@example.com", "is_verified": false }
```

#### Verify Email
```http
GET /api/v1/auth/verify-email?token=<verification_token>

Response: { "message": "Email verified successfully" }
```

#### User Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}

Response: {
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3540
}
```

#### Refresh Access Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>

Response: {
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Logout (Current Session)
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>

Response: { "message": "Logged out successfully" }
```

#### Logout All Sessions
```http
POST /api/v1/auth/logout-all
Authorization: Bearer <access_token>

Response: { "message": "Logged out from all devices" }
```

#### View Active Sessions
```http
GET /api/v1/auth/sessions
Authorization: Bearer <access_token>

Response: {
  "sessions": [
    {
      "id": "session_id",
      "device": "Mozilla/5.0...",
      "ip_address": "192.168.1.1",
      "created_at": "2024-04-22T10:30:00Z",
      "last_activity": "2024-04-22T10:45:00Z"
    }
  ]
}
```

#### Revoke Specific Session
```http
DELETE /api/v1/auth/session/{session_id}
Authorization: Bearer <access_token>

Response: { "message": "Session revoked" }
```

#### Password Reset
```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}

Response: { "message": "Password reset link sent to email" }
```

#### Reset Password with Token
```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "reset_token",
  "new_password": "new_secure_password"
}

Response: { "message": "Password reset successfully" }
```

---

### 👤 **User Routes** (`/api/v1/users/`)

#### Get Current User Profile
```http
GET /api/v1/users/user
Authorization: Bearer <access_token>

Response: {
  "id": "...",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "is_verified": true,
  "disabled": false
}
```

---

### 🏪 **Restaurant Routes** (`/api/v1/restaurants/`)

#### List All Approved Restaurants (Public)
```http
GET /api/v1/restaurants/?page=1&page_size=10

Response: {
  "total_restaurants": 25,
  "page": 1,
  "page_size": 10,
  "restaurants": [
    {
      "id": "...",
      "name": "Pizza Palace",
      "description": "Best pizzas in town",
      "address": "123 Main St",
      "phone": "555-1234",
      "slug": "pizza-palace"
    }
  ],
  "has_next": true
}
```

#### Search Restaurants
```http
GET /api/v1/restaurants/search?q=pizza&page=1

Response: { "restaurants": [...], "has_next": true }
```

#### Get Restaurant Details
```http
GET /api/v1/restaurants/{restaurant_id}

Response: {
  "id": "...",
  "name": "Pizza Palace",
  "owner_email": "owner@example.com",
  "approved": true,
  "description": "Best pizzas in town"
}
```

#### Create Restaurant (Superadmin Only)
```http
POST /api/v1/restaurants/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Burger King",
  "description": "Best burgers",
  "address": "456 Oak Ave",
  "phone": "555-5678",
  "owner_email": "owner@example.com"
}

Response: { "id": "...", "name": "Burger King", "approved": true }
```

#### Update Restaurant
```http
PATCH /api/v1/restaurants/{restaurant_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}

Response: { "id": "...", "name": "Updated Name" }
```

---

### 🍜 **Menu Routes** (`/api/v1/menu/`)

#### List Menu Items by Restaurant
```http
GET /api/v1/menu/{restaurant_id}?available=true

Response: {
  "menu_items": [
    {
      "id": "...",
      "name": "Margherita Pizza",
      "price": 12.99,
      "description": "Classic cheese pizza",
      "is_available": true
    }
  ]
}
```

#### Search Menu Items
```http
GET /api/v1/menu/search?q=pizza

Response: { "menu_items": [...] }
```

#### Create Menu Item (Restaurant Admin Only)
```http
POST /api/v1/menu/{restaurant_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Pepperoni Pizza",
  "price": 14.99,
  "description": "Pizza with pepperoni",
  "is_available": true
}

Response: { "id": "...", "name": "Pepperoni Pizza", "price": 14.99 }
```

#### Update Menu Item
```http
PATCH /api/v1/menu/{restaurant_id}/{item_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "price": 15.99,
  "is_available": false
}

Response: { "id": "...", "price": 15.99, "is_available": false }
```

#### Delete Menu Item
```http
DELETE /api/v1/menu/{restaurant_id}/{item_id}
Authorization: Bearer <access_token>

Response: (204 No Content)
```

---

### 📦 **Order Routes** (`/api/v1/orders/`)

#### Place New Order (Customer)
```http
POST /api/v1/orders/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "restaurant_id": "...",
  "items": [
    {
      "menu_item_id": "...",
      "quantity": 2,
      "name": "Margherita Pizza",
      "price": 12.99
    }
  ],
  "total_amount": 25.98
}

Response: {
  "id": "...",
  "status": "pending",
  "restaurant_id": "...",
  "total_amount": 25.98,
  "items": [...],
  "created_at": "2024-04-22T10:30:00Z"
}
```

#### Get User's Orders
```http
GET /api/v1/orders/?status=pending&page=1&page_size=10
Authorization: Bearer <access_token>

Response: {
  "total_orders": 5,
  "page": 1,
  "orders": [
    {
      "id": "...",
      "status": "pending",
      "total_amount": 25.98,
      "created_at": "2024-04-22T10:30:00Z"
    }
  ],
  "has_next": false
}
```

#### Search Orders by Status
```http
GET /api/v1/orders/search?status=delivered
Authorization: Bearer <access_token>

Response: { "orders": [...] }
```

#### Update Order (User Only)
```http
PUT /api/v1/orders/{order_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "special_instructions": "No onions please"
}

Response: { "id": "...", "special_instructions": "No onions please" }
```

#### Cancel Order (Customer)
```http
POST /api/v1/orders/{order_id}/cancel
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "reason": "Change of plans"
}

Response: { "id": "...", "status": "cancelled", "reason": "Change of plans" }
```

#### Delete Order
```http
DELETE /api/v1/orders/{order_id}
Authorization: Bearer <access_token>

Response: (204 No Content)
```

---

### 🏢 **Restaurant Admin Routes** (`/api/v1/restaurant/`)

#### Get All Orders for Restaurant Admin's Restaurants
```http
GET /api/v1/restaurant/orders?status=pending&page=1
Authorization: Bearer <access_token>

Response: {
  "total_orders": 10,
  "orders": [
    {
      "id": "...",
      "status": "pending",
      "user_email": "customer@example.com",
      "total_amount": 25.98,
      "created_at": "2024-04-22T10:30:00Z"
    }
  ]
}
```

#### Update Order Status (Restaurant Admin)
```http
PATCH /api/v1/restaurant/orders/{order_id}/status
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "preparing"
}

Response: { "id": "...", "status": "preparing", "updated_at": "2024-04-22T10:35:00Z" }
```

---

### 🔑 **Admin Routes** (`/api/v1/admin/`)

#### List All Users
```http
GET /api/v1/admin/users?page=1&page_size=20
Authorization: Bearer <access_token>

Response: {
  "total_users": 150,
  "page": 1,
  "users": [
    {
      "id": "...",
      "email": "user@example.com",
      "role": "user",
      "is_verified": true,
      "disabled": false
    }
  ]
}
```

#### Get User Details
```http
GET /api/v1/admin/users/{user_id}
Authorization: Bearer <access_token>

Response: {
  "id": "...",
  "email": "user@example.com",
  "role": "user",
  "is_verified": true,
  "restaurant_ids": [],
  "token_version": 1
}
```

#### Change User Role
```http
PATCH /api/v1/admin/users/{user_id}/role
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "role": "restaurant_admin",
  "restaurant_ids": ["rest_id_1", "rest_id_2"]
}

Response: { "id": "...", "role": "restaurant_admin", "restaurant_ids": [...] }
```

#### Promote User to Restaurant Admin
```http
POST /api/v1/admin/users/{target_email}/promote
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "restaurant_ids": ["rest_id_1", "rest_id_2"]
}

Response: { "email": "user@example.com", "role": "restaurant_admin", "restaurants": [...] }
```

#### Revoke All User Tokens
```http
POST /api/v1/admin/users/{user_id}/revoke
Authorization: Bearer <access_token>

Response: { "message": "All tokens revoked", "new_token_version": 2 }
```

#### Disable User Account
```http
POST /api/v1/admin/users/{user_id}/disable
Authorization: Bearer <access_token>

Response: { "id": "...", "disabled": true }
```

#### Enable User Account
```http
POST /api/v1/admin/users/{user_id}/enable
Authorization: Bearer <access_token>

Response: { "id": "...", "disabled": false }
```

#### View Audit Logs
```http
GET /api/v1/admin/audit-logs?page=1&limit=50
Authorization: Bearer <access_token>

Response: {
  "logs": [
    {
      "id": "...",
      "actor_email": "admin@example.com",
      "action": "role_change",
      "resource_type": "user",
      "resource_id": "...",
      "before": { "role": "user" },
      "after": { "role": "restaurant_admin" },
      "reason": "Promoted to manage restaurant",
      "timestamp": "2024-04-22T10:30:00Z"
    }
  ]
}
```

---

## 📊 Database Models

### Users Collection
```json
{
  "_id": "ObjectId",
  "email": "user@example.com",
  "password_hash": "bcrypt_hash",
  "name": "John Doe",
  "role": "user|restaurant_admin|superadmin",
  "restaurant_ids": ["rest_id_1", "rest_id_2"],
  "is_verified": true,
  "disabled": false,
  "token_version": 1,
  "created_at": "2024-04-22T10:30:00Z"
}
```

### Restaurants Collection
```json
{
  "_id": "ObjectId",
  "name": "Pizza Palace",
  "slug": "pizza-palace",
  "owner_email": "owner@example.com",
  "description": "Best pizzas in town",
  "address": "123 Main St",
  "phone": "555-1234",
  "approved": true,
  "disabled": false,
  "created_at": "2024-04-22T10:30:00Z"
}
```

### Menu Items Collection
```json
{
  "_id": "ObjectId",
  "restaurant_id": "...",
  "name": "Margherita Pizza",
  "price": 12.99,
  "description": "Classic cheese pizza",
  "is_available": true,
  "created_at": "2024-04-22T10:30:00Z"
}
```

### Orders Collection
```json
{
  "_id": "ObjectId",
  "user_email": "customer@example.com",
  "restaurant_id": "...",
  "items": [
    {
      "menu_item_id": "...",
      "name": "Margherita Pizza",
      "price": 12.99,
      "quantity": 2
    }
  ],
  "total_amount": 25.98,
  "status": "pending|accepted|preparing|ready|out_for_delivery|delivered|cancelled|rejected",
  "special_instructions": "No onions",
  "created_at": "2024-04-22T10:30:00Z",
  "updated_at": "2024-04-22T10:35:00Z"
}
```

### Refresh Tokens Collection
```json
{
  "_id": "ObjectId",
  "user_email": "user@example.com",
  "token_hash": "sha256_hash",
  "expires_at": "2024-04-29T10:30:00Z",
  "revoked": false,
  "replaced_by_token": "new_token_hash",
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1",
  "created_at": "2024-04-22T10:30:00Z"
}
```

### Audit Logs Collection
```json
{
  "_id": "ObjectId",
  "actor_email": "admin@example.com",
  "action": "role_change|restaurant_update|menu_create|order_status_update",
  "resource_type": "user|restaurant|menu_item|order",
  "resource_id": "...",
  "before": {},
  "after": {},
  "reason": "Promoted to manage restaurant",
  "timestamp": "2024-04-22T10:30:00Z"
}
```

---

## 🎯 Order Status Workflow

### Customer View
```
pending ──→ accepted ──→ preparing ──→ ready ──→ out_for_delivery ──→ delivered
   ↓           ↓            ↓
rejected    cancelled      cancelled
```

### Restaurant Admin View
```
pending ──→ preparing ──→ ready ──→ out_for_delivery ──→ delivered
```

---

## 🔐 Security Features

### 🛡️ Authentication
- **JWT Bearer Tokens** with 59-minute expiration
- **Refresh Token Rotation** - New token issued on refresh, old one marked revoked
- **Email Verification** - 15-minute token validity
- **Password Reset** - 30-minute token validity
- **Secure Password Hashing** - Bcrypt with passlib

### 🚨 Authorization
- **Role-Based Access Control (RBAC)** - 3 roles with granular permissions
- **Restaurant Isolation** - Admins can only access assigned restaurants
- **User Data Privacy** - Users can only access their own data
- **Token Versioning** - Revoke all sessions by incrementing version

### 🔒 Session Management
- **Refresh Token Reuse Detection** - Prevents token theft
- **Per-Session Tracking** - IP address and User-Agent logging
- **Multi-Device Support** - Users can be logged in from multiple devices
- **Selective Logout** - Logout from single device or all devices

### 📊 Audit & Compliance
- **Complete Audit Trail** - All actions logged with actor info
- **Before/After Snapshots** - Track what changed and when
- **Immutable Logs** - Cannot be modified after creation
- **Rate Limiting** - 10 requests per 60 seconds

---

## 💡 Learning Objectives for Frontend Developers

### 🔐 **Authentication Flow**
Learn how to implement:
```
1. User Registration with email verification
2. Secure password hashing and validation
3. JWT token management (access & refresh)
4. Token refresh and rotation strategies
5. Multi-device session management
6. Password reset via email
7. Logout and token revocation
```

### 🏗️ **Role-Based UI Architecture**
Understand how to build:
```
1. Different UI layouts based on user roles
2. Conditional rendering of features based on permissions
3. Protected routes and component-level access control
4. Admin dashboards with user management
5. Restaurant owner portals with menu/order management
6. Customer interfaces for browsing and ordering
```

### 🏪 **Multi-Tenancy Implementation**
Learn patterns for:
```
1. Data isolation by restaurant/tenant
2. Query filtering based on user context
3. Permission checks before data access
4. Nested resources (restaurant → menu items)
5. Multi-restaurant admin capabilities
```

### 📦 **Complex State Management**
Master patterns for:
```
1. Authentication state persistence
2. User context across application
3. Role-based feature toggles
4. Cache invalidation after mutations
5. Real-time status updates (WebSocket integration ready)
```

### 🔔 **Notification Systems**
Integrate:
```
1. Email notifications
2. Order status update handling
3. Verification email workflows
4. Error notifications from API
5. Toast/Alert UI patterns
```

---

## 🚀 Integration Examples

### React Example - Login Flow
```jsx
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

// Login function
async function login(email, password) {
  try {
    const response = await axios.post(`${API_BASE}/auth/login`, {
      email,
      password
    });
    
    // Store tokens
    localStorage.setItem('accessToken', response.data.access_token);
    localStorage.setItem('refreshToken', response.data.refresh_token);
    
    return response.data;
  } catch (error) {
    console.error('Login failed:', error.response.data);
  }
}

// Protected API call
async function getCurrentUser() {
  const token = localStorage.getItem('accessToken');
  
  try {
    const response = await axios.get(`${API_BASE}/users/user`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    if (error.response.status === 401) {
      // Token expired, try refresh
      await refreshToken();
    }
  }
}

// Refresh token
async function refreshToken() {
  const token = localStorage.getItem('refreshToken');
  
  try {
    const response = await axios.post(`${API_BASE}/auth/refresh`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    localStorage.setItem('accessToken', response.data.access_token);
    localStorage.setItem('refreshToken', response.data.refresh_token);
  } catch (error) {
    // Refresh failed, redirect to login
    localStorage.clear();
    window.location.href = '/login';
  }
}
```

### Vue Example - Role-Based UI
```vue
<template>
  <div v-if="user" class="dashboard">
    <!-- Customer View -->
    <div v-if="user.role === 'user'">
      <CustomerDashboard :user="user" />
    </div>
    
    <!-- Restaurant Admin View -->
    <div v-else-if="user.role === 'restaurant_admin'">
      <RestaurantAdminDashboard :user="user" />
    </div>
    
    <!-- Superadmin View -->
    <div v-else-if="user.role === 'superadmin'">
      <AdminDashboard :user="user" />
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      user: null
    }
  },
  async mounted() {
    this.user = await this.getCurrentUser();
  },
  methods: {
    async getCurrentUser() {
      const response = await axios.get(`${API_BASE}/users/user`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });
      return response.data;
    }
  }
}
</script>
```

### Angular Example - HTTP Interceptor
```typescript
import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.authService.getAccessToken();
    
    if (token) {
      request = request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      });
    }
    
    return next.handle(request);
  }
}
```

---

## 📁 Project Structure Explained

```
backend-service/
├── main.py                    # FastAPI app entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
│
├── core/                      # Core infrastructure
│   ├── authorization.py       # Role-based permission checks
│   ├── dependencies.py        # FastAPI dependency injection
│   ├── exceptions.py          # Custom exception classes
│   ├── middleware.py          # Request middleware (rate limiting, request ID)
│   └── rate_limiter.py        # Redis-based rate limiting
│
├── routes/                    # HTTP endpoint handlers
│   ├── auth.py               # Authentication endpoints
│   ├── user_routes.py        # User profile endpoints
│   ├── restaurant_routes.py  # Restaurant management
│   ├── menu_routes.py        # Menu management
│   ├── order_route.py        # Customer order endpoints
│   ├── restaurant_order_routes.py  # Restaurant order management
│   └── admin_routes.py       # Admin system management
│
├── services/                  # Business logic layer
│   ├── auth_service.py       # Authentication logic
│   ├── user_service.py       # User operations
│   ├── restaurant_service.py # Restaurant operations
│   ├── menu_service.py       # Menu operations
│   ├── user_order_service.py # Customer order logic
│   ├── restaurant_order_service.py # Restaurant order logic
│   └── admin_service.py      # Admin operations
│
├── models/                    # Pydantic data models
│   ├── auth_models.py        # Auth-related models
│   ├── user.py               # User data model
│   ├── restaurant.py         # Restaurant data model
│   ├── menu.py               # Menu item data model
│   ├── order.py              # Order data model
│   ├── refresh_tokens.py     # Token data model
│   ├── admin.py              # Admin operations model
│   └── __init__.py
│
├── db/                        # Database operations
│   ├── db_operation.py       # MongoDB operations helper
│   ├── redis_client.py       # Redis client setup
│   └── __init__.py
│
├── utils/                     # Utility functions
│   ├── jwt_handler.py        # JWT token creation/validation
│   ├── hash.py               # Password hashing utilities
│   ├── email.py              # Email sending
│   ├── token.py              # Token utilities
│   ├── logger.py             # Logging setup
│   └── __init__.py
│
├── settings/                  # Configuration
│   ├── config.py             # Environment variables & settings
│   └── __init__.py
│
└── scripts/                   # Utility scripts
    ├── seed_superadmin.py    # Create initial superadmin
    └── __init__.py
```

---

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.116.1 | Modern async web framework |
| **Database** | MongoDB | NoSQL document store |
| **Cache/Rate Limit** | Redis 7.1.0 | In-memory data store |
| **Auth** | PyJWT + cryptography | JWT token handling |
| **Password** | Passlib + bcrypt | Secure password hashing |
| **Validation** | Pydantic 2.11.7 | Data validation |
| **DB Driver** | Motor 3.7.1 | Async MongoDB driver |
| **Email** | SMTP | Email notifications |

---

## 🎓 Learning Paths

### 👶 **Beginner Developer**
Start with understanding:
1. **API Basics** - GET, POST, PUT, DELETE requests
2. **Authentication** - How login/tokens work
3. **Basic Integration** - Call auth and listing endpoints
4. **Simple UI** - Build login form and customer dashboard

### 🧑‍💼 **Intermediate Developer**
Learn about:
1. **Role-Based Access** - Handle different UI for different roles
2. **State Management** - Manage auth state across app
3. **Protected Routes** - Implement route guards
4. **Token Management** - Handle expiration and refresh
5. **Error Handling** - Proper error messages and logging

### 🚀 **Advanced Developer**
Master:
1. **Multi-Tenancy** - Build restaurant admin portals
2. **Complex Workflows** - Order status updates and permissions
3. **Real-time Updates** - WebSocket integration for live orders
4. **Performance** - Caching, pagination, and optimization
5. **Security** - Implement security best practices

---

## 📖 API Documentation

Full interactive documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:
- [ ] WebSocket support for real-time updates
- [ ] Payment integration (Stripe, PayPal)
- [ ] Ratings and reviews system
- [ ] Restaurant analytics dashboard
- [ ] Mobile app backend features
- [ ] Advanced filtering and sorting
- [ ] Internationalization support

---

## 📝 License

This project is open source and available for educational purposes.

---

## 🆘 Support & Questions

For questions about:
- **API Integration** - Check the endpoint examples above
- **Frontend Implementation** - See the React/Vue/Angular examples
- **Database Queries** - Check the models section
- **Deployment** - See the Dockerfile for containerization
- **Issues** - File an issue on the repository

---

## ⭐ If this project helped you learn, please star it!

Your support motivates us to keep improving and adding more learning resources for the developer community.
