import sqlite3


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id):
        with self.connection:
            self.cursor.execute(f"INSERT INTO users (user_id) VALUES ({user_id})")

    def user_exists(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM users WHERE user_id = {user_id}")
            return bool(len(self.cursor.fetchall()))

    def delete_user(self, user_id):
        with self.connection:
            self.cursor.execute(f"DELETE FROM users WHERE user_id = {user_id}")

    def get_users(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM users").fetchall()
         
    def get_id_by_mail(self, mail):
        with self.connection:
            return self.cursor.execute("SELECT id FROM users WHERE mail = ?", (mail,)).fetchone()[0]

    def get_step(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT step FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
        
    def set_step(self, step, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE users SET step = ? WHERE user_id = ?", (step, user_id,))
        
    def get_news_number(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT news FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
        
    def set_news_number(self, news, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE users SET news = ? WHERE user_id = ?", (news, user_id,))
        
    def get_sub(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT sub FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
        
    def set_sub(self, sub, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE users SET sub = ? WHERE user_id = ?", (sub, user_id,))
        
    def get_name(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
        
    def set_name(self, name, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id,))
        
    def get_blocked(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT blocked FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
        
    def set_blocked(self, blocked, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE users SET blocked = ? WHERE user_id = ?", (blocked, user_id,))
        
    def get_subed(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT subed FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
        
    def set_subed(self, subed, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE users SET subed = ? WHERE user_id = ?", (subed, user_id,))
    
    def get_free_search(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT free_search FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
        
    def set_free_search(self, free_search, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE users SET free_search = ? WHERE user_id = ?", (free_search, user_id,))
        
    def get_mail(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT mail FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
        
    def set_mail(self, mail, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE users SET mail = ? WHERE user_id = ?", (mail, user_id,))
    
    def get_path(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT path FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
        
    def set_path(self, path, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE users SET path = ? WHERE user_id = ?", (path, user_id,))
        
    def add_item(self, item):
        with self.connection:
            return self.cursor.execute(f"INSERT INTO items (name) VALUES (?)", (item,))
        
    def item_exists(self, name):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM items WHERE name = ?", (name,))
            return bool(len(self.cursor.fetchall()))
        
    def item_exists_by_id(self, id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM items WHERE id = ?", (id,))
            return bool(len(self.cursor.fetchall()))
        
    def delete_item(self, item_id):
        with self.connection:
            self.cursor.execute(f"DELETE FROM items WHERE id = {item_id}")

    def get_item_id(self, name):
        with self.connection:
            return self.cursor.execute("SELECT id FROM items WHERE name = ?", (name,)).fetchone()[0]
        
    def get_items(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM items").fetchall()
    
    def get_text(self, item_id):
        with self.connection:
            return self.cursor.execute("SELECT text FROM items WHERE id = ?", (item_id,)).fetchone()[0]
        
    def set_text(self, text, item_id):
        with self.connection:
            return self.cursor.execute("UPDATE items SET text = ? WHERE id = ?", (text, item_id,))
        
    def get_url(self, item_id):
        with self.connection:
            return self.cursor.execute("SELECT url FROM items WHERE id = ?", (item_id,)).fetchone()[0]
        
    def set_url(self, url, item_id):
        with self.connection:
            return self.cursor.execute("UPDATE items SET url = ? WHERE id = ?", (url, item_id,))
        
    def get_item_name(self, item_id):
        with self.connection:
            return self.cursor.execute("SELECT name FROM items WHERE id = ?", (item_id,)).fetchone()[0]
        
    
    def set_item_name(self, name, item_id):
        with self.connection:
            return self.cursor.execute("UPDATE items SET name = ? WHERE id = ?", (name, item_id,))
        
    def get_media(self, item_id):
        with self.connection:
            return self.cursor.execute("SELECT media FROM items WHERE id = ?", (item_id,)).fetchone()[0]
        
    def set_media(self, media, item_id):
        with self.connection:
            return self.cursor.execute("UPDATE items SET media = ? WHERE id = ?", (media, item_id,))
        
    def get_undone_item_id(self):
        with self.connection:
            return self.cursor.execute("SELECT id FROM items WHERE step != 'done'").fetchone()[0]
    
    def get_item_step(self, item_id):
        with self.connection:
            return self.cursor.execute("SELECT step FROM items WHERE id = ?", (item_id,)).fetchone()[0]
        
    def set_item_step(self, item_step, item_id):
        with self.connection:
            return self.cursor.execute("UPDATE items SET step = ? WHERE id = ?", (item_step, item_id,))
    
    def undone_item_exists(self):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM items WHERE step != 'done'")
            return bool(len(self.cursor.fetchall()))
    
    
    def get_id_by_step(self, step):
        with self.connection:
            return self.cursor.execute("SELECT id FROM items WHERE step = ?", (step,)).fetchone()[0]
        
    # def get_last_item_id(self):
    #     with self.connection:
    #         return self.cursor.execute("SELECT id FROM items WHERE id = (SELECT MAX(id) FROM items)").fetchone()[0]
        
    def add_news(self, news_message_id):
        with self.connection:
            self.cursor.execute(f"INSERT INTO news (message_id) VALUES ({news_message_id})")

   
    def delete_news(self, news_id):
        with self.connection:
            self.cursor.execute(f"DELETE FROM news WHERE news_id = {news_id}")

    def get_all_news(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM news").fetchall()
        
    def get_message_id(self, news_id):
        with self.connection:
            return self.cursor.execute("SELECT message_id FROM news WHERE id = ?", (news_id,)).fetchone()[0]
        
    def set_message_id(self, message_id, news_id):
        with self.connection:
            return self.cursor.execute("UPDATE news SET message_id = ? WHERE id = ?", (message_id, news_id,))
        
    def get_news(self, message_id):
        with self.connection:
            return self.cursor.execute("SELECT id FROM news WHERE message_id = ?", (message_id,)).fetchone()[0]
    
    def get_news_max_number(self):
        with self.connection:
            return self.cursor.execute("SELECT id FROM news WHERE id=(SELECT max(id) FROM news)").fetchone()[0]

    