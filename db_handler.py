from MARIADB_CREDS import DB_CONFIG
from mariadb import connect
from models.RentalHistory import RentalHistory
from models.Waitlist import Waitlist
from models.Item import Item
from models.Rental import Rental
from models.Customer import Customer
from datetime import date, timedelta


conn = connect(user=DB_CONFIG["username"], password=DB_CONFIG["password"], host=DB_CONFIG["host"],
               database=DB_CONFIG["database"], port=DB_CONFIG["port"])


cur = conn.cursor()


def add_item(new_item: Item = None):
    """
    new_item - An Item object containing a new item to be inserted into the DB in the item table.
        new_item and its attributes will never be None.
    """
    # generate new item sk
    cur.execute("SELECT COALESCE(MAX(i_item_sk), 0) + 1 FROM item")
    new_item_sk = cur.fetchone()[0]

    rec_start_date = f"{new_item.start_year}-01-01"

    cur.execute(
        """
        INSERT INTO item (
            i_item_sk,
            i_item_id,
            i_rec_start_date,
            i_product_name,
            i_brand,
            i_class,
            i_category,
            i_manufact,
            i_current_price,
            i_num_owned
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_item_sk,
            new_item.item_id,
            rec_start_date,
            new_item.product_name,
            new_item.brand,
            None,
            new_item.category,
            new_item.manufact,
            new_item.current_price,
            new_item.num_owned,
        )
    )


def add_customer(new_customer: Customer = None):
    """
    new_customer - A Customer object containing a new customer to be inserted into the DB in the customer table.
        new_customer and its attributes will never be None.
    """
    # split full name into first and last name

    name_parts = new_customer.name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # parse address string
    # format: "123 Main St, Gainesville, FL 32601"
    address_parts = new_customer.address.split(",")

    street_part = address_parts[0].strip()
    city = address_parts[1].strip()
    state_zip = address_parts[2].strip()

    # Split street into number + name
    street_split = street_part.split(" ", 1)
    street_number = street_split[0]
    street_name = street_split[1] if len(street_split) > 1 else ""

    # Split state and zip
    state_zip_split = state_zip.split()
    state = state_zip_split[0]
    zip_code = state_zip_split[1] if len(state_zip_split) > 1 else ""

    # generate new address surrogate key
    cur.execute("SELECT COALESCE(MAX(ca_address_sk), 0) + 1 FROM customer_address")
    new_address_sk = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO customer_address (
            ca_address_sk,
            ca_street_number,
            ca_street_name,
            ca_city,
            ca_state,
            ca_zip
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            new_address_sk,
            street_number,
            street_name,
            city,
            state,
            zip_code,
        )
    )
    
    # generate new customer surrogate key
    cur.execute("SELECT COALESCE(MAX(c_customer_sk), 0) + 1 FROM customer")
    new_customer_sk = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO customer (
            c_customer_sk,
            c_customer_id,
            c_first_name,
            c_last_name,
            c_email_address,
            c_current_addr_sk
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            new_customer_sk,
            new_customer.customer_id,
            first_name,
            last_name,
            new_customer.email,
            new_address_sk,
        )
    )


def edit_customer(original_customer_id: str = None, new_customer: Customer = None):
    """
    original_customer_id - A string containing the customer id for the customer to be edited.
    new_customer - A Customer object containing attributes to update. If an attribute is None, it should not be altered.
    """
    # Get current customer and address info
    cur.execute("SELECT c_current_addr_sk, c_first_name, c_last_name, c_email_address FROM customer WHERE c_customer_id = ?", (original_customer_id,))
    row = cur.fetchone()
    if not row:
        return
    
    addr_sk, first_name, last_name, email = row

    # Only split name if provided
    if new_customer.name:
        name_parts = new_customer.name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    if new_customer.email:
        email = new_customer.email

    # Update customer table
    cur.execute(
        """
        UPDATE customer 
        SET c_customer_id = COALESCE(?, c_customer_id),
            c_first_name = ?,
            c_last_name = ?,
            c_email_address = ?
        WHERE c_customer_id = ?
        """,
        (new_customer.customer_id, first_name, last_name, email, original_customer_id)
    )

    # Update address table if address provided
    if new_customer.address:
        try:
            address_parts = new_customer.address.split(",")
            street_part = address_parts[0].strip()
            city = address_parts[1].strip()
            state_zip = address_parts[2].strip()

            street_split = street_part.split(" ", 1)
            street_number = street_split[0]
            street_name = street_split[1] if len(street_split) > 1 else ""

            state_zip_split = state_zip.split()
            state = state_zip_split[0]
            zip_code = state_zip_split[1] if len(state_zip_split) > 1 else ""

            cur.execute(
                """
                UPDATE customer_address
                SET ca_street_number = ?,
                    ca_street_name = ?,
                    ca_city = ?,
                    ca_state = ?,
                    ca_zip = ?
                WHERE ca_address_sk = ?
                """,
                (street_number, street_name, city, state, zip_code, addr_sk)
            )
        except (IndexError, ValueError):
            # If address format is invalid, we skip updating it
            pass


def rent_item(item_id: str = None, customer_id: str = None):
    """
    item_id - A string containing the Item ID for the item being rented.
    customer_id - A string containing the customer id of the customer renting the item.
    """
    rental_date = date.today()
    due_date = rental_date + timedelta(days=14)
    cur.execute("INSERT INTO rental (item_id, customer_id, rental_date, due_date) VALUES (?, ?, ?, ?)",
                (item_id, customer_id, rental_date, due_date))


def waitlist_customer(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's new place in line.
    """
    new_pos = line_length(item_id) + 1
    cur.execute("INSERT INTO waitlist (item_id, customer_id, place_in_line) VALUES (?, ?, ?)",
                (item_id, customer_id, new_pos))
    return new_pos

def update_waitlist(item_id: str = None):
    """
    Removes person at position 1 and shifts everyone else down by 1.
    """
    cur.execute("DELETE FROM waitlist WHERE item_id = ? AND place_in_line = 1", (item_id,))
    cur.execute("UPDATE waitlist SET place_in_line = place_in_line - 1 WHERE item_id = ?", (item_id,))


def return_item(item_id: str = None, customer_id: str = None):
    """
    Moves a rental from rental to rental_history with return_date = today.
    """
    cur.execute("SELECT rental_date, due_date FROM rental WHERE item_id = ? AND customer_id = ?",
                (item_id, customer_id))
    row = cur.fetchone()
    if row:
        rental_date, due_date = row
        return_date = date.today()
        cur.execute("DELETE FROM rental WHERE item_id = ? AND customer_id = ?", (item_id, customer_id))
        cur.execute("INSERT INTO rental_history (item_id, customer_id, rental_date, due_date, return_date) VALUES (?, ?, ?, ?, ?)",
                    (item_id, customer_id, rental_date, due_date, return_date))


def grant_extension(item_id: str = None, customer_id: str = None):
    """
    Adds 14 days to the due_date.
    """
    cur.execute("UPDATE rental SET due_date = DATE_ADD(due_date, INTERVAL 14 DAY) WHERE item_id = ? AND customer_id = ?",
                (item_id, customer_id))


def get_filtered_items(filter_attributes: Item = None,
                       use_patterns: bool = False,
                       min_price: float = -1,
                       max_price: float = -1,
                       min_start_year: int = -1,
                       max_start_year: int = -1) -> list[Item]:
    """
    Returns a list of Item objects matching the filters.
    """
    query = "SELECT * FROM item WHERE 1=1"
    params = []
    op = "LIKE" if use_patterns else "="

    if filter_attributes:
        if filter_attributes.item_id:
            query += f" AND i_item_id {op} ?"
            params.append(filter_attributes.item_id)
        if filter_attributes.product_name:
            query += f" AND i_product_name {op} ?"
            params.append(filter_attributes.product_name)
        if filter_attributes.brand:
            query += f" AND i_brand {op} ?"
            params.append(filter_attributes.brand)
        if filter_attributes.category:
            query += f" AND i_category {op} ?"
            params.append(filter_attributes.category)
        if filter_attributes.manufact:
            query += f" AND i_manufact {op} ?"
            params.append(filter_attributes.manufact)
        if filter_attributes.current_price != -1:
            query += " AND i_current_price = ?"
            params.append(filter_attributes.current_price)
        if filter_attributes.num_owned != -1:
            query += " AND i_num_owned = ?"
            params.append(filter_attributes.num_owned)

    if min_price != -1:
        query += " AND i_current_price >= ?"
        params.append(min_price)
    if max_price != -1:
        query += " AND i_current_price <= ?"
        params.append(max_price)
    if min_start_year != -1:
        query += " AND YEAR(i_rec_start_date) >= ?"
        params.append(min_start_year)
    if max_start_year != -1:
        query += " AND YEAR(i_rec_start_date) <= ?"
        params.append(max_start_year)

    cur.execute(query, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        item = Item(
            item_id=row[1].strip() if row[1] else None,
            product_name=row[3].strip() if row[3] else None,
            brand=row[4].strip() if row[4] else None,
            category=row[6].strip() if row[6] else None,
            manufact=row[7].strip() if row[7] else None,
            current_price=float(row[8]) if row[8] is not None else -1.0,
            start_year=row[2].year if row[2] else -1,
            num_owned=row[9] if row[9] is not None else -1
        )
        results.append(item)

    return results


def get_filtered_customers(filter_attributes: Customer = None, use_patterns: bool = False) -> list[Customer]:
    """
    Returns a list of Customer objects matching the filters.
    """
    query = """
    SELECT
        c.c_customer_id,
        c.c_first_name,
        c.c_last_name,
        c.c_email_address,
        ca.ca_street_number,
        ca.ca_street_name,
        ca.ca_city,
        ca.ca_state,
        ca.ca_zip
    FROM customer c
    JOIN customer_address ca
        ON c.c_current_addr_sk = ca.ca_address_sk
    WHERE 1=1
    """
    params = []
    op = "LIKE" if use_patterns else "="

    if filter_attributes:
        if filter_attributes.customer_id:
            query += f" AND c.c_customer_id {op} ?"
            params.append(filter_attributes.customer_id)
        if filter_attributes.name:
            query += f" AND CONCAT(TRIM(c.c_first_name), ' ', TRIM(c.c_last_name)) {op} ?"
            params.append(filter_attributes.name)
        if filter_attributes.email:
            query += f" AND c.c_email_address {op} ?"
            params.append(filter_attributes.email)
        if filter_attributes.address:
            query += f" AND CONCAT(TRIM(ca.ca_street_number), ' ', TRIM(ca.ca_street_name), ', ', TRIM(ca.ca_city), ', ', TRIM(ca.ca_state), ' ', TRIM(ca.ca_zip)) {op} ?"
            params.append(filter_attributes.address)

    cur.execute(query, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        first_name = row[1].strip() if row[1] else ""
        last_name = row[2].strip() if row[2] else ""
        name = f"{first_name} {last_name}".strip()
        
        street_num = row[4].strip() if row[4] else ""
        street_name = row[5].strip() if row[5] else ""
        city = row[6].strip() if row[6] else ""
        state = row[7].strip() if row[7] else ""
        zip_code = row[8].strip() if row[8] else ""
        
        address = f"{street_num} {street_name}, {city}, {state} {zip_code}"

        results.append(Customer(
            customer_id=row[0].strip() if row[0] else None,
            name=name,
            address=address,
            email=row[3].strip() if row[3] else None
        ))

    return results


def get_filtered_rentals(filter_attributes: Rental = None,
                         min_rental_date: str = None,
                         max_rental_date: str = None,
                         min_due_date: str = None,
                         max_due_date: str = None) -> list[Rental]:
    """
    Returns a list of Rental objects matching the filters.
    """
    query = "SELECT * FROM rental WHERE 1=1"
    params = []

    if filter_attributes:
        if filter_attributes.item_id:
            query += " AND item_id = ?"
            params.append(filter_attributes.item_id)
        if filter_attributes.customer_id:
            query += " AND customer_id = ?"
            params.append(filter_attributes.customer_id)
        if filter_attributes.rental_date:
            query += " AND rental_date = ?"
            params.append(filter_attributes.rental_date)
        if filter_attributes.due_date:
            query += " AND due_date = ?"
            params.append(filter_attributes.due_date)

    if min_rental_date:
        query += " AND rental_date >= ?"
        params.append(min_rental_date)
    if max_rental_date:
        query += " AND rental_date <= ?"
        params.append(max_rental_date)
    if min_due_date:
        query += " AND due_date >= ?"
        params.append(min_due_date)
    if max_due_date:
        query += " AND due_date <= ?"
        params.append(max_due_date)

    cur.execute(query, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        results.append(Rental(
            item_id=row[0].strip() if row[0] else None,
            customer_id=row[1].strip() if row[1] else None,
            rental_date=str(row[2]) if row[2] else None,
            due_date=str(row[3]) if row[3] else None
        ))

    return results


def get_filtered_rental_histories(filter_attributes: RentalHistory = None,
                                  min_rental_date: str = None,
                                  max_rental_date: str = None,
                                  min_due_date: str = None,
                                  max_due_date: str = None,
                                  min_return_date: str = None,
                                  max_return_date: str = None) -> list[RentalHistory]:
    """
    Returns a list of RentalHistory objects matching the filters.
    """
    query = "SELECT * FROM rental_history WHERE 1=1"
    params = []

    if filter_attributes:
        if filter_attributes.item_id:
            query += " AND item_id = ?"
            params.append(filter_attributes.item_id)
        if filter_attributes.customer_id:
            query += " AND customer_id = ?"
            params.append(filter_attributes.customer_id)
        if filter_attributes.rental_date:
            query += " AND rental_date = ?"
            params.append(filter_attributes.rental_date)
        if filter_attributes.due_date:
            query += " AND due_date = ?"
            params.append(filter_attributes.due_date)
        if filter_attributes.return_date:
            query += " AND return_date = ?"
            params.append(filter_attributes.return_date)

    if min_rental_date:
        query += " AND rental_date >= ?"
        params.append(min_rental_date)
    if max_rental_date:
        query += " AND rental_date <= ?"
        params.append(max_rental_date)
    if min_due_date:
        query += " AND due_date >= ?"
        params.append(min_due_date)
    if max_due_date:
        query += " AND due_date <= ?"
        params.append(max_due_date)
    if min_return_date:
        query += " AND return_date >= ?"
        params.append(min_return_date)
    if max_return_date:
        query += " AND return_date <= ?"
        params.append(max_return_date)

    cur.execute(query, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        results.append(RentalHistory(
            item_id=row[0].strip() if row[0] else None,
            customer_id=row[1].strip() if row[1] else None,
            rental_date=str(row[2]) if row[2] else None,
            due_date=str(row[3]) if row[3] else None,
            return_date=str(row[4]) if row[4] else None
        ))

    return results


def get_filtered_waitlist(filter_attributes: Waitlist = None,
                          min_place_in_line: int = -1,
                          max_place_in_line: int = -1) -> list[Waitlist]:
    """
    Returns a list of Waitlist objects matching the filters.
    """
    query = "SELECT * FROM waitlist WHERE 1=1"
    params = []

    if filter_attributes:
        if filter_attributes.item_id:
            query += " AND item_id = ?"
            params.append(filter_attributes.item_id)
        if filter_attributes.customer_id:
            query += " AND customer_id = ?"
            params.append(filter_attributes.customer_id)
        if filter_attributes.place_in_line != -1:
            query += " AND place_in_line = ?"
            params.append(filter_attributes.place_in_line)

    if min_place_in_line != -1:
        query += " AND place_in_line >= ?"
        params.append(min_place_in_line)
    if max_place_in_line != -1:
        query += " AND place_in_line <= ?"
        params.append(max_place_in_line)

    cur.execute(query, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        results.append(Waitlist(
            item_id=row[0].strip() if row[0] else None,
            customer_id=row[1].strip() if row[1] else None,
            place_in_line=row[2] if row[2] is not None else -1
        ))

    return results


def number_in_stock(item_id: str = None) -> int:
    """
    Returns num_owned - active rentals. Returns -1 if item doesn't exist.
    """
    raise NotImplementedError("you must implement this function")


def place_in_line(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's place_in_line, or -1 if not on waitlist.
    """
    cur.execute("SELECT place_in_line FROM waitlist WHERE item_id = ? AND customer_id = ?", (item_id, customer_id))
    row = cur.fetchone()
    if row:
        return row[0]
    return -1


def line_length(item_id: str = None) -> int:
    """
    Returns how many people are on the waitlist for this item.
    """
    cur.execute("SELECT COUNT(*) FROM waitlist WHERE item_id = ?", (item_id,))
    row = cur.fetchone()
    return row[0] if row else 0


def save_changes():
    """
    Commits all changes made to the db.
    """
    conn.commit()


def close_connection():
    """
    Closes the cursor and connection.
    """
    cur.close()
    conn.close()

