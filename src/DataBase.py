import sqlite3
import random
from typing import List, Dict, Any, Optional
from vars import DB_PATH

class KasebBase:
    def __init__(self):
        self.db_name = DB_PATH
        self.init_database()
    
    def get_connection(self):
        """Create and return a database connection"""
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Initialize all tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                role TEXT DEFAULT 'Basic',
                phone TEXT DEFAULT '',
                card TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                coins INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                mode TEXT NOT NULL,
                username TEXT,
                password TEXT,
                file_id TEXT,
                host TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users (user_id)
            )
        ''')
        
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id),
                FOREIGN KEY (author_id) REFERENCES users (user_id)
            )
        ''')
        
        # Invites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invites (
                user_id INTEGER PRIMARY KEY,
                invite_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # User Management Functions
    def add_user(self, user_id: int, role: str = 'Basic') -> bool:
        """Add a new user to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, role) 
                VALUES (?, ?)
            ''', (user_id, role))
            cursor.execute('''
                INSERT OR IGNORE INTO invites (user_id, invite_count) 
                VALUES (?, 0)
            ''', (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
        finally:
            conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'role': row[1],
                'phone': row[2],
                'card': row[3],
                'status': row[4],
                'coins': row[5],
                'created_at': row[6]
            }
        return None
    
    def update_user_role(self, user_id: int, role: str) -> bool:
        """Update user role"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', (role, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False
        finally:
            conn.close()
    
    def update_user_phone(self, user_id: int, phone: str) -> bool:
        """Update user phone number"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET phone = ? WHERE user_id = ?', (phone, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user phone: {e}")
            return False
        finally:
            conn.close()
    
    def update_user_card(self, user_id: int, card: str) -> bool:
        """Update user card number"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET card = ? WHERE user_id = ?', (card, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user card: {e}")
            return False
        finally:
            conn.close()
    
    def ban_user(self, user_id: int) -> bool:
        """Ban a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET status = ? WHERE user_id = ?', ('banned', user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error banning user: {e}")
            return False
        finally:
            conn.close()
    
    def unban_user(self, user_id: int) -> bool:
        """Unban a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET status = ? WHERE user_id = ?', ('active', user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error unbanning user: {e}")
            return False
        finally:
            conn.close()
    
    def add_coins(self, user_id: int, coins: int) -> bool:
        """Add coins to user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding coins: {e}")
            return False
        finally:
            conn.close()
    
    def get_all_users(self) -> List[int]:
        """Get all user IDs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row and row[0] == 'banned'
    
    def get_user_card(self, user_id: int) -> str:
        """Get user card number"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT card FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ""
    
    def get_user_phone(self, user_id: int) -> str:
        """Get user phone number"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT phone FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ""
    
    # Product Management Functions
    def generate_unique_id(self) -> int:
        """Generate a unique product ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        while True:
            product_id = random.randint(1000, 10000)
            cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
            if not cursor.fetchone():
                conn.close()
                return product_id
    
    def add_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        """Add a new product"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            product_id = self.generate_unique_id()
            cursor.execute('''
                INSERT INTO products (
                    product_id, name, description, price, author_id, 
                    mode, username, password, file_id, host
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_id,
                product_data.get('name'),
                product_data.get('description'),
                product_data.get('price'),
                product_data.get('author_id'),
                product_data.get('mode'),
                product_data.get('username'),
                product_data.get('password'),
                product_data.get('file_id'),
                product_data.get('host')
            ))
            conn.commit()
            return product_id
        except Exception as e:
            print(f"Error adding product: {e}")
            return None
        finally:
            conn.close()
    
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'product_id': row[0],
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'author_id': row[4],
                'mode': row[5],
                'username': row[6],
                'password': row[7],
                'file_id': row[8],
                'host': row[9],
                'created_at': row[10]
            }
        return None
    
    def get_products_by_author(self, author_id: int) -> List[Dict[str, Any]]:
        """Get all products by author"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE author_id = ?', (author_id,))
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                'product_id': row[0],
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'author_id': row[4],
                'mode': row[5],
                'username': row[6],
                'password': row[7],
                'file_id': row[8],
                'host': row[9],
                'created_at': row[10]
            })
        return products
    
    def get_products_by_mode(self, mode: str) -> List[Dict[str, Any]]:
        """Get products by mode"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE mode = ?', (mode,))
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                'product_id': row[0],
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'author_id': row[4],
                'mode': row[5],
                'username': row[6],
                'password': row[7],
                'file_id': row[8],
                'host': row[9],
                'created_at': row[10]
            })
        return products
    
    def search_products_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Search products by name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE name LIKE ?', (f'%{name}%',))
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                'product_id': row[0],
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'author_id': row[4],
                'mode': row[5],
                'username': row[6],
                'password': row[7],
                'file_id': row[8],
                'host': row[9],
                'created_at': row[10]
            })
        return products
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products')
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                'product_id': row[0],
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'author_id': row[4],
                'mode': row[5],
                'username': row[6],
                'password': row[7],
                'file_id': row[8],
                'host': row[9],
                'created_at': row[10]
            })
        return products
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting product: {e}")
            return False
        finally:
            conn.close()
    
    def update_product(self, product_id: int, updates: Dict[str, Any]) -> bool:
        """Update product information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            for key, value in updates.items():
                cursor.execute(f'UPDATE products SET {key} = ? WHERE product_id = ?', (value, product_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating product: {e}")
            return False
        finally:
            conn.close()
    
    # Payment Management Functions
    def add_payment(self, user_id: int, product_id: int, author_id: int, amount: int) -> Optional[int]:
        """Add a payment record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO payments (user_id, product_id, author_id, amount)
                VALUES (?, ?, ?, ?)
            ''', (user_id, product_id, author_id, amount))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error adding payment: {e}")
            return None
        finally:
            conn.close()
    
    def get_payments_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all payments by user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM payments WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        payments = []
        for row in rows:
            payments.append({
                'payment_id': row[0],
                'user_id': row[1],
                'product_id': row[2],
                'author_id': row[3],
                'amount': row[4],
                'status': row[5],
                'created_at': row[6]
            })
        return payments
    
    # Invite Management Functions
    def add_invite(self, user_id: int) -> bool:
        """Increment invite count for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO invites (user_id, invite_count) 
                VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET invite_count = invite_count + 1
            ''', (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding invite: {e}")
            return False
        finally:
            conn.close()
    
    def get_invite_count(self, user_id: int) -> int:
        """Get invite count for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT invite_count FROM invites WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    
    def user_exists(self, user_id: int) -> bool:
        """Check if user exists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists