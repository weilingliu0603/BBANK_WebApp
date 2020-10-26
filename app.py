import flask
import sqlite3
from flask import jsonify
import datetime as dt

labels = [
    'ONLINE SHOPPING', 'DINING'
]

values = [
    967.67, 1190.89
]

colors = [
    "#F7464A", "#46BFBD"
]


app = flask.Flask(__name__)

@app.route("/")
def index():
       return flask.render_template("index.html")

#register user
@app.route("/registration")
def registration(): 
##    data = flask.request.form
##    
##    Name = data["Name"]
##    Email = data["Email"]
##    Password = data["Password"]
##    Mobile = data["Mobile"]

    Name = "Liu Weiling"
    Email = "liu@gmail.com"
    Password = "liu123"
    Mobile = "98361234"

    connection = sqlite3.connect("BBOOK.db")
    cursor = connection.execute("SELECT * FROM Customer WHERE Email = ? ", (Email,)).fetchall()
    if len(cursor) > 0:
        results = [{'status': 'fail', 'message': 'email has been registered'}]
        connection.close()
        return jsonify(results)        
    else:
        results = [{'status': 'success', 'message': 'if any'}]
        cursor = connection.execute("SELECT seq FROM sqlite_sequence WHERE name = ? ", ("Customer",)).fetchall()
        nextID = int(cursor[0][0]) + 1
        
        cursor = connection.execute("INSERT INTO Customer VALUES (?,?,?,?,?)", (Name, Email, Password, Mobile, str(nextID)))
        connection.commit()
        connection.close()

        return jsonify(results)

@app.route("/login", methods = ["POST"])
def login(): 
    data = flask.request.form
    Email = data["Email"]
    Password = data["Password"]
    
    connection = sqlite3.connect("BBOOK.db")
    cursor = connection.execute("SELECT * FROM Customer WHERE Email = ? AND Password = ?", (Email, Password)).fetchall()
    
    if len(cursor) == 1:
        CustomerID = cursor[0][4]
        cursor = connection.execute("SELECT CustomerID,Name FROM Customer WHERE Email = ? ", (Email,)).fetchall()
        CustomerID = cursor[0][0]
        Name = cursor[0][1]
        cursor = connection.execute("SELECT SUM(Balance) FROM Account WHERE CustomerID = ? ", (CustomerID,)).fetchall()
        Deposit = cursor[0][0]
        cursor = connection.execute("SELECT SUM(AmountDue) FROM CreditCard WHERE CustomerID = ? ", (CustomerID,)).fetchall()
        Credit = cursor[0][0]
        connection.close()
        return flask.render_template("home.html", CustomerID = CustomerID, Deposit=Deposit, Credit=Credit)
        
    else:
        connection.close()
        return flask.render_template("index.html")
       
@app.route('/main/<CustomerID>')
def main(CustomerID):
        connection = sqlite3.connect("BBOOK.db")
        cursor = connection.execute("SELECT SUM(Balance) FROM Account WHERE CustomerID = ? ", (CustomerID,)).fetchall()
        Deposit = round(cursor[0][0],2)
        cursor = connection.execute("SELECT SUM(AmountDue) FROM CreditCard WHERE CustomerID = ? ", (CustomerID,)).fetchall()
        Credit = round(cursor[0][0],2)
        connection.close()
       
        return flask.render_template("home.html", CustomerID = CustomerID, Deposit=Deposit, Credit=Credit)
       
@app.route('/accounts/<CustomerID>')
def accounts(CustomerID):
       connection = sqlite3.connect("BBOOK.db")
       cursor = connection.execute("SELECT * FROM Account, Bank WHERE CustomerID = ? AND Account.BankID = Bank.BankID", (CustomerID,)).fetchall()
       cursor2 = connection.execute("SELECT * FROM CreditCard WHERE CustomerID = ?", (CustomerID,)).fetchall()
       connection.close()
       return flask.render_template("accounts.html", cursor = cursor, cursor2 = cursor2, CustomerID = CustomerID)

@app.route('/depositaccounts/<CustomerID>')
def depositaccounts(CustomerID):
       connection = sqlite3.connect("BBOOK.db")
       cursor = connection.execute("SELECT * FROM Account, Bank WHERE CustomerID = ? AND Account.BankID = Bank.BankID", (CustomerID,)).fetchall()
       connection.close()
       return flask.render_template("depositaccounts.html", cursor = cursor, CustomerID = CustomerID)

@app.route('/creditcards/<CustomerID>')
def creditcards(CustomerID):
       connection = sqlite3.connect("BBOOK.db")
       cursor = connection.execute("SELECT * FROM CreditCard WHERE CustomerID = ?", (CustomerID,)).fetchall()
       connection.close()
       return flask.render_template("creditcards.html", cursor = cursor, CustomerID = CustomerID)

@app.route('/payment/<CustomerID>')
def payment(CustomerID):
       connection = sqlite3.connect("BBOOK.db")
       cursor = connection.execute("SELECT * FROM CreditCard WHERE CustomerID = ?", (CustomerID,)).fetchall()
       cursor2 = connection.execute("SELECT * FROM Account, Bank WHERE CustomerID = ? AND Account.BankID = Bank.BankID", (CustomerID,)).fetchall()
       connection.close()
       return flask.render_template("payment.html", cursor = cursor, cursor2 = cursor2, CustomerID = CustomerID)

@app.route('/transfer/<CustomerID>')
def transfer(CustomerID):
       connection = sqlite3.connect("BBOOK.db")
       cursor = connection.execute("SELECT * FROM Account WHERE CustomerID = ? AND AccountType = ?", (CustomerID, "Savings")).fetchall()
       connection.close()
       return flask.render_template("transfer.html", cursor = cursor, CustomerID = CustomerID)

@app.route('/transferred/<CustomerID>', methods = ["POST"])
def transferred(CustomerID):
       today = dt.datetime.now()
       date = str(today.day)+"/"+str(today.month)+"/"+str(today.year)
       time = str(today.hour)+":"+str(today.min)+":00"
       data = flask.request.form
       Sender = data["Sender"]
       Receiver = data["Receiver"]
       AmountDue = float(data["Amount"])

       connection = sqlite3.connect("BBOOK.db")
       cursor = connection.execute("SELECT Balance FROM Account WHERE AccountNumber = ? ", (Sender,)).fetchall()
       balance = cursor[0][0]

       if balance < AmountDue:
              connection = sqlite3.connect("BBOOK.db")
              cursor = connection.execute("SELECT * FROM Account WHERE CustomerID = ? AND AccountType = ?", (CustomerID, "Savings")).fetchall()
              connection.close()
              return flask.render_template("transfer.html", cursor = cursor, CustomerID = CustomerID)
       else:
              connection.execute("UPDATE Account SET Balance = ? WHERE AccountNumber = ? ", (balance - AmountDue, Sender))
              connection.commit()
              cursor = connection.execute("SELECT Balance FROM Account WHERE AccountNumber = ? ", (Receiver,)).fetchall()
              newamount = cursor[0][0]
              connection.execute("UPDATE Account SET Balance = ? WHERE AccountNumber = ? ", (newamount + AmountDue, Receiver))
              connection.commit()
              connection.execute("INSERT INTO AccountTransaction VALUES (?,?,?,?,?)", (int(Sender), date, time, AmountDue, "Fund Transfer" ))
              connection.commit()
              connection.execute("INSERT INTO AccountTransaction VALUES (?,?,?,?,?)", (int(Receiver), date, time, AmountDue, "Fund Transfer" ))
              connection.commit()
              cursor = connection.execute("SELECT SUM(Balance) FROM Account WHERE CustomerID = ? ", (CustomerID,)).fetchall()
              Deposit = round(cursor[0][0],2)
              cursor = connection.execute("SELECT SUM(AmountDue) FROM CreditCard WHERE CustomerID = ? ", (CustomerID,)).fetchall()
              Credit = round(cursor[0][0],2)

       connection.close()
       return flask.render_template("home.html", CustomerID = CustomerID, Deposit=Deposit, Credit=Credit)


@app.route('/paid/<CustomerID>', methods = ["POST"])
def paid(CustomerID):
       today = dt.datetime.now()
       date = str(today.day)+"/"+str(today.month)+"/"+str(today.year)
       time = time = str(today.hour)+":"+str(today.min)+":00"
       data = flask.request.form
       CardNumber = data["CardNumber"]
       AccountNum = data["AccountNumber"]

       connection = sqlite3.connect("BBOOK.db")
       cursor = connection.execute("SELECT Balance FROM Account WHERE AccountNumber = ? ", (AccountNum,)).fetchall()
       balance = cursor[0][0]

       cursor = connection.execute("SELECT AmountDue FROM CreditCard WHERE CardNumber = ? ", (CardNumber,)).fetchall()
       AmountDue = cursor[0][0]
    
       if balance < AmountDue:
              connection = sqlite3.connect("BBOOK.db")
              cursor = connection.execute("SELECT * FROM CreditCard WHERE CustomerID = ?", (CustomerID,)).fetchall()
              cursor2 = connection.execute("SELECT * FROM Account, Bank WHERE CustomerID = ? AND Account.BankID = Bank.BankID", (CustomerID,)).fetchall()
              connection.close()
              return flask.render_template("unsuccessful.html", cursor = cursor, cursor2 = cursor2, CustomerID = CustomerID)
       else:
              results = [{'status': 'success', 'message': 'if any'}]
              connection.execute("UPDATE Account SET Balance = ? WHERE AccountNumber = ? ", (balance - AmountDue, AccountNum,))
              connection.commit()
              newamount = 0
              connection.execute("UPDATE CreditCard SET AmountDue = ? WHERE CardNumber = ? ", (newamount, CardNumber,))
              connection.commit()
              connection.execute("INSERT INTO AccountTransaction VALUES (?,?,?,?,?)", (int(AccountNum), date, time, AmountDue, "Card Payment" ))
              connection.commit()
              cursor = connection.execute("SELECT SUM(Balance) FROM Account WHERE CustomerID = ? ", (CustomerID,)).fetchall()
              Deposit = round(cursor[0][0],2)
              cursor = connection.execute("SELECT SUM(AmountDue) FROM CreditCard WHERE CustomerID = ? ", (CustomerID,)).fetchall()
              Credit = round(cursor[0][0],2)

       connection.close()
       return flask.render_template("home.html", CustomerID = CustomerID, Deposit=Deposit, Credit=Credit)

@app.route('/insights/<CustomerID>')
def insights(CustomerID):
       today = dt.datetime.now()
       month = today.month
       months = ["Jan","Feb","Mar","April","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

       thismonth = months[month-1]

       command = """select SUM(CreditCardTransaction.Amount), CreditCardTransaction.Category 
       from CreditCard, CreditCardTransaction
       where CreditCard.CardNumber =  CreditCardTransaction.CardNumber
       and CreditCard.CustomerID = ? and CreditCardTransaction.Month = ?
       group by Category
       """
       connection = sqlite3.connect("BBOOK.db")
       cursor = connection.execute(command, (CustomerID, thismonth)).fetchall()

       pie_labels = []
       pie_values = []
       colors = ["#0066FF","#0099FF","#003366","#888888","#009999","#003399"]

       for record in cursor:
              if record[1] != "Cashback":
                     pie_labels.append(record[1])
              pie_values.append(abs(record[0]))            


       return flask.render_template('pie_chart.html', title='Your Expenses in '+thismonth+ ' by Category', max=17000, set=zip(pie_values, pie_labels, colors),set2=zip(pie_labels, colors), CustomerID = CustomerID)


       #return flask.render_template("insights.html", results = results, CustomerID = CustomerID)

@app.route('/recommendations/<CustomerID>')
def recommendations(CustomerID):
       return "Hello " + CustomerID


@app.route('/chart')
def chart():
    connection = sqlite3.connect("BBOOK.db")
    cursor = connection.execute("SELECT SUM(Amount), Month from CreditCardTransaction where CardNumber = ? group by Month", (4544092911023330,)).fetchall()
    connection.close()

    labels = []
    values = []
    for record in cursor:
           labels.append(record[1])
           values.append(abs(record[0]))
    legend = 'Monthly Data'
    return flask.render_template('linechart.html', values=values, labels=labels, legend=legend)
       
#customer summary
@app.route("/customer_summary/<Email>")
def customer_summary(Email):
       connection = sqlite3.connect("BBOOK.db")
       cursor = connection.execute("SELECT CustomerID,Name FROM Customer WHERE Email = ? ", (Email,)).fetchall()
       CustomerID = cursor[0][0]
       Name = cursor[0][1]
       cursor = connection.execute("SELECT SUM(Balance) FROM Account WHERE CustomerID = ? ", (CustomerID,)).fetchall()
       Deposit = cursor[0][0]
       cursor = connection.execute("SELECT SUM(AmountDue) FROM CreditCard WHERE CustomerID = ? ", (CustomerID,)).fetchall()
       Credit = cursor[0][0]
       connection.close()
       results = [{'CustomerID': CustomerID, 'Name': Name, 'Deposit': Deposit, 'Credit': Credit}]
       return jsonify(results)

#retrieve all saving accounts transactions
@app.route("/accounts_transactions/<Email>")
def accounts_transactions(Email): 
    connection = sqlite3.connect("BBOOK.db")
    cursor = connection.execute("SELECT CustomerID FROM Customer WHERE Email = ? ", (Email,)).fetchall()

    CustomerID = cursor[0][0]

    cursor = connection.execute("SELECT AccountNumber FROM Account WHERE CustomerID = ? AND AccountType = ?", (CustomerID, "Savings")).fetchall()

    dic = {}
    for account in cursor:
           dic[account[0]] = []
       
    for AccountNumber in dic:
           cursor = connection.execute("SELECT Date, Time, Amount, Description FROM AccountTransaction WHERE AccountNumber = ? ", (AccountNumber,)).fetchall()
           for record in cursor:
                  dic[AccountNumber].append(record)

    connection.close()
    
    return jsonify(dic)

#retrieve transactions of one saving account
@app.route("/account_transactions/<AccountNumber>")
def account_transactions(AccountNumber):
    dic = {AccountNumber:[]}
    connection = sqlite3.connect("BBOOK.db")

    cursor = connection.execute("SELECT Date, Time, Amount, Description FROM AccountTransaction WHERE AccountNumber = ? ", (AccountNumber,)).fetchall()
    connection.close()   

    for record in cursor:
           dic[AccountNumber].append(record)
    
    return jsonify(dic)

#retrieve all credit card transactions
@app.route("/cards_transactions/<Email>")
def cards_transactions(Email): 
    connection = sqlite3.connect("BBOOK.db")
    cursor = connection.execute("SELECT CustomerID FROM Customer WHERE Email = ? ", (Email,)).fetchall()

    CustomerID = cursor[0][0]

    cursor = connection.execute("SELECT CardNumber FROM CreditCard WHERE CustomerID = ? ", (CustomerID,)).fetchall()

    dic = {}
    for account in cursor:
           dic[account[0]] = []
       
    for CardNumber in dic:
           cursor = connection.execute("SELECT Date, Time, Amount, Category FROM CreditCardTransaction WHERE CardNumber = ? ", (CardNumber,)).fetchall()
           for record in cursor:
                  dic[CardNumber].append(record)
    connection.close()
    
    return jsonify(dic)     

#retrieve credit card transactions of one card
@app.route("/card_transactions/<CardNumber>")
def card_transactions(CardNumber):
    dic = {CardNumber:[]}
    connection = sqlite3.connect("BBOOK.db")

    cursor = connection.execute("SELECT Date, Time, Amount, Category FROM CreditCardTransaction WHERE CardNumber = ? ", (CardNumber,)).fetchall()
    for record in cursor:
           dic[CardNumber].append(record)
    connection.close()
    
    return jsonify(dic)

#retrieve info of each credit card (incl amount due)
@app.route("/card_info/<CardNumber>")
def card_info(CardNumber):
    connection = sqlite3.connect("BBOOK.db")

    cursor = connection.execute("SELECT * FROM CreditCard WHERE CardNumber = ? ", (CardNumber,)).fetchall()
    cursor1 = connection.execute("SELECT Name FROM Customer WHERE CustomerID = ? ", (cursor[0][5],)).fetchall()
    connection.close()

    dic = {"CardNumber":cursor[0][0], "Name":cursor1[0][0], "CardType":cursor[0][1], "ExpiryDate":cursor[0][3], "CardName":cursor[0][4], "AmountDue":cursor[0][6]}
    
    return jsonify(dic)


#retrieve historical total monthly spending (credit cards)
@app.route("/total_spending/<Email>")
def total_spending(Email):
    connection = sqlite3.connect("BBOOK.db")
    cursor = connection.execute("SELECT CustomerID FROM Customer WHERE Email = ? ", (Email,)).fetchall()

    CustomerID = cursor[0][0]

    cursor = connection.execute("SELECT CardNumber FROM CreditCard WHERE CustomerID = ? ", (CustomerID,)).fetchall()

    creditcards = []
    for record in cursor:
           creditcards.append(record)

    dic = {}

    for card in creditcards:
           if card not in dic:
                  dic[card[0]] = {}

           for card in dic:
                  cursor = connection.execute("SELECT Amount, Month FROM CreditCardTransaction WHERE CardNumber = ? ", (card,)).fetchall()
                  for record in cursor:
                         if record[1] not in dic[card]:
                                dic[card][record[1]] = record[0]
                         else:
                                dic[card][record[1]] += record[0]
                  
    connection.close()
    return jsonify(dic)
       

#retrieve this month's spending by category (credit cards)
@app.route("/category_spending/<Email>")
def category_spending(Email):
    today = dt.datetime.now()
    month = today.month
    months = ["Jan","Feb","Mar","April","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    thismonth = months[month-1]
    
    
    connection = sqlite3.connect("BBOOK.db")
    cursor = connection.execute("SELECT CustomerID FROM Customer WHERE Email = ? ", (Email,)).fetchall()

    CustomerID = cursor[0][0]

    cursor = connection.execute("SELECT CardNumber FROM CreditCard WHERE CustomerID = ? ", (CustomerID,)).fetchall()

    creditcards = []
    for record in cursor:
           creditcards.append(record)

    dic = {}

    for card in creditcards:
           if card not in dic:
                  dic[card[0]] = {}

           for card in dic:
                  cursor = connection.execute("SELECT Amount, Category FROM CreditCardTransaction WHERE CardNumber = ? AND Month = ?", (card, thismonth)).fetchall()
                  for record in cursor:
                         if record[1] not in dic[card]:
                                dic[card][record[1]] = round(record[0],2)
                         else:
                                dic[card][record[1]] += round(record[0],2)
                  
    connection.close()
    return jsonify(dic)
       

#pay credit card amount due
@app.route("/pay_cc") #set method to GET/POST
def pay_cc(): 
##    data = flask.request.form
##    CardNumber = data["CardNumber"]
##    AccountNum = data["AccountNum"]
##    AmountPaid = data["AmountPaid"]

    CardNumber = 4335666755550000 #to be removed, for testing only
    AccountNum = 123244500 #to be removed, for testing only
    AmountPaid = 500 #to be removed, for testing only
    
    connection = sqlite3.connect("BBOOK.db")
    cursor = connection.execute("SELECT Balance FROM Account WHERE AccountNumber = ? ", (AccountNum,)).fetchall()
    balance = cursor[0][0]

    cursor = connection.execute("SELECT AmountDue FROM CreditCard WHERE CardNumber = ? ", (CardNumber,)).fetchall()
    AmountDue = cursor[0][0]
    
    if balance < AmountDue:
        results = [{'status': 'fail', 'message': 'if any'}]
        connection.close()
        return jsonify(results)         
    else:
        results = [{'status': 'success', 'message': 'if any'}]
        connection.execute("UPDATE Account SET Balance = ? WHERE AccountNumber = ? ", (balance - AmountPaid, AccountNum,))
        connection.commit()
        newamount = AmountDue + AmountPaid
        connection.execute("UPDATE CreditCard SET AmountDue = ? WHERE CardNumber = ? ", (newamount, CardNumber,))
        connection.commit()

    connection.close()
    return jsonify(results) 


#transfer funds
@app.route("/transfer_funds") #set method to GET/POST
def transfer_funds(): 
##    data = flask.request.form
##    Sender = data["Account_Send"]
##    Receiver = data["Accound_Receive"]
##    Amount = data["Amount"]

    Sender = 112244537 #to be removed, for testing only
    Receiver = 123244500 #to be removed, for testing only
    Amount = 500 #to be removed, for testing only
    
    connection = sqlite3.connect("BBOOK.db")
    cursor = connection.execute("SELECT Balance FROM Account WHERE AccountNumber = ? ", (Sender,)).fetchall()
    sender_balance = cursor[0][0]

    if sender_balance < Amount:
        results = [{'status': 'fail', 'message': 'if any'}]
        connection.close()
        return jsonify(results)         
    else:
        results = [{'status': 'success', 'message': 'if any'}]
        cursor = connection.execute("SELECT Balance FROM Account WHERE AccountNumber = ? ", (Receiver,)).fetchall()
        receiver_balance = cursor[0][0]
    
        connection.execute("UPDATE Account SET Balance = ? WHERE AccountNumber = ? ", (sender_balance - Amount, Sender,))
        connection.commit()
        connection.execute("UPDATE Account SET Balance = ? WHERE AccountNumber = ? ", (receiver_balance + Amount, Receiver,))
        connection.commit()

    connection.close()
    return jsonify(results) 

if __name__ == "__main__":
    app.run(port=6789,debug=True)
