from flask import Flask, render_template, g, redirect, url_for, request, session
from sqlite3 import connect, Connection, Cursor
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import DB
import forms
import os



from models import UserLogin



app = Flask(__name__)
app.config['DATABASE'] = 'static/db/database.db'
app.config['SECRET_KEY'] = 'secret'
app.config['UPLOAD_FOLDER_CAR'] = 'static/image/products'


def connect_db():
   con = connect(app.config['DATABASE'])
   return con


def get_connect():
    if not hasattr(g, 'link_db'):
      g.link_db = connect_db()
    return g.link_db

@app.teardown_appcontext
def close_db(error):
   if hasattr(g, 'link_db'):
    g.link_db.close()

listMenu = [
   {'link':'/index/', 'name':'Главная'},
   {'link':'/allProducts/', 'name':'Вся продукция'}

]

login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(user_id):
    print('load_user')
    return UserLogin().formDB(user_id, DB.UserDB(get_connect()))

def list_brand():
    objects = DB.Cars(get_connect())
    lst = objects.get_all_Brand()
    return lst



def profile():
    username = (current_user.login,current_user.role) if current_user.is_authenticated else ' '
    return username


@app.route('/')
@app.route('/index/')
def index():
    objects = DB.Cars(get_connect())
    lst = objects.get_random_Car(8)
    # print(lst[0][4])
    return render_template('index.html', carsList = lst, menu = listMenu, brands = list_brand(), name = profile())



def sortCar(objects,sort_by):

    if sort_by == "price_asc":
        return objects.sorted_car_priceASC()

    elif sort_by == "price_desc":
        return objects.sorted_car_priceDESC()

    elif sort_by == "name_asc":
        return objects.sorted_car_name()
    
    else:
        return objects.get_allCars()



@app.route('/allProducts/')
def allProducts():
    objects = DB.Cars(get_connect())
    sort_by = request.args.get('sort_by')
    lst = sortCar(objects, sort_by)

    return render_template('allProducts.html', carsList = lst, menu = listMenu, brands = list_brand(), name = profile())


@app.route("/car/<name>")
def car(name):
    objects = DB.Cars(get_connect())
    lst = objects.get_carByName(name)
    # print(lst[1])
    return render_template('car.html', carsList=lst, brands = list_brand(), menu = listMenu, name = profile())



@app.route("/adminPanel/", methods=['POST','GET'])
@login_required
def add():
    if current_user.role == 'admin':

        objects = DB.Cars(get_connect())

        formCar = forms.addCar()
        formBrand = forms.addBrand()
        allCars = objects.get_allCars()

        if request.method == 'POST':
            if 'submit_car' in request.form:
                if formCar.validate_on_submit():

                    name=formCar.name.data
                    price=formCar.price.data
                    descriptionCar=formCar.descriptionCar.data
                    brandCar=formCar.brandCar.data
                    images=formCar.images.data

                    # Имя для папки
                    folder_name = name.replace(' ', '_')
                    folder_path = os.path.join(app.config['UPLOAD_FOLDER_CAR'], folder_name)
                    # Создание новой папки для автомобиля
                    os.makedirs(folder_path, exist_ok=True)

                    # Сохранение файла с оригинальным именем в новую папку
                    for image in images:
                        if image and image.filename:
                            filename = secure_filename(image.filename)
                            image_path = os.path.join(folder_path, filename)
                            image.save(image_path)

                    objects.add_car(name, price, descriptionCar,brandCar, folder_name)
                    print("Added car")
                    return redirect('/adminPanel/')    
            elif 'submit_brand' in request.form:
                if formBrand.validate_on_submit():
                    objects.add_Brand(formBrand.brand.data, formBrand.descriptionBrand.data)
                    print("Added brand")
                    return redirect('/adminPanel/')
            elif 'delete_car' in request.form:
                car_id = request.form['car_id']
                objects.delete_car(car_id)
                return redirect('/adminPanel/')
  
        return render_template('adminPanel.html', formCar=formCar, formBrand=formBrand, brands = list_brand(), menu = listMenu, name = profile(), allCars = allCars)
    else:
        return "ты не админ!!!"




@app.route('/brandCar/<brand>')
def brandCar(brand):
   objects = DB.Cars(get_connect())
   lst = objects.get_carByBrand(brand)
   Brand = objects.get_BrandByName(brand)

   return render_template('brandCar.html', carsList=lst, brands = list_brand(), menu = listMenu, brand=Brand, name = profile())


@app.route("/login/", methods=['POST','GET'])
def login():
    form = forms.Authorization()

    log = form.login.data
    passw = form.password.data
    Object = DB.UserDB(get_connect())

    u = Object.loginUser(log)
    if u and check_password_hash(u[2], passw):
        userlogin = UserLogin().create(u)
        login_user(userlogin)
        return redirect('/')


    return render_template('login.html', form=form,  brands = list_brand(), menu = listMenu, name = profile())


@app.route("/register/", methods=['POST','GET'])
def register():
    form = forms.Registration()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        Object = DB.UserDB(get_connect())
        Object.registration(form.login.data, hashed_password)
        print('ВОШЕЛ')
        return redirect('/login/')
    return render_template('register.html', form=form,  brands = list_brand(), menu = listMenu, name = profile())



@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect('/')




app.config['TEMPLATES_AUTO_RELOAD'] = True
if __name__ == "__main__":
  app.run()