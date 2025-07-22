import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
import os

# --------------------- DATABASE SETUP ---------------------
db = sqlite3.connect("bank_users.db")
cursor = db.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    age INTEGER,
    balance INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    username TEXT,
    type TEXT,
    amount INTEGER,
    time TEXT
)
''')

db.commit()

# --------------------- UTILS ---------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --------------------- APP CLASS ---------------------
class BankApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏦 Baryashah Bank")
        self.root.geometry("400x400")
        self.username = None

        self.login_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --------------------- LOGIN SCREEN ---------------------
    def login_screen(self):
        self.clear_window()

        tk.Label(self.root, text="Welcome to Baryashah Bank", font=("Arial", 14)).pack(pady=10)

        tk.Button(self.root, text="Login", command=self.login).pack(pady=5)
        tk.Button(self.root, text="Register", command=self.register).pack(pady=5)
        tk.Button(self.root, text="Forgot Password", command=self.reset_password).pack(pady=5)
        tk.Button(self.root, text="Exit", command=self.root.quit).pack(pady=20)

    # --------------------- REGISTER ---------------------
    def register(self):
        self.clear_window()
        tk.Label(self.root, text="Register", font=("Arial", 14)).pack(pady=10)

        username = simpledialog.askstring("Register", "Enter Username")
        if not username:
            self.login_screen()
            return

        existing = cursor.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if existing:
            messagebox.showerror("Error", "Username already exists")
            return self.login_screen()

        password = simpledialog.askstring("Register", "Enter Password", show='*')
        age = simpledialog.askinteger("Register", "Enter Age")

        if not password or not age:
            messagebox.showwarning("Invalid", "All fields required!")
            return self.login_screen()

        hashed = hash_password(password)
        cursor.execute("INSERT INTO users (username, password, age) VALUES (?, ?, ?)",
                       (username, hashed, age))
        db.commit()
        messagebox.showinfo("Success", "Account Created Successfully")
        self.login_screen()

    # --------------------- LOGIN ---------------------
    def login(self):
        self.clear_window()
        tk.Label(self.root, text="Login", font=("Arial", 14)).pack(pady=10)

        username = simpledialog.askstring("Login", "Enter Username")
        password = simpledialog.askstring("Login", "Enter Password", show='*')

        if not username or not password:
            messagebox.showwarning("Error", "Username and Password required")
            return

        hashed = hash_password(password)
        user = cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                              (username, hashed)).fetchone()
        if user:
            self.username = username
            self.dashboard()
        else:
            messagebox.showerror("Error", "Invalid credentials")
            self.login_screen()

    # --------------------- RESET PASSWORD ---------------------
    def reset_password(self):
        username = simpledialog.askstring("Reset Password", "Enter your Username")
        user = cursor.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

        if user:
            new_pass = simpledialog.askstring("Reset", "Enter New Password", show='*')
            if new_pass:
                hashed = hash_password(new_pass)
                cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
                db.commit()
                messagebox.showinfo("Success", "Password reset successfully")
        else:
            messagebox.showerror("Error", "User not found")

    # --------------------- DASHBOARD ---------------------
    def dashboard(self):
        self.clear_window()
        tk.Label(self.root, text=f"Welcome {self.username}", font=("Arial", 14)).pack(pady=10)

        tk.Button(self.root, text="Check Balance", command=self.check_balance).pack(pady=5)
        tk.Button(self.root, text="Deposit", command=self.deposit).pack(pady=5)
        tk.Button(self.root, text="Withdraw", command=self.withdraw).pack(pady=5)
        tk.Button(self.root, text="View Transaction History", command=self.view_history).pack(pady=5)
        tk.Button(self.root, text="Export to CSV", command=self.export_csv).pack(pady=5)
        tk.Button(self.root, text="Logout", command=self.logout).pack(pady=20)

    def logout(self):
        self.username = None
        self.login_screen()

    def check_balance(self):
        balance = cursor.execute("SELECT balance FROM users WHERE username=?", (self.username,)).fetchone()[0]
        messagebox.showinfo("Balance", f"Your balance is: Rs {balance}")

    def deposit(self):
        amount = simpledialog.askinteger("Deposit", "Enter amount")
        if amount and amount > 0:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, self.username))
            cursor.execute("INSERT INTO transactions VALUES (?, ?, ?, ?)",
                           (self.username, 'Deposit', amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            messagebox.showinfo("Success", "Amount deposited successfully")

    def withdraw(self):
        amount = simpledialog.askinteger("Withdraw", "Enter amount")
        balance = cursor.execute("SELECT balance FROM users WHERE username=?", (self.username,)).fetchone()[0]

        if amount and 0 < amount <= balance:
            cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, self.username))
            cursor.execute("INSERT INTO transactions VALUES (?, ?, ?, ?)",
                           (self.username, 'Withdraw', amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            messagebox.showinfo("Success", "Amount withdrawn successfully")
        else:
            messagebox.showwarning("Error", "Invalid or Insufficient funds")

    def view_history(self):
        history = cursor.execute("SELECT * FROM transactions WHERE username=?", (self.username,)).fetchall()
        if not history:
            messagebox.showinfo("History", "No transactions yet.")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("Transaction History")
        history_window.geometry("400x300")

        for i, (user, tx_type, amt, time) in enumerate(history):
            tk.Label(history_window, text=f"{i+1}. {tx_type} Rs {amt} on {time}").pack(anchor='w')

    def export_csv(self):
        history = cursor.execute("SELECT * FROM transactions WHERE username=?", (self.username,)).fetchall()
        if not history:
            messagebox.showinfo("No Data", "No transactions to export")
            return

        df = pd.DataFrame(history, columns=['Username', 'Type', 'Amount', 'Time'])
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if save_path:
            df.to_csv(save_path, index=False)
            messagebox.showinfo("Exported", f"History exported to {save_path}")


# --------------------- RUN ---------------------
if __name__ == '__main__':
    root = tk.Tk()
    app = BankApp(root)
    root.mainloop()
