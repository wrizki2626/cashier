from flask import Flask, render_template, request, url_for, redirect, flash, session, abort, jsonify
from functools import wraps
from hashlib import sha256
import json, requests
import base64
from base64 import encodebytes

app = Flask(__name__)
app.secret_key = 'asdiquwbebd12365sdfn'


# def auth_user(user):
#     session['logged_in'] = True
#     # session['user_id'] = user.id
#     session['nama'] = ka

def get_curret_user():
    if session.get('logged_in'):
        return session['id_karyawan']
    # session['user_id']

def redirect_to_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('id_karyawan'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def redirect_after_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('id_karyawan'):
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(500)
def page_not_found(error):
    return render_template('404.html'), 500


def format_rupiah(number):
    # Mengubah angka menjadi string dan menghapus karakter non-digit
    number = str(number).replace(',', '').replace('.', '')

    # Mengecek apakah angka valid
    if not number.isdigit():
        raise ValueError('Invalid number')

    # Mengubah string angka menjadi integer
    number = int(number)

    # Mengubah angka menjadi format rupiah
    rupiah = "Rp. {:,}".format(number).replace(',', '.')

    return rupiah

def MagerDicts(dict1,dict2):
    if isinstance(dict1, list) and isinstance(dict2,list):
        return dict1  + dict2
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items()) + list(dict2.items()))



@app.route('/', methods=['GET','POST'])
@redirect_after_login
def index():
    if request.method == 'POST':
        form_email = request.form['email']
        form_password = request.form['password']

        data_login = {
            "email" : form_email,
            "password" : form_password
            }
            
        dataLogin_json = json.dumps(data_login)
        alamatserver = "http://localhost:5055/api/loginkaryawan"
        headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
        kirimdata = requests.post(alamatserver, data=dataLogin_json, headers=headers)
        cow = json.loads(kirimdata.text)

        # print(cow)
        if cow["message"] == "sukses":
            session['Shoppingcart'] = {}
            session['email'] = form_email
            session["id_karyawan"] = cow["auth_karyawan"]["karyawan_id"]
            return redirect(url_for('dashboard'))
        elif cow["message"] == "gagal":
            flash('Data karyawan tidak ditemukan', 'alert-danger')    
    return render_template('index.html')

@app.route('/dashboard', methods=['GET','POST'])
@redirect_to_login
def dashboard():

    alamatserver = "http://localhost:5055/api/todashboardcashier/"  
    headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
    kirimdata = requests.get(alamatserver, headers=headers)
    rows = json.loads(kirimdata.text)

    jumlah_produk = rows["jumlah_produk"]
    transaksi_hari_ini = rows["transaksi_hari_ini"]
    jumlah_toko = rows["jumlah_toko"]



    return render_template("dashboard.html", jumlah_produk=jumlah_produk, transaksi_hari_ini=transaksi_hari_ini, jumlah_toko=jumlah_toko)


@app.route('/pemesanan', methods=['GET','POST'])
@redirect_to_login
def pemesanan():
    alamatserver = "http://localhost:5055/api/productall/"  
    headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
    kirimdata = requests.get(alamatserver, headers=headers)
    rows = json.loads(kirimdata.text)


    return render_template('pemesanan.html', rows=rows, format_rupiah=format_rupiah)

@app.route('/pemesanansearch', methods=['GET', 'POST'])
@redirect_to_login
def pemesanansearch():
    if request.method == 'POST':
        error = None
        inputSearch = request.form['formoption']

        if not inputSearch or not inputSearch.strip():
            error = 'Pilih kategori terlebih dahulu'

        if error != None:
            flash(error, 'alert-danger')
            return redirect(url_for('pemesanan'))
        elif error is None:
            data_search = {
                "formoption" : inputSearch
                }

        dataSearch_json = json.dumps(data_search)
        alamatserver = "http://localhost:5055/api/productsearch/"
        headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
        kirimdata = requests.get(alamatserver, data=dataSearch_json, headers=headers)
        rows = json.loads(kirimdata.text)

        return render_template('pemesanan.html', rows=rows, format_rupiah=format_rupiah)

    return redirect(url_for('pemesanan'))


