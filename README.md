# Nook & Nest — Flask E-commerce Store

A Flask e-commerce portfolio project featuring a product catalog, shopping cart, user accounts, checkout/orders, and stock-aware inventory handling.

## Included functionality

- Product catalog with category filtering and search
- Product detail pages and stock availability
- Session-based shopping cart with quantity updates
- User registration, sign in, and order history
- Checkout flow with stock locking and automatic inventory reduction
- Demo payment option and a clearly documented production payment integration point
- SQLite-backed product, inventory, category, and order management

## Run locally

```bash
cd ecommerce_store
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Open `http://127.0.0.1:5000/`. On its first run, the application creates `store.db` and loads the demo catalog automatically. Create an account through the site before checking out.

The original Django source is retained for reference, but it is no longer needed to run the app.

## Payment note

The checkout’s **Demo Card** creates a successful simulated payment reference. It does not submit card details or process money. Before production, integrate a PCI-compliant provider such as Razorpay or Stripe from the server using secret keys stored in environment variables and verified webhooks.

See [`docs/PROJECT_DOCUMENTATION.md`](docs/PROJECT_DOCUMENTATION.md) for the report and presentation material.
