from unittest import TestCase, main
import db_handler as db
from models.Customer import Customer
from models.Item import Item

class PrivateTests(TestCase):
    def test_edit_customer_partial_name(self):
        # Setup: add a customer
        c = Customer(customer_id="PRIV_CUST_1", name="Original Name", email="orig@test.com", address="123 Street, City, ST 12345")
        db.cur.execute("DELETE FROM customer WHERE c_customer_id = ?", (c.customer_id,))
        db.add_customer(c)
        db.save_changes()

        # Act: Update ONLY the name
        db.edit_customer(original_customer_id="PRIV_CUST_1", new_customer=Customer(name="New Name"))
        db.save_changes()

        # Verify
        results = db.get_filtered_customers(Customer(customer_id="PRIV_CUST_1"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "New Name")
        self.assertEqual(results[0].email, "orig@test.com") # Should remain unchanged
        self.assertEqual(results[0].address, "123 Street, City, ST 12345") # Should remain unchanged

    def test_number_in_stock_calculation(self):
        # Setup: item with 5 owned
        item_id = "PRIV_ITEM_1"
        db.cur.execute("DELETE FROM rental WHERE item_id = ?", (item_id,))
        db.cur.execute("DELETE FROM item WHERE i_item_id = ?", (item_id,))
        db.add_item(Item(item_id=item_id, product_name="Test", brand="B", category="C", manufact="M", current_price=10.0, start_year=2020, num_owned=5))
        
        # Verify initial stock
        self.assertEqual(db.number_in_stock(item_id), 5)

        # Rent 2 copies
        db.rent_item(item_id, "CUST_A")
        db.rent_item(item_id, "CUST_B")
        
        # Verify reduced stock
        self.assertEqual(db.number_in_stock(item_id), 3)

        # Cleanup
        db.cur.execute("DELETE FROM rental WHERE item_id = ?", (item_id,))
        db.cur.execute("DELETE FROM item WHERE i_item_id = ?", (item_id,))
        db.save_changes()

if __name__ == "__main__":
    main()