@app.route('/addcart', methods=['POST'])
def AddCart():
    try:
        product_id = request.form.get('productid')
        quantity = int(request.form.get('quantity'))

        alamatserver = f"http://localhost:5055/api/productbyid/{product_id}"
        headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
        kirimdata = requests.get(alamatserver, headers=headers)
        product = json.loads(kirimdata.text)

        nama = product['nama']
        harga = product['harga']

        if request.method =="POST":
            DictItems = {product_id:{'namaproduk':nama,'harga':harga,'kuantitas':quantity}}
            if 'Shoppingcart' in session:
                print(session['Shoppingcart'])
                if product_id in session['Shoppingcart']:
                    for key, item in session['Shoppingcart'].items():
                        if key == product_id:
                            session.modified = True
                            item['kuantitas'] += 1
                else:
                    session['Shoppingcart'] = MagerDicts(session['Shoppingcart'], DictItems)
                    return redirect(request.referrer)
            else:
                session['Shoppingcart'] = DictItems
                return redirect(request.referrer)
              
    except Exception as e:
        print(e)
    finally:
        return redirect(request.referrer)


@app.route('/carts', methods=['POST', 'GET'])
def getCart():
    if request.method == 'POST':
            error = None
            id_siswa = request.form['idsiswa']
            harga_total =  request.form['harga_total']

            try:
                if not id_siswa or not id_siswa.strip():
                    error = 'Masukkan id siswa terlebih dahulu'
                elif error != None:
                    flash(error, 'alert-danger')
                    return redirect(url_for('getCart'))

                data_cek_id = {
                    "id_siswa" : id_siswa,
                    "harga_total": harga_total
                }

                dataSearch_json = json.dumps(data_cek_id)
                alamatserver = "http://127.0.0.1:5055/api/getsaldo"
                headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
                kirimdata = requests.get(alamatserver, data=dataSearch_json, headers=headers)
                rows1 = json.loads(kirimdata.text)
            except Exception as e:
                print(e)
                return redirect(url_for('getCart'))

            try:
                data_cek_saldo = {
                    "id_siswa" : id_siswa
                    # "harga_total": harga_total
                }

                dataSearchId_json = json.dumps(data_cek_saldo)
                alamatserver = "http://127.0.0.1:5055/api/outofid"
                headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
                kirimdata = requests.get(alamatserver, data=dataSearchId_json, headers=headers)
                cekid = json.loads(kirimdata.text)
            except Exception as e:
                print(e)
                return redirect(url_for('getCart'))

            try:
                if not id_siswa or not id_siswa.strip():
                    error = 'Masukkan id siswa terlebih dahulu'
                elif error != None:
                    flash(error, 'alert-danger')
                    return redirect(url_for('getCart'))
                # if rows1["saldo"] != "ada":
                #     error = "Maaf saldo anda kurang"
                # elif cekid["message"] != "ada":
                #     error = "Maaf id siswa tidak ditemukan"
                # elif error != None:
                #     flash(error, 'alert-danger')
                #     return redirect(url_for('getCart'))


                data_order = {
                    "id_siswa" : id_siswa,
                    "harga_total":harga_total,
                    "detail_pesanan":session['Shoppingcart']
                }

                dataSearch_json = json.dumps(data_order)
                alamatserver = "http://localhost:5055/api/order/"
                headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
                kirimdata = requests.post(alamatserver, data=dataSearch_json, headers=headers)
                feedback = json.loads(kirimdata.text)

                message = feedback["messages"]
                style = feedback["style"]

                flash(message, style)
                if style == "alert-success":
                    session.pop('Shoppingcart', None)
            except Exception as error:
                error = "Masukkan id siswa"
        # except IndexError:
        #     abort(500)


    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('pemesanan'))
    subtotal = 0
    grandtotal = 0
    for key,product in session['Shoppingcart'].items():
        subtotal += product['harga'] * int(product['kuantitas'])
        grandtotal = subtotal

    alamatserver = "http://localhost:5055/api/outofid/"  
    headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
    kirimdata = requests.get(alamatserver, headers=headers)
    rows = json.loads(kirimdata.text)

    return render_template('cart.html', grandtotal=grandtotal, format_rupiah=format_rupiah, maxidsiswa=rows)

@app.route('/updatecart/<int:code>', methods=['POST'])
def updatecart(code):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('home'))
    if request.method =="POST":
        quantity = request.form.get('kuantitas')
        try:
            session.modified = True
            for key , item in session['Shoppingcart'].items():
                if int(key) == code:
                    item['kuantitas'] = quantity
                    flash('Item kuantitas sudah terupdate!', 'alert-success')
                    return redirect(url_for('getCart'))
        except Exception as e:
            print(e)
            return redirect(url_for('getCart'))



@app.route('/deleteitem/<int:id>')
def deleteitem(id):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('pemesanan'))
    try:
        session.modified = True
        for key , item in session['Shoppingcart'].items():
            if int(key) == id:
                session['Shoppingcart'].pop(key, None)
                return redirect(url_for('getCart'))
    except Exception as e:
        print(e)
        return redirect(url_for('pemesanan'))



