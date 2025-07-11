# LugX Gaming Platform - Testing Guide

## Quick Test Instructions

### 1. Start All Services

```bash
# Run the test script
./test_services.sh
```

This will:
- Start Game Service on port 8001
- Start Order Service on port 8002
- Start Analytics Service on port 8003
- Start Frontend on port 8080

### 2. Test Frontend Pages

Open your browser and visit:

1. **Homepage**: http://localhost:8080/index.html
   - Check trending games load dynamically
   - Test search functionality
   - Try "Add to Cart" buttons

2. **Shop Page**: http://localhost:8080/shop.html
   - Test category filters
   - Try search functionality
   - Test sorting options
   - Check pagination

3. **Product Details**: http://localhost:8080/product-details.html?id=1
   - Verify product info loads
   - Test image gallery
   - Try "Add to Cart" button
   - Check reviews section

4. **Authentication**:
   - **Login**: http://localhost:8080/login.html
   - **Register**: http://localhost:8080/register.html
   - Test form validation
   - Try creating an account

5. **Shopping Cart**: http://localhost:8080/cart.html
   - View cart items
   - Update quantities
   - Remove items

### 3. Test API Endpoints

Visit the API documentation:
- Game Service: http://localhost:8001/docs
- Order Service: http://localhost:8002/docs
- Analytics Service: http://localhost:8003/docs

### 4. Common Test Scenarios

1. **Browse and Add to Cart (Guest)**:
   - Browse shop without logging in
   - Add items to cart
   - Cart persists in localStorage

2. **User Registration and Login**:
   - Register new account
   - Login with credentials
   - Cart syncs to server

3. **Product Search and Filter**:
   - Search for games
   - Filter by category
   - Sort by price

### 5. Stop All Services

```bash
./stop_services.sh
```

## What's Working

✅ **Frontend Pages**:
- Homepage with dynamic content
- Shop with search/filter/sort
- Product details with API integration
- Authentication pages (login/register)
- Shopping cart

✅ **API Services**:
- Game Service (catalog, search, categories)
- Order Service (auth, cart, orders)
- Analytics Service (events, dashboards)

✅ **Features**:
- Real-time search
- Cart persistence
- User authentication
- Product recommendations
- Analytics tracking

## Known Limitations

- Payment processing is simulated
- Email notifications are mocked
- Some images use placeholders
- Guest checkout not implemented yet

## Troubleshooting

If services fail to start:
1. Check Python 3.8+ is installed
2. Ensure ports 8001-8003, 8080 are free
3. Check logs in `logs/` directory
4. Try running `pip install -r requirements.txt` in each service directory

If frontend doesn't load:
1. Check browser console for errors
2. Ensure all services are running
3. Try hard refresh (Ctrl+F5)
4. Check network tab for failed requests