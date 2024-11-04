import sqlite3
from datetime import datetime

# Connect to (or create) the SQLite database
conn = sqlite3.connect("inventory.db")
cursor = conn.cursor()

# Set up tables
def setup_database():
    # Main tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL UNIQUE,
            quantity INTEGER NOT NULL,
            price_inr REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            quantity_sold INTEGER NOT NULL,
            sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_price_inr REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            quantity_added INTEGER NOT NULL,
            update_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Archive tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archive_date DATE NOT NULL,
            product_name TEXT NOT NULL,
            quantity_added INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_log_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archive_date DATE NOT NULL,
            product_name TEXT NOT NULL,
            quantity_sold INTEGER NOT NULL,
            total_price_inr REAL NOT NULL,
            sale_date DATETIME
        )
    """)
    conn.commit()

# Initialize database tables
setup_database()

# Function to add items to inventory
def add_to_inventory(product_name, quantity, price_inr):
    cursor.execute("""
        INSERT INTO inventory_log (product_name, quantity_added) VALUES (?, ?)
    """, (product_name, quantity))

    # Check if the product already exists in inventory
    cursor.execute("SELECT quantity FROM inventory WHERE product_name = ?", (product_name,))
    result = cursor.fetchone()
    if result:
        cursor.execute("""
            UPDATE inventory SET quantity = quantity + ?, price_inr = ? WHERE product_name = ?
        """, (quantity, price_inr, product_name))
    else:
        cursor.execute("""
            INSERT INTO inventory (product_name, quantity, price_inr) VALUES (?, ?, ?)
        """, (product_name, quantity, price_inr))

    conn.commit()

# Function to record a sale with a specific sale price
def record_sale(product_name, quantity, sale_price_inr):
    # Check if enough quantity is available
    cursor.execute("SELECT quantity FROM inventory WHERE product_name = ?", (product_name,))
    result = cursor.fetchone()
    
    if result and result[0] >= quantity:
        # Calculate the total price for this sale
        total_price_inr = sale_price_inr * quantity

        # Log the sale in sales_log
        cursor.execute("""
            INSERT INTO sales_log (product_name, quantity_sold, total_price_inr) VALUES (?, ?, ?)
        """, (product_name, quantity, total_price_inr))

        # Update current inventory
        cursor.execute("""
            UPDATE inventory SET quantity = quantity - ?
            WHERE product_name = ?
        """, (quantity, product_name))
        
        conn.commit()
        
        print(f"Sold {quantity} {product_name} for ₹{total_price_inr:.2f} at ₹{sale_price_inr:.2f} each")
    else:
        print(f"Not enough {product_name} in inventory to complete the sale.")

# Function to view current inventory
def view_inventory():
    cursor.execute("SELECT product_name, quantity, price_inr FROM inventory")
    inventory = cursor.fetchall()

    print("Current Inventory:")
    for item in inventory:
        product_name, quantity, price_inr = item
        print(f"{product_name}: {quantity} units available at ₹{price_inr:.2f} each")

# Function to archive and clear daily logs
def archive_daily_logs():
    # Get today's date
    archive_date = datetime.now().date()
    
    # Archive inventory additions
    cursor.execute("""
        INSERT INTO inventory_archive (archive_date, product_name, quantity_added)
        SELECT ?, product_name, quantity_added FROM inventory_log
    """, (archive_date,))
    
    # Archive sales logs
    cursor.execute("""
        INSERT INTO sales_log_archive (archive_date, product_name, quantity_sold, total_price_inr, sale_date)
        SELECT ?, product_name, quantity_sold, total_price_inr, sale_date FROM sales_log
    """, (archive_date,))

    # Clear current day’s logs from inventory_log and sales_log
    cursor.execute("DELETE FROM inventory_log")
    cursor.execute("DELETE FROM sales_log")

    conn.commit()
    print(f"Archived and cleared logs for {archive_date}")

# Function to retrieve archived logs for a specific day
def get_archived_logs(date):
    # Fetch inventory additions for the specified date
    cursor.execute("SELECT product_name, quantity_added FROM inventory_archive WHERE archive_date = ?", (date,))
    inventory_logs = cursor.fetchall()

    # Fetch sales records for the specified date
    cursor.execute("""
        SELECT product_name, quantity_sold, total_price_inr, sale_date
        FROM sales_log_archive
        WHERE archive_date = ?
    """, (date,))
    sales_logs = cursor.fetchall()

    print(f"\nArchived Logs for {date}:")
    print("\nInventory Additions:")
    for log in inventory_logs:
        print(f"+ {log[1]} {log[0]}")

    print("\nSales Logs:")
    for log in sales_logs:
        print(f"- {log[1]} {log[0]} ₹{log[2]:.2f} (Sold on {log[3]})")

# Usage example
add_to_inventory("MacBook Pro", 5, 82000)
record_sale("MacBook Pro", 2, 85000)  # Selling at a custom price of ₹85000 per unit
view_inventory()

# End of day: archive and clear logs
archive_daily_logs()

# Retrieve archived logs for a specific date (replace with today’s date or any archived date)
get_archived_logs(datetime.now().date())

# Close connection
conn.close()