@app.route('/ceksaldo', methods=['POST', 'GET'])
@redirect_to_login
def ceksaldo():
    rows = {}

    alamatserver = "http://localhost:5055/api/outofid/"  
    headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
    kirimdata = requests.get(alamatserver, headers=headers)
    outofid = json.loads(kirimdata.text)

    return render_template('ceksaldo.html', rows=rows, maxidsiswa=outofid)

@app.route('/searchsiswa', methods=['GET','POST'])
@redirect_to_login
def searchsiswa():
    if request.method == 'POST':
        error = None
        id_siswa = request.form['idsiswa']

        if not id_siswa or not id_siswa.strip():
            error = 'Masukkan id siswa terlebih dahulu'

        if error != None:
            flash(error, 'alert-danger')
            return redirect(url_for('ceksaldo'))
        elif error is None:
            data_form = {
                "id_siswa" : id_siswa,
                }

        dataSearch_json = json.dumps(data_form)
        alamatserver = "http://127.0.0.1:5055/api/ceksaldo"
        headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
        kirimdata = requests.get(alamatserver, data=dataSearch_json, headers=headers)
        rows = json.loads(kirimdata.text)


    alamatserver = "http://localhost:5055/api/outofid/"  
    headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
    kirimdata = requests.get(alamatserver, headers=headers)
    outofid = json.loads(kirimdata.text)

    return render_template('ceksaldo.html', rows=rows, format_rupiah=format_rupiah,  maxidsiswa=outofid)

@app.route('/riwayattransaksi', methods=['GET','POST'])
@redirect_to_login
def riwayattransaksi():


    alamatserver = f"http://localhost:5055/api/semuahistoripesanan/"
    datas = requests.get(alamatserver)
    rows = json.loads(datas.text)

    return render_template('riwayattransaksi.html', rows=rows, format_rupiah=format_rupiah)


@app.route('/searchriwayat', methods=['GET', 'POST'])
@redirect_to_login
def searchriwayat():
    if request.method == 'POST':
        error = None
        form_input = request.form['forminput']

        if not form_input or not form_input.strip():
            error = 'Form harus terisi'

        if error != None:
            flash(error, 'alert-danger')

        try:
            if error is None:
                data_search = {
                    'forminput': form_input
                }

                data_dump_json = json.dumps(data_search)
                alamatserver = "http://localhost:5055/api/searchHistoripesananbyid/"
                headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
                kirimdata = requests.get(alamatserver, data=data_dump_json, headers=headers)
                rows = json.loads(kirimdata.text)

                return render_template('riwayattransaksi.html', rows=rows, format_rupiah=format_rupiah)
        except:
            error = "sisis server gagal"

    alamatserver = f"http://localhost:5055/api/semuahistoripesanan/"
    datas = requests.get(alamatserver)
    rows = json.loads(datas.text)

    return render_template('riwayattransaksi.html', rows=rows, format_rupiah=format_rupiah)
           


@app.route('/detail/<int:id>', methods=['GET', 'POST'])
@redirect_to_login
def detail(id):

    alamatserver = f"http://127.0.0.1:5055/api/detailpesanan/{id}"
    headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
    datas = requests.get(alamatserver, headers=headers)

    rows = json.loads(datas.text)

    detailPesanan = rows['detail']
    namaanak = rows['namanya']
    ttl_pemesanan = rows['ttl_pemesanan']
    totalPembayaran = rows['totalPembayaran']

    totalHarga = format_rupiah(totalPembayaran)
    # print(totalHarga)

    return render_template('detail.html', detailPesanan=detailPesanan, namaanak=namaanak, ttl_pemesanan=ttl_pemesanan, totalHarga=totalHarga, format_rupiah=format_rupiah)


@app.route('/logout', methods=['GET','POST'])
def logout():
    if request.method == 'GET':
        # membuat data dummy untuk permintaan menghapus session pada server yang id karyawan
        hapus_session = {
            'session_hapus' : True
        }

        dataHapusSession_json = json.dumps(hapus_session)
        alamatserver = "http://localhost:5055/api/logoutkaryawan"
        headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
        kirimdata = requests.get(alamatserver, data=dataHapusSession_json, headers=headers)
        
    session.pop('id_karyawan', None)
    session.pop('Shoppingcart', None)
    flash('You are now logged out','alert-success')
    return redirect(url_for('index'))

if __name__ == '__main__':
	app.run(
		debug=True,
		host='0.0.0.0',
        port=5057
		)