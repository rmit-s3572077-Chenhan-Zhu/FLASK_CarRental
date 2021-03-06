﻿# encoding: utf-8
'''
 @Time : 2018/04/05 10:45
 @Author: ChenHan Zhu, Hong Wu
'''
from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint, jsonify,abort,Response
import config
import requests
from modules import User, Car_rental, CarsDataset,Cars
from exits import db
import os
from decoratars import login_required
from flask_googlemaps import GoogleMaps,Map
from flask_admin import *
import random

from flask_admin.contrib import sqla
from flask_basicauth import BasicAuth
from flask_admin.contrib.sqla import ModelView
from werkzeug.exceptions import HTTPException
# from flask_login import LoginManager,UserMixin

from math import *

ip = '128.250.51.47'
url = 'http://freegeoip.net/json/' + ip
r = requests.get(url)
js = r.json()


app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
app.secret_key = os.urandom(24)
GoogleMaps(app)


# admin management page 
admin = Admin(app, name='WIN Admin', template_mode='bootstrap3')
from modules import User, Cars,CarsDataset
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Cars, db.session))
admin.add_view(ModelView(CarsDataset, db.session))


# main page for win rental
@app.route('/')
# @login_required
def index():
    username = {}
    try:
        username=session['username']
    except KeyError:
        print 'no Peer'
    return render_template('index.html',username=username)



#function login
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        if request.form.get('register'):
            return redirect(url_for('register'))

        username = request.form.get('username')
        password = request.form.get('password')
        # authorid=request.form('')
        user = User.query.filter(User.username == username, User.password == password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['password'] = user.password
            session.permanent = True
            if session['username']=='admin':
                return redirect('/admin/')
            else:
                return redirect('/')
        else :
            return u'wrong username or password,please try again '

# function register
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if password1 != password2:
            return u'different passwords,please try again!'
        if User.query.filter_by(username=username).first():
            return 'the username had been used, please try other name'

        else:
            user = User(username=username, password=password1)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))



@app.route('/logout/')
@login_required
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.context_processor
def my_context_processor():
    user = session.get('username')
    if user:
        return {'user': user}
    return {}


def url_for_other_page(page):
    # args = request.view_args.copy()
    args = dict(request.view_args.items() + request.args.to_dict().items())  # 如果采用上面那句则换页时querystring会丢失
    args['page'] = page
    return url_for(request.endpoint, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page


# set unique URL for each user
@app.route('/users/<username>/')
@login_required
def get_users(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('users.html', user=user)


# contact us page
@app.route('/ContactUs/', methods=['GET', 'POST'])
def ContactUs():
    username = {}
    try:
        username = session['username']
    except KeyError:
        print 'no Peer'
    return render_template('ContactUs.html',username=username)


# faq page
@app.route('/faq/', methods=['GET', 'POST'])
def faq():
    username = {}
    try:
        username = session['username']
    except KeyError:
        print 'no Peer'
    return render_template('Faq.html',username=username)

# save car
@app.route('/booking/savecar',methods=['POST'])
@login_required
def bookingsavecar():
    if request.method == 'POST':
        # value from post
        Bdatetime = request.form.get('Bdatetime')
        Btime = request.form.get('Btime')
        Bday = request.form.get('Bday')
        Rdatetime = request.form.get('Rdatetime')
        Rtime = request.form.get('Rtime')
        Rday = request.form.get('Rday')

        name = request.form['name']
            # brand = request.form['brand']
            # seat = request.form['seat']
            # bluetooth = request.form['bluetooth']
            # vehicleType = request.form['vehicleType']

        # return 'test'

        carinfo = Cars(Rdatetime=Rdatetime, Bdatetime=Bdatetime, carname=name,
                       Rday=Rday, Rtime=Rtime, Btime=Btime, Bday=Bday)

        user_id = session.get('user_id')
        user = User.query.filter(User.id == user_id).first()
        carinfo.author = user
        db.session.add(carinfo)
        db.session.commit()
        return redirect(url_for('booking'))


# get values from map
@app.route('/booking/car/', methods=['GET', 'POST'])
@login_required
def bookingcar():
    username = session['username']
    if request.method == 'GET':
        # return map
        return redirect(url_for('booking'))
        #return render_template('car.html',name='tom')
    else:
     # values from map
        name = request.form['name']
        price = request.form['price']
        brand = request.form['brand']

        seat = request.form['seat']
        bluetooth = request.form['bluetooth']
        vehicleType = request.form['vehicleType']

        kilometer = request.form['kilometer']


        #return 'test'


        return render_template('car.html', name=name, price=price, brand=brand, bluetooth=bluetooth, seat=seat,
                               vehicleType=vehicleType, username=username,kilometer=kilometer)


#return car function
@app.route('/return/car/', methods=['GET', 'POST'])
@login_required
def returncar():
    if request.method == 'POST':
        carname = request.form.get('name')
        car = Cars.query.filter_by(carname=carname).first()
        db.session.delete(car)
        db.session.commit()
        print("Return car", carname)

    return redirect(url_for('booking'))

def rand(a,b):
    return random.random()*(a-b)+b

def get_dist(car_loc, user_loc):
    x = abs(car_loc[0]-user_loc[0])
    y = abs(car_loc[1]-user_loc[1])
    return pow(x,2)+pow(y,2)


# booking car function
def rand(a,b):
    return random.random()*(a-b)+b
@app.route('/booking/', methods=['GET', 'POST'])
@login_required
def booking():
    min_dist = 999999
    username = session['username']
    user_id = session['user_id']
    user_loc = (-37.801, 144.961)
    # print("Leo", user_id)
    page_data = CarsDataset.query
    for p in page_data:
        name = p.serializer()['name']
        db.session.query(CarsDataset).filter(CarsDataset.name==name).update(
            {'lat': rand(-37.817000,-37.778999), 'lng': rand(144.95000,144.99399)})
    db.session.commit()
    tid = request.args.get("tid", 0)
    # print(tid)
    avail_cars = CarsDataset.query.filter_by(name='NOEXIST')
    for p in page_data:
        name = p.serializer()['name']
        if (int(tid) == -1):
            db.session.query(CarsDataset).filter(CarsDataset.name==name).update({'lat': rand(-37.817000,-37.778999), 'lng': rand(144.95000,144.99399)})
    db.session.commit()

# filter result according to different condition
    if int(tid) > 0:
        if int(tid) == 1:
            page_data = page_data.filter_by(brand='audi')

        if int(tid) == 2:
            page_data = page_data.filter_by(brand='volkswagen')

        if int(tid) == 3:
            page_data = page_data.filter_by(brand='bmw')

        if int(tid) == 4:
            page_data = page_data.filter_by(brand='peugeot')

        if int(tid) == 5:
            page_data = page_data.filter_by(brand='mercedesBenz')

        if int(tid) == 6:
            page_data = page_data.filter_by(brand='ford')

    time = request.args.get("time", 0)
    if int(time) == 1:
        page_data = page_data.filter_by(gearbox='manual')
    if int(time) == 2:
        page_data = page_data.filter_by(gearbox='automatic')
    if int(time) == 3:
        nearest = ""
        for p in page_data:
            name = p.serializer()['name']
            if Cars.query.filter_by(carname=name).count() > 0: continue
            car_loc = (p.serializer()['lat'], p.serializer()['lng'])
            dist = get_dist(car_loc, user_loc)
            # print(name, dist)
            if dist < min_dist:
                nearest = name
                min_dist = dist
        page_data = page_data.filter_by(name=nearest)

    pm = request.args.get("pm", 0)
    p = dict(
        tid=tid,
        time=time,
        pm=pm
    )
    locations = [d.serializer() for d in page_data]

    Lat_A = -37.80314407
    Lng_A = 144.9655776
    Lat_B = page_data.with_entities(CarsDataset.lat).all()
    Lng_B = page_data.with_entities(CarsDataset.lng).all()
    sb = haversine(Lng_A, Lat_A, Lng_B, Lat_B)
    sb = [s for s in sb]

    context = {
        'CarsDataset': CarsDataset.query.all()
    }


    boxcontent = "<form method='post' action='http://www.wincarshare.tk/booking/car/'><div>{0}<input type='hidden' name='name' value='{0}'/></div>"" \
    ""<div>{1}$/Day<input type='hidden' name='price' value='{1}'/><div><input type='hidden' name='brand' value='{2}'/></div> <div><input type='hidden' name='seat' value='{3}'/></div>" \
    "<div><input type='hidden' name='bluetooth' value='{4}'/></div>" \
    "<div><input type='hidden' name='vehicleType' value='{5}'/></div>" \
    "<div><input type='hidden' name='kilometer' value='{6}'/></div>" \
    "</div><button type='submit'class=btn btn-primary>book</button></form>"

    return_boxcontent = "<form method='post' action='http://www.wincarshare.tk/return/car/'><div>{0}<input type='hidden' name='name' value='{0}'/></div>"" \
    ""<div>{1}$/Day<input type='hidden' name='price' value='{1}'/><div><input type='hidden' name='brand' value='{2}'/></div> <div><input type='hidden' name='seat' value='{3}'/></div>" \
    "<div><input type='hidden' name='bluetooth' value='{4}'/></div>" \
    "<div><input type='hidden' name='vehicleType' value='{5}'/></div>" \
    "<div><input type='hidden' name='kilometer' value='{6}'/></div>" \
    "</div><button type='submit' onclick=\"{7}\" class=btn btn-primary>return</button></form>"

#shows location marks on the map
    allmarkers = []
    booked_markers = []

    for loc in locations:
        rcd = Cars.query.filter_by(carname=loc['name'])
        if rcd.count() == 0:
            m = { "lat": loc['lat'], "lng": loc['lng'],
                "infobox": boxcontent.format(loc['name'].encode('utf-8'), loc['price'], loc['brand'].encode('utf-8'), loc['seat'],
                loc['bluetooth'], loc['vehicleType'],loc['kilometer'])}
            allmarkers.append(m)
        else:
            if user_id == rcd.first().author_id:
                # print("Leo", "Found user booked car", loc['name'])
                # print(return_boxcontent)
                m = {"icon":"http://maps.google.com/mapfiles/ms/icons/blue-dot.png", "lat": loc['lat'], "lng": loc['lng'],
                "infobox": return_boxcontent.format(loc['name'].encode('utf-8'), loc['price'],
                            loc['brand'].encode('utf-8'), loc['seat'], loc['bluetooth'], loc['vehicleType'],loc['kilometer'], "{if(confirm('Are you confirm to return')) {alert('Congratulation，Return Success!');return true; }return false;}")}
                allmarkers.append(m)
    user_marker = {"lat": user_loc[0], "lng": user_loc[1], 'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png', "infobox": "<b>You are here</b>"}
    # print(user_marker)
    allmarkers.append(user_marker)

#google map api on python
    carmap = Map(
        identifier="carmap",
        style="height:700px;width:744px;margin:0;",
        zoom="15",
        language="en",

        # lat=locations[0]['lat'],
        lat =-37.80314407,
        # lng=locations[0]['lng'],
        lng=144.9655776,
        icon="http://maps.google.com/mapfiles/ms/icons/red-dot.png",
        name=locations[0]['name'],
        brand=locations[0]['brand'],
        seat=locations[0]['seat'],
        bluetooth=locations[0]['bluetooth'],
        vehicleType=locations[0]['vehicleType'],
        kilometer=locations[0]['kilometer'],
        price=locations[0]['price'],

        markers=allmarkers
    )
    return render_template('booking.html', carmap=carmap, page_data=page_data, sb=sb, p=p, username=username,**context)



#booking history
@app.route('/users/tables/', methods=['GET', 'POST'])
@login_required
def tables():
    username = session['username']
    author_id = session['user_id']



    context = {
        'Cars': Cars.query.filter_by(author_id=author_id)
    }

    return render_template('tables.html',username=username,**context)


# the formula for calculating distance between different cars coordinates
def haversine(lon1, lat1, lon2, lat2):  # longitude1，longitude1，latitude2，latitude2
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    conter = 0
    for x, y in zip(lon2, lat2):
        conter += 1
        # print(x[0], y[0], conter, lon1, lat1)
        lon1_, lat1_, lon2, lat2 = map(radians, [lon1, lat1, x[0], y[0]])
        # haversine formula
        dlon = lon2 - lon1_
        dlat = lat2 - lat1_
        a = sin(dlat / 2) ** 2 + cos(lat1_) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # radius of earth
        yield c * r


#jsonify the dataset
@app.route('/api/cardatas')
def fetch_cardata():
    datas = CarsDataset.query.all()
    return jsonify({'data': [d.serializer() for d in datas]})


if __name__ == '__main__':
    app.run()