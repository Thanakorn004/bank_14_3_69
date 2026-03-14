from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)

# ตั้งค่า MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # ใส่รหัสผ่านของคุณ
app.config['MYSQL_DB'] = 'atm_db'

mysql = MySQL(app)

# หน้าแรก
@app.route('/')
def index():
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM accounts")
    accounts = cur.fetchall()

    cur.execute("SELECT SUM(balance) FROM accounts")
    total_balance = cur.fetchone()[0]
    if total_balance is None:
        total_balance = 0

    cur.close()
    return render_template('index.html', accounts=accounts, total_balance=total_balance)


# สร้างบัญชี
@app.route('/create', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        account_number = request.form['account_number']
        username = request.form['username']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO accounts(account_number, username, balance) VALUES(%s,%s,%s)",
                    (account_number, username, 0))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('index'))

    return render_template('create.html')


# ดูบัญชี
@app.route('/account/<account_number>')
def account_detail(account_number):
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM accounts WHERE account_number=%s", (account_number,))
    account = cur.fetchone()

    cur.execute("SELECT type, amount, created_at FROM transactions WHERE account_number=%s ORDER BY created_at DESC", (account_number,))
    transactions = cur.fetchall()

    cur.close()
    return render_template('account.html', account=account, transactions=transactions)


# ฝากเงิน
@app.route('/deposit/<account_number>', methods=['POST'])
def deposit(account_number):
    amount = float(request.form['amount'])

    cur = mysql.connection.cursor()
    cur.execute("UPDATE accounts SET balance = balance + %s WHERE account_number=%s",
                (amount, account_number))

    cur.execute("INSERT INTO transactions(account_number, type, amount, created_at) VALUES(%s,%s,%s,%s)",
                (account_number, "Deposit", amount, datetime.now()))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('account_detail', account_number=account_number))


# ถอนเงิน
@app.route('/withdraw/<account_number>', methods=['POST'])
def withdraw(account_number):
    amount = float(request.form['amount'])

    cur = mysql.connection.cursor()
    cur.execute("SELECT balance FROM accounts WHERE account_number=%s", (account_number,))
    balance = cur.fetchone()[0]

    if balance >= amount:
        cur.execute("UPDATE accounts SET balance = balance - %s WHERE account_number=%s",
                    (amount, account_number))

        cur.execute("INSERT INTO transactions(account_number, type, amount, created_at) VALUES(%s,%s,%s,%s)",
                    (account_number, "Withdraw", amount, datetime.now()))

        mysql.connection.commit()

    cur.close()
    return redirect(url_for('account_detail', account_number=account_number))


# ลบบัญชี
@app.route('/delete/<account_number>')
def delete_account(account_number):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM accounts WHERE account_number=%s", (account_number,))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)