from flask import Flask, render_template, url_for, request, redirect, flash
import psycopg2
from datetime import datetime


app = Flask(__name__)

con = psycopg2.connect(database='db_test', user='u_test',
                           port=1984,
                           host="92.242.58.173",
                           password='testpwd')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/authorized/<id>') # Достать User из бд и передать
def authorized_index(id):
    cur = con.cursor()
    cur.execute('select u.full_name from "No_problems".user_info as u where u.id = %s', (id,))
    name = cur.fetchall()
    cur.close()
    return render_template("authorized_index.html", id=id, name=name[0][0])

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/authorized_about/<id>')
def authorized_about(id):
    return render_template("authorized_about.html", id = id)


@app.route('/offer_order/<id>')
def offer_order(id):
    return render_template("offer_order.html", id = id)


@app.route('/get_order_info/<id>', methods=['POST'])
def get_order_info(id):
    cur = con.cursor()
    subject = str(request.form['subject'])
    description = str(request.form['description'])
    deadline = datetime.strptime(request.form['deadline'], '%d.%m.%Y').date()
    price = str(request.form['price'])
    post_date = datetime.now().date()
    cur.execute('select s.id from "No_problems".subject as s where s.name LIKE %s', (subject,))
    subj_id = cur.fetchone()
    # TODO  TRY EXCEPT ловить ошибку некорректного ввода даты и сделать дд.мм.гггг в поле для ввода
    if subj_id is None:
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Предметная область указана не верно', redir=url_for('offer_order', id = id))
    else:
        if deadline < post_date:
            return render_template("error.html", message_error='Упс🤭 Дедлайн уже прошел', redir=url_for('offer_order', id = id))
        cur.execute('insert into "No_problems".problem (deadline, price, info, subject_id, post_client_id, post_date) values (%s, %s, %s, %s, %s, %s)',
                    (deadline, price, description, subj_id[0], id, post_date))
        con.commit()
        cur.close()
        return redirect(url_for('my_orders', id=id))




@app.route('/my_orders/<id>', methods=['GET']) # это предложенные заказы
def my_orders(id):

    cur = con.cursor()
    cur_d = datetime.now().date()
    cur.execute('''UPDATE "No_problems".problem
                            SET status_id = (SELECT st.id 
                                             FROM "No_problems".status as st
                                             WHERE st.name = %s)
                            WHERE deadline < %s''', ('Просрочен дедлайн', cur_d))
    con.commit()
    cur.close()

    cur = con.cursor()
    cur.execute('''SELECT s.name, p.info, p.post_date, p.deadline, st.name,  u2.full_name
                    FROM "No_problems".user_info as u JOIN "No_problems".problem as p ON (u.id = p.post_client_id)
					                    JOIN "No_problems".subject as s ON (s.id = p.subject_id)
                                        JOIN "No_problems".status as st ON (st.id = p.status_id)
                                        JOIN "No_problems".user_info as u2 ON (u2.id = p.solve_client_id)
                    WHERE u.id = %s''', (id, ))
    data = cur.fetchall()
    cur.close()
    columns_name = ['Предметная область', 'Описание задачи', 'Дата публикации', 'Дедлайн', 'Статус', 'Имя исполнителя']
    return render_template("template.html", id=id, output_data=data, columns=columns_name, number=len(columns_name))


@app.route('/select_order/<id>', methods=['GET'])
def select_order(id):

    # TODO статус заказа меняется и в требует подтверждения отправляется кнопки для выбора задач
    cur = con.cursor()
    cur_d = datetime.now().date()
    cur.execute('''UPDATE "No_problems".problem
                        SET status_id = (SELECT st.id 
                                         FROM "No_problems".status as st
                                         WHERE st.name = %s)
                        WHERE deadline < %s''', ('Просрочен дедлайн', cur_d))
    con.commit()
    cur.close()

    cur = con.cursor()
    cur.execute(''' select u.full_name, p.info, p.post_date,  p.deadline, p.price, s.name

            from "No_problems".problem as p join "No_problems".user_info as u on (u.id = p.post_client_id)
                                            join "No_problems".user_info as u1 on (u1.id = p.solve_client_id)
                                            join "No_problems".subject as s on (s.id = p.subject_id)

            where (p.status_id) = 0 AND (u.id != %s)
            order by p.post_date ''', (id,))
    data = cur.fetchall()
    cur.close()
    columns_name = ['Имя заказчика', 'Описание задачи', 'Дата публикации', 'Дедлайн', 'Цена', 'Предметная область']
    return render_template("template.html", id=id, output_data=data, columns=columns_name, number=len(columns_name))
    # return render_template('template.html', output_data=data)


@app.route('/selected_orders/<id>')
def selected_orders(id):

    cur = con.cursor()
    cur_d = datetime.now().date()
    cur.execute('''UPDATE "No_problems".problem
                            SET status_id = (SELECT st.id 
                                             FROM "No_problems".status as st
                                             WHERE st.name = %s)
                            WHERE deadline < %s''', ('Просрочен дедлайн', cur_d))
    con.commit()
    cur.close()

    cur = con.cursor()
    cur.execute(''' SELECT  s.name, p.info, p.post_date, p.deadline, p.price, u2.full_name, st.name
                    FROM "No_problems".user_info as u JOIN "No_problems".problem as p ON (u.id = p.solve_client_id)
					                    JOIN "No_problems".subject as s ON (s.id = p.subject_id)
                                        JOIN "No_problems".user_info as u2 ON (u2.id = p.post_client_id)
                                        JOIN "No_problems".status as st ON (p.status_id = st.id)
                    WHERE u.id = %s''', (id,))
    data = cur.fetchall()
    cur.close()
    columns_name = ["Предметная область", "Информация о задаче", "Дата публикации", 'Дедлайн', 'Цена', 'Имя заказчика']
    return render_template("template.html", id=id, output_data=data, columns=columns_name, number=len(columns_name))
    # return render_template("selected_orders.html", id=id)


@app.route('/change_information/<id>')
def change_information(id):
    return render_template("change_information.html", id=id)


@app.route('/change_password/<id>', methods=['POST'])
def change_password(id):
    cur = con.cursor()
    password_old = request.form['oldpassword']
    password_new = request.form['newpassword']
    password_new2 = request.form['newpassword_']

    cur.execute('''
                select u.password 
                from "No_problems".user_info as u 
                where u.id LIKE %s''', (id, ))
    password_true = cur.fetchone()
    if (password_true[0] != password_old):
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Неверный пароль', redir=url_for('personal_account', id = id))

    if (password_new == password_new2) & (password_new is not None):
        cur.execute('''
        UPDATE "No_problems".User_info SET password= %s WHERE id = %s
        ''', (password_new, id))
        con.commit()

    cur.close()

    return render_template("error.html", message_error='Пароль успешно изменен 👍', redir=url_for('personal_account', id = id))

# ---------- Extra fine 🤌 login/regstration part ------------------

@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/registration')
def registration():
    return render_template("registration.html")


@app.route('/get_registration', methods=['POST'])
def get_registration():
    cur = con.cursor()

    name = request.form['name']
    login_reg = request.form['email']
    country = request.form['country']
    telephone = request.form['telephone']
    password = request.form['password']
    repeat_password = request.form['repeat_password']
    info = request.form['info'] # TODO получать тоже из поля

    # check if login is unique
    cur.execute('SELECT u.id FROM "No_problems".User_info as u WHERE u.email = %s', [login_reg])
    logs = cur.fetchall()

    # check country
    cur.execute('select c.id from "No_problems".countries as c where c.name LIKE %s', (country,))
    country_id = cur.fetchone()
    if len(logs) != 0:
        print('not unique login')  # TODO PRINT ON SCREEN
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Такой логин уже есть', redir='/registration')
        # return render_template("registration.html"
    elif country_id is None:
        print('incorrect country')  # TODO PRINT ON SCREEN
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Такой страны не существует', redir='/registration')
    else:
        # TODO поменять id на осмысленное там должен быть автоинкремент  в дата грипе
        if password == repeat_password:
            cur.execute('INSERT INTO "No_problems".User_info (password, full_name, email, telephone, country_code, info) VALUES(%s, %s, %s, %s, %s, %s)',
                        (password, name, login_reg, telephone, country_id[0], info))
            con.commit()
            cur.close()
        else:
            print('Passwords do not match')  # TODO PRINT ON SCREEN
            cur.close()
            return render_template("error.html", message_error='Упс🤭 Пароли не совпадают', redir='/registration')
    return redirect(url_for('login'))


@app.route('/verification', methods=['POST'])
def verification():

    login = request.form['login']
    password = request.form['password']
    # check if login and password are valid
    cur = con.cursor()
    cur.execute('SELECT u.id FROM "No_problems".User_info as u WHERE u.email = %s', (login,))
    current_id = cur.fetchone()
    if current_id is None:
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Такого логина не существует', redir='/login')

    cur.execute('select u.password from "No_problems".user_info as u where u.email LIKE %s', (login,))
    password_true = cur.fetchone()
    if (password_true[0] != password):
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Неверный пароль', redir='/login')

    cur.close()
    current_id = current_id[0]
    return redirect(url_for('personal_account', id = current_id))
    # return render_template("personal_account.html", data=data)


@app.route('/personal_account/<id>')
def personal_account(id):
    cur = con.cursor()
    cur.execute('''
                SELECT u.email, c.name, u.full_name, u.telephone, u.info 
                FROM "No_problems".User_info as u
                JOIN "No_problems".countries as c ON u.country_code=c.id
                WHERE u.id = %s''', (id,))
    data = cur.fetchone()
    cur.close()
    return render_template("personal_account.html", data=data, id=id)


@app.route('/orders_confirmation/<id>')
def orders_confirmation(id):
    cur = con.cursor()
    cur.execute(''' SELECT  s.name, p.info, p.post_date, p.deadline, u.full_name, u.email, u.telephone, u.rating
                        FROM "No_problems".user_info as u JOIN "No_problems".problem as p ON (u.id = p.solve_client_id)
    					                    JOIN "No_problems".subject as s ON (s.id = p.subject_id)
                                            JOIN "No_problems".user_info as u2 ON (u2.id = p.post_client_id)
                                            JOIN "No_problems".status as st ON (st.id = p.status_id)
                        WHERE (st.name = %s) AND (u2.id = %s)''', ('На утверждении', id, ))
    data = cur.fetchall()
    cur.close()
    columns_name = ["Предметная область", "Информация о задаче", "Дата публикации", 'Дедлайн', 'Имя исполнителя',
                    'Почта исполнителя', 'Телефон исполнителя', "Рейтинг исполнителя"]
    return render_template("template.html", id=id, output_data=data, columns=columns_name, number=len(columns_name))
    # return render_template("orders_confirmation.html", id=id)


if __name__ == "__main__":
    app.run(debug=True)