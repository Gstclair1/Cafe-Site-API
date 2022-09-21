from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, url
import csv
from csv import writer
from flask_sqlalchemy import SQLAlchemy
import random
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
db = SQLAlchemy(app)

Bootstrap(app)

YES_NO = ['Yes', 'No']


class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class CafeForm(FlaskForm):
    cafe = StringField('Cafe name', validators=[DataRequired()])
    loc = StringField('Location', validators=[DataRequired()])
    map_url = StringField('Link in Google Maps', validators=[DataRequired(), url()])
    img_url = StringField('Link for Cafe Image', validators=[DataRequired()])
    seats = StringField('Seating Capacity', validators=[DataRequired()])
    toilet = SelectField('Has Toilets?', choices=YES_NO)
    wifi = SelectField('Has Wifi?', choices=YES_NO)
    sockets = SelectField('Has Power Outlets?', choices=YES_NO)
    calls = SelectField('Can Make Phone Calls?', choices=YES_NO)
    price = StringField('Coffee Price (with Currency Symbol)', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/add', methods=["GET", "POST"])
def add_cafe():
    form = CafeForm()
    if form.validate_on_submit():
        name = form.cafe.data
        loc = form.loc.data
        map_url = form.map_url.data
        img_url = form.img_url.data
        seats = form.seats.data
        toilet = form.toilet.data
        wifi = form.wifi.data
        sockets = form.wifi.data
        calls = form.calls.data
        price = form.calls.data


    return render_template('add.html', form=form)


@app.route('/cafes')
def cafes():
    all_response = requests.get('http://127.0.0.1:5000/all')
    all_json = all_response.json()
    cat_names = []
    for cat in all_json['cafes'][0]:
        cat_names.append(cat)
    cafe_details = [['Name', 'Location', 'Can Take Calls', "Coffee Price", 'Power Outlets Available', 'Bathrooms', 'WiFi', 'Seats']]
    for item in all_json['cafes']:
        idv_cafe_detail = []
        for cat in cat_names:
            print(item[cat])
            if item[cat]:
                idv_cafe_detail.append("✔")
            elif not item[cat]:
                idv_cafe_detail.append('❌')
            else:
                idv_cafe_detail.append(item[cat])
        cafe_details.append(idv_cafe_detail)
    print(cafe_details)
    return render_template('cafes.html', cafes=cafe_details)


#API Section
## HTTP GET - Read Record
@app.route("/random")
def get_random_cafe():
    cafes = db.session.query(Cafe).all()
    random_cafe = random.choice(cafes)
    return jsonify(cafe={
        "id": random_cafe.id,
        "name": random_cafe.name,
        "map_url": random_cafe.map_url,
        "img_url": random_cafe.img_url,
        "location": random_cafe.location,
        "seats": random_cafe.seats,
        "has_toilet": random_cafe.has_toilet,
        "has_wifi": random_cafe.has_wifi,
        "has_sockets": random_cafe.has_sockets,
        "can_take_calls": random_cafe.can_take_calls,
        "coffee_price": random_cafe.coffee_price,
    })


@app.route("/all")
def get_all_cafes():
    all_cafes = Cafe.query.order_by(Cafe.name).all()
    cafe_dict = [cafe.to_dict() for cafe in all_cafes]
    return jsonify(cafes=cafe_dict)


@app.route("/search", methods=["GET"])
def get_cafes_at_location():
    query_location = request.args.get("loc").capitalize()
    print(query_location)
    cafe = db.session.query(Cafe).filter_by(location=query_location).first()
    print(cafe)
    if cafe:
        return jsonify(cafe=cafe.to_dict())
    else:
        return jsonify(error={
            "Not Found": "Sorry, we don't have a cafe at that location"
        })


## HTTP POST - Create Record
@app.route("/add", methods=["POST"])
def post_new_cafe():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets")),
        has_toilet=bool(request.form.get("toilet")),
        has_wifi=bool(request.form.get("wifi")),
        can_take_calls=bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})


## HTTP PUT/PATCH - Update Record
@app.route('/update/<cafe_id>', methods=["PATCH"])
def update_price(cafe_id):
    cafe_to_update = db.session.query(Cafe).get(cafe_id)
    new_price = request.args.get("coffee_price")
    if cafe_to_update:
        cafe_to_update.coffee_price = new_price
        db.session.commit()
        return jsonify(response={"Success": "Successfully updated the price."}), 200
    else:
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404

## HTTP DELETE - Delete Record


@app.route('/closed/<cafe_id>', methods=["DELETE"])
def cafe_closed(cafe_id):
    api_key = request.args.get("api-key")
    if api_key == "TopSecretAPIKey":
        cafe_to_delete = db.session.query(Cafe).get(cafe_id)
        if cafe_to_delete:
            db.session.delete(cafe_to_delete)
            db.session.commit()
            return jsonify(response={"Success": "Successfully removed closed cafe."}), 200
        else:
            return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
    else:
        return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403



if __name__ == '__main__':
    app.run(debug=True)
