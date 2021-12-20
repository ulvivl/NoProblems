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
    cur.execute('SELECT u.id FROM "No_problem".User_info as u WHERE u.email = %s', [login_reg])
    logs = cur.fetchall()

    # check country
    cur.execute('select c.id from "No_problem".countries as c where c.name LIKE %s', (country,))
    country_id = cur.fetchone()
    if len(logs) != 0:
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Такой логин уже есть', redir='/registration', massage = "Попробовать снова")
        # return render_template("registration.html"
    elif country_id is None:
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Такой страны не существует', redir='/registration', massage = "Попробовать снова")
    else:
        # TODO поменять id на осмысленное там должен быть автоинкремент  в дата грипе
        if password == repeat_password:
            cur.execute('INSERT INTO "No_problem".User_info (password, full_name, email, telephone, country_code, info) VALUES(%s, %s, %s, %s, %s, %s)',
                        (password, name, login_reg, telephone, country_id[0], info))
            con.commit()
            cur.close()
        else:
            cur.close()
            return render_template("error.html", message_error='Упс🤭 Пароли не совпадают', redir='/registration', massage = "Попробовать снова")
    return redirect(url_for('login'))


@app.route('/verification', methods=['POST'])
def verification():

    login = request.form['login']
    password = request.form['password']
    # check if login and password are valid
    cur = con.cursor()
    cur.execute('SELECT u.id FROM "No_problem".User_info as u WHERE u.email = %s', (login,))
    current_id = cur.fetchone()
    if current_id is None:
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Такого логина не существует', redir='/login', massage = "Попробовать снова")

    cur.execute('select u.password from "No_problem".user_info as u where u.email LIKE %s', (login,))
    password_true = cur.fetchone()
    if (password_true[0] != password):
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Неверный пароль', redir='/login', massage = "Попробовать снова")

    cur.close()
    current_id = current_id[0]
    return redirect(url_for('personal_account', id = current_id))
    # return render_template("personal_account.html", data=data)


@app.route('/personal_account/<id>')
def personal_account(id):
    cur = con.cursor()
    cur.execute('''
                SELECT u.email, c.name, u.full_name, u.telephone, u.info, u.rating
                FROM "No_problem".User_info as u
                JOIN "No_problem".countries as c ON u.country_code=c.id
                WHERE u.id = %s''', (id,))
    data = cur.fetchone()
    cur.close()
    return render_template("personal_account.html", data=data, id=id, rating = f"{data[5]:.{2}f}")


@app.route('/authorized/<id>')
def authorized_index(id):
    cur = con.cursor()
    cur.execute('select u.full_name from "No_problem".user_info as u where u.id = %s', (id,))
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
    price = str(request.form['price'])
    tags = str(request.form['tag']).split(',')
    try:
        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()
    except:
        return render_template("error.html", message_error='Некорректный формат дедлайна📆',
                            redir=url_for('offer_order', id=id), massage="Попробовать снова")
    post_date = datetime.now().date()
    cur.execute('select s.id from "No_problem".subject as s where s.name LIKE %s', (subject,))
    subj_id = cur.fetchone()

    if subj_id is None:
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Предметная область указана не верно', redir=url_for('offer_order', id = id), massage = "Попробовать снова")
    else:
        if deadline < post_date:
            return render_template("error.html", message_error='Упс🤭 Дедлайн уже прошел', redir=url_for('offer_order', id = id), massage = "Попробовать снова")
        cur.execute('insert into "No_problem".problem (deadline, price, info, subject_id, post_client_id, post_date, solve_date) values (%s, %s, %s, %s, %s, %s, %s)',
                    (deadline, price, description, subj_id[0], id, post_date, deadline))
        con.commit()
        cur.close()
        cur = con.cursor()
        cur.execute('''select p.id from "No_problem".problem as p 
                    where (p.deadline, p.price, p.info, p.subject_id, p.post_client_id, p.post_date, p.solve_date) 
                    = (%s, %s, %s, %s, %s, %s, %s) ''', (deadline, price, description, subj_id[0], id, post_date, deadline))
        prob_id = cur.fetchone()[0]

        for tag in tags:
            cur.execute('''select t.id from "No_problem".tag as t
                    where t.name = %s ''', (tag, ))
            tag_id = cur.fetchone()
            if tag_id is None:
                cur.execute('''
                    insert into "No_problem".tag (name) 
                    values (%s)''', (tag, ))
                con.commit()
                cur.execute('''select t.id from "No_problem".tag as t
                    where t.name = %s ''', (tag, ))
                tag_id = cur.fetchone()
            cur.close()
            cur = con.cursor()
            cur.execute('''
                    insert into "No_problem".tag_problem (tag_id, problem_id) 
                    values (%s, %s)''', (tag_id, prob_id))
            con.commit()

        cur.close()
        return redirect(url_for('my_orders', id=id))


@app.route('/my_orders/<id>', methods=['GET']) # это предложенные заказы
def my_orders(id):

    cur = con.cursor()
    cur_d = datetime.now().date()
    cur.execute('''UPDATE "No_problem".problem
                            SET status_id = (SELECT st.id 
                                             FROM "No_problem".status as st
                                             WHERE st.name = %s)
                            WHERE (deadline < %s) AND (status_id < %s)''', ('Просрочен дедлайн', cur_d, 3))
    con.commit()
    cur.close()

    cur = con.cursor()
    cur.execute('''SELECT s.name, p.info, p.post_date, p.deadline, p.solve_date, st.name,  u2.full_name, u2.email, u2.telephone
                    FROM "No_problem".user_info as u JOIN "No_problem".problem as p ON (u.id = p.post_client_id)
					                    JOIN "No_problem".subject as s ON (s.id = p.subject_id)
                                        JOIN "No_problem".status as st ON (st.id = p.status_id)
                                        JOIN "No_problem".user_info as u2 ON (u2.id = p.solve_client_id)
                    WHERE u.id = %s
                    ORDER BY p.status_id''', (id, ))
    data = cur.fetchall()
    cur.close()

    # Выбираем id всех таких задач
    cur = con.cursor()
    cur.execute('''SELECT p.id
                    FROM "No_problem".user_info as u JOIN "No_problem".problem as p ON (u.id = p.post_client_id)
                    WHERE u.id = %s
                    ORDER BY p.status_id''', (id, ))
    prob_ids = cur.fetchall()
    cur.close()

    columns_name = ['Предметная область', 'Описание задачи', 'Дата публикации', 'Дедлайн', 'Дата решения', 'Статус', 'Имя исполнителя', 'Почта исполнителя', 'Телефон исполнителя']
    return render_template("template_ready.html", id=id, output_data=data, columns=columns_name, number=len(columns_name),
                           prob_ids=prob_ids, lenth=len(data))


@app.route('/ready_problem/<id>/<prob_id>', methods=["POST"])
def ready_problem(id, prob_id):
    mark = request.form['mark' + str(prob_id)]
    try:
        integer_mark = int(mark)
    except ValueError:
        return render_template("error.html", message_error='Оценка не соответсвует формату🤨',
                            redir=url_for('my_orders', id=id), massage="Вернуться к заказам")
    if integer_mark < 1 or integer_mark > 5:
        return render_template("error.html", message_error='Оценка не соответсвует формату🤨',
                            redir=url_for('my_orders', id=id), massage="Вернуться к заказам")
    cur = con.cursor()

    cur.execute('''SELECT COUNT(p.id) 
                    FROM "No_problem".problem AS p
                    WHERE (p.status_id = (SELECT st2.id 
                                            FROM "No_problem".status as st2
                                            WHERE st2.name = %s))
                    GROUP BY p.solve_client_id
                    HAVING (p.solve_client_id = (SELECT p2.solve_client_id
                                    FROM "No_problem".problem AS p2
                                    WHERE p2.id = %s))
                    ''', ('Задача закрыта', prob_id,))
    us_count = cur.fetchall()
    cur.close()

    if len(us_count) == 0:
        us_count = 1
    else:
        us_count = us_count[0][0] + 1

    cur = con.cursor()
    cur.execute('''SELECT u.rating 
                        FROM "No_problem".user_info as u
                        WHERE u.id = (SELECT p2.solve_client_id
                                        FROM "No_problem".problem AS p2
                                        WHERE p2.id = %s)
                        ''', (prob_id,))

    us_rating = cur.fetchall()
    cur.close()
    if len(us_rating) == 0:
        us_rating = integer_mark
    else:
        us_rating = us_rating[0][0] + integer_mark

    cur = con.cursor()
    cur.execute('''UPDATE "No_problem".user_info
                    SET rating = %s
                    WHERE id = (SELECT p.solve_client_id
                                    FROM "No_problem".problem AS p
                                    WHERE (p.id = %s) AND p.status_id = (SELECT st2.id 
                                                                        FROM "No_problem".status as st2
                                                                        WHERE st2.name = %s))''',
                (us_rating / us_count, prob_id, 'На выполнении'))
    con.commit()
    cur.close()

    cur = con.cursor()
    cur_d = datetime.now().date()
    cur.execute('''UPDATE "No_problem".problem
                                SET status_id = (SELECT st.id 
                                                FROM "No_problem".status as st
                                                WHERE st.name = %s),
                                    solve_date = %s,
                                    mark = %s
                                WHERE ((id = %s) AND (status_id = (SELECT st2.id 
                                                FROM "No_problem".status as st2
                                                WHERE st2.name = %s)))''', ('Задача закрыта', cur_d, integer_mark, prob_id, 'На выполнении'))
    con.commit()
    cur.close()
    return redirect(url_for('my_orders', id=id))



@app.route('/select_order/<id>', methods=['GET'])
def select_order(id):

    # Меняем статус у просрроченных задач
    cur = con.cursor()
    cur_d = datetime.now().date()
    cur.execute('''UPDATE "No_problem".problem
                        SET status_id = (SELECT st.id 
                                         FROM "No_problem".status as st
                                         WHERE st.name = %s)
                        WHERE (deadline < %s) AND (status_id < %s)''', ('Просрочен дедлайн', cur_d, 3))
    con.commit()
    cur.close()

    # Выбираем задачи которые можно выбрать
    cur = con.cursor()
    cur.execute('''select u.full_name, p.info, p.post_date,  p.deadline, p.price, s.name

            from "No_problem".problem as p join "No_problem".user_info as u on (u.id = p.post_client_id)
                                            join "No_problem".user_info as u1 on (u1.id = p.solve_client_id)
                                            join "No_problem".subject as s on (s.id = p.subject_id)

            where (p.status_id = 0) AND (u.id != %s)
            order by p.post_date ''', (id,))
    data = cur.fetchall()
    cur.close()

    # Выбираем is всех таких задач
    cur = con.cursor()
    cur.execute(''' select p.id
                from "No_problem".problem as p join "No_problem".user_info as u on (u.id = p.post_client_id)
                                                join "No_problem".user_info as u1 on (u1.id = p.solve_client_id)

                where (p.status_id) = 0 AND (u.id != %s)
                order by p.post_date ''', (id,))
    prob_ids = cur.fetchall()
    cur.close()
    columns_name = ['Имя заказчика', 'Описание задачи', 'Дата публикации', 'Дедлайн', 'Цена', 'Предметная область']
    return render_template("template_select.html", id=id, output_data=data, columns=columns_name, number=len(columns_name),
                           prob_ids=prob_ids, lenth=len(data))

@app.route('/tag_search/<id>', methods=['POST'])
def tag_search(id):
    tag = request.form['tag']
    cur = con.cursor()
    cur.execute(
    '''
        select p.info, p.deadline, p.price, s.name, st.name

        from "No_problem".problem as p
        join "No_problem".subject as s on s.id = p.subject_id
        join "No_problem".status as st on st.id = p.status_id

        where lower(s.name) = lower(%s)
        ''', (tag, ))
    data = cur.fetchall()
    if len(data) == 0:
        cur.execute(
        '''
            select p.info, p.deadline, p.price, s.name, st.name

            from "No_problem".problem as p
            join "No_problem".subject as s on s.id = p.subject_id
            join "No_problem".status as st on st.id = p.status_id
            join "No_problem".tag_problem as tp on p.id = tp.problem_id
            join "No_problem".tag as t on t.id = tp.tag_id

            where lower(t.name) = lower(%s)
            ''', (tag, ))
        data = cur.fetchall()
        cur.close()

        # Выбираем is всех таких задач
        cur = con.cursor()
        cur.execute(''' select p.id
                        from "No_problem".problem as p
                        join "No_problem".tag_problem as tp on p.id = tp.problem_id
                        join "No_problem".tag as t on t.id = tp.tag_id
                        where lower(t.name) = lower(%s)
                        order by p.status_id''', (tag,))
        prob_ids = cur.fetchall()
        cur.close()
    else:
        # Выбираем is всех таких задач
        cur = con.cursor()
        cur.execute(''' select p.id
                        from "No_problem".problem as p
                        join "No_problem".subject as s on s.id = p.subject_id
                        where lower(s.name) = lower(%s)
                        order by p.status_id''', (tag,))
        prob_ids = cur.fetchall()
        cur.close()
    columns_name = ["Описание задачи", "Дедлайн", "Цена", "Предметная область", "Статус выполнения"]
    return render_template("template_select.html", id=id, output_data=data, columns=columns_name, number=len(columns_name),
                        prob_ids=prob_ids, lenth=len(data))


@app.route('/select_problem/<id>/<prob_id>', methods=["POST"])
def select_problem(id, prob_id):
    cur = con.cursor()
    cur.execute('''UPDATE "No_problem".problem
                                SET status_id = (SELECT st.id 
                                                 FROM "No_problem".status as st
                                                 WHERE st.name = %s),
                                    solve_client_id = %s
                                WHERE id = %s''', ('На утверждении', id, prob_id))
    con.commit()
    cur.close()
    return redirect(url_for('selected_orders', id=id))

@app.route('/selected_orders/<id>')
def selected_orders(id):

    cur = con.cursor()
    cur_d = datetime.now().date()
    cur.execute('''UPDATE "No_problem".problem
                            SET status_id = (SELECT st.id 
                                             FROM "No_problem".status as st
                                             WHERE st.name = %s)
                            WHERE (deadline < %s) AND (status_id < %s)''', ('Просрочен дедлайн', cur_d, 3))
    con.commit()
    cur.close()

    cur = con.cursor()
    cur.execute(''' SELECT  s.name, p.info, p.post_date, p.deadline, p.price, p.mark, st.name, u2.full_name, u2.email, u2.telephone
                    FROM "No_problem".user_info as u JOIN "No_problem".problem as p ON (u.id = p.solve_client_id)
					                    JOIN "No_problem".subject as s ON (s.id = p.subject_id)
                                        JOIN "No_problem".user_info as u2 ON (u2.id = p.post_client_id)
                                        JOIN "No_problem".status as st ON (p.status_id = st.id)
                    WHERE u.id = %s''', (id,))
    data = cur.fetchall()
    cur.close()
    columns_name = ["Предметная область", "Информация о задаче", "Дата публикации", 'Дедлайн', 'Цена','Оценка решения', 'Статус', 'Имя заказчика', 'Почта заказчика', 'Телефон заказчика']
    return render_template("template_base.html", id=id, output_data=data, columns=columns_name, number=len(columns_name))

@app.route('/redir_info/<id>')
def redir_info(id):
    return render_template("change_information.html", id=id)

@app.route('/change_information/<id>', methods=["POST"]) # TODO проверка на пустоту
def change_information(id):
    cur = con.cursor()

    name = request.form['fullname']
    country = request.form['country']
    telephone = request.form['telephone']
    info = request.form['info']

    cur.execute('select c.id from "No_problem".countries as c where c.name = %s', (country,))
    country_id = cur.fetchone()

    if country_id is None:
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Такой страны не существует', redir=url_for('personal_account', id = id),  massage = "Попробовать снова")
    
    if name == '':
        cur.execute('select u.full_name from "No_problem".user_info as u where u.id = %s', (id,))
        name = cur.fetchone()[0]
    if info == '':
        cur.execute('select u.info from "No_problem".user_info as u where u.id = %s', (id,))
        info = cur.fetchone()[0]
    if telephone == '':
        cur.execute('select u.telephone from "No_problem".user_info as u where u.id = %s', (id,))
        telephone = cur.fetchone()[0]

    cur.execute('''
        UPDATE "No_problem".User_info SET (full_name, telephone, country_code, info) = (%s, %s, %s, %s) WHERE id = %s
        ''', (name, telephone, country_id[0], info, id))
    con.commit()
    cur.close()
    return render_template("error.html", message_error='Информация успешно изменена 👍', redir=url_for('personal_account', id = id),  massage = "Вернуться в личный кабинет")


@app.route('/redir_password/<id>')
def redir_password(id):
    return render_template("change_password.html", id=id)

@app.route('/change_password/<id>', methods=['POST'])
def change_password(id):
    cur = con.cursor()
    password_old = request.form['oldpassword']
    password_new = request.form['newpassword']
    password_new2 = request.form['newpassword_']

    cur.execute('''
                select u.password 
                from "No_problem".user_info as u 
                where u.id = %s''', (id, ))
    password_true = cur.fetchone()
    if (password_true[0] != password_old):
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Неверный пароль', redir=url_for('personal_account', id = id), massage = "Попробовать снова")

    if (password_new == password_new2) & (password_new is not None):
        cur.execute('''
        UPDATE "No_problem".User_info SET password= %s WHERE id = %s
        ''', (password_new, id))
        con.commit()
    else:
        cur.close()
        return render_template("error.html", message_error='Упс🤭 Введены разные пароли', redir=url_for('personal_account', id = id),  massage = "Попробовать снова")

    cur.close()

    return render_template("error.html", message_error='Пароль успешно изменен 👍', redir=url_for('personal_account', id = id),  massage = "Вернуться в личный кабинет")


@app.route('/orders_confirmation/<id>')
def orders_confirmation(id):
    cur = con.cursor()
    cur.execute(''' SELECT  s.name, p.info, p.post_date, p.deadline, u.full_name, u.email, u.telephone, u.rating
                        FROM "No_problem".user_info as u JOIN "No_problem".problem as p ON (u.id = p.solve_client_id)
                             JOIN "No_problem".subject as s ON (s.id = p.subject_id)
                                            JOIN "No_problem".user_info as u2 ON (u2.id = p.post_client_id)
                                            JOIN "No_problem".status as st ON (st.id = p.status_id)
                        WHERE (st.name = %s) AND (u2.id = %s)''', ('На утверждении', id, ))
    data = cur.fetchall()
    cur.close()

    # Выбираем id всех таких задач
    cur = con.cursor()
    cur.execute(''' SELECT p.id
                    FROM "No_problem".problem AS p JOIN "No_problem".user_info as u on (u.id = p.post_client_id)
                                                    JOIN "No_problem".status as st ON (st.id = p.status_id)
                    WHERE (st.name = %s) AND (u.id = %s)''', ('На утверждении', id, ))
    prob_ids = cur.fetchall()
    cur.close()
    columns_name = ["Предметная область", "Информация о задаче", "Дата публикации", 'Дедлайн', 'Имя исполнителя',
                    'Почта исполнителя', 'Телефон исполнителя', "Рейтинг исполнителя"]
    return render_template("template_approve.html", id=id, output_data=data, columns=columns_name, number=len(columns_name),
                           prob_ids=prob_ids, lenth=len(data))


@app.route('/approve_problem/<id>/<prob_id>', methods=["POST"])
def approve_problem(id, prob_id):
    cur = con.cursor()
    cur.execute('''UPDATE "No_problem".problem
                                SET status_id = (SELECT st.id 
                                                 FROM "No_problem".status as st
                                                 WHERE st.name = %s)
                                WHERE id = %s''', ('На выполнении', prob_id))
    con.commit()
    cur.close()
    return redirect(url_for('orders_confirmation', id=id))


@app.route('/reject_problem/<id>/<prob_id>', methods=["POST"])
def reject_problem(id, prob_id):
    cur = con.cursor()
    cur.execute('''UPDATE "No_problem".problem
                                    SET status_id = (SELECT st.id 
                                                     FROM "No_problem".status as st
                                                     WHERE st.name = %s),
                                        solve_client_id = %s
                                    WHERE id = %s''', ('Выложена',  0, prob_id))
    con.commit()
    cur.close()
    return redirect(url_for('orders_confirmation', id=id))


if __name__ == "__main__":
    app.run(debug=True)