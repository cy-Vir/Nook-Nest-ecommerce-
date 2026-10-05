# Nook & Nest presentation outline

1. **Title:** Nook & Nest — Django E-commerce Website.
2. **Problem:** Small stores need a simple digital catalog, order capture, and stock tracking.
3. **Solution:** One Django storefront for shopping plus an admin workspace for operations.
4. **Features:** Catalog, cart, accounts, checkout, orders, inventory, admin dashboard.
5. **Catalog screen:** Search and category filters make products easy to discover.
6. **Cart screen:** Session-based quantities and calculated totals.
7. **Checkout:** Authentication and shipping form; Demo Card clearly signals simulated payment.
8. **Order processing:** Order and line-item records preserve price and quantity history.
9. **Inventory:** Checkout uses database locking and decreases inventory only when stock exists.
10. **Payment production plan:** Stripe/Razorpay hosted payment + verified webhooks + environment secrets.
11. **Future scope:** Coupons, reviews, real delivery tracking, staff roles, REST API, analytics.
