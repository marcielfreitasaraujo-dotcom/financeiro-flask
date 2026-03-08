from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "segredo"


def conectar():
    return sqlite3.connect("banco.db")


# ---------------- CRIAR TABELAS ----------------

def criar_tabelas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT,
        tipo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT,
        valor REAL,
        data TEXT,
        usuario_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT,
        valor REAL,
        data TEXT,
        usuario_id INTEGER
    )
    """)

    conn.commit()

    # criar admin automaticamente se não existir
    cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'")
    admin = cursor.fetchone()

    if not admin:
        cursor.execute(
            "INSERT INTO usuarios (usuario, senha, tipo) VALUES ('admin','123','admin')"
        )
        conn.commit()

    conn.close()


# 🔹 ESTA LINHA FOI ADICIONADA (para funcionar no Render)
with app.app_context():
    criar_tabelas()


# ---------------- LOGIN ----------------

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/registrar")
def registrar():
    return render_template("registrar.html")


@app.route("/criar_usuario", methods=["POST"])
def criar_usuario():

    usuario = request.form["usuario"]
    senha = request.form["senha"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
        (usuario, senha, "usuario")
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/logar", methods=["POST"])
def logar():

    usuario = request.form["usuario"]
    senha = request.form["senha"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM usuarios WHERE usuario=? AND senha=?",
        (usuario, senha)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        session["usuario_id"] = user[0]
        session["usuario"] = user[1]
        session["tipo"] = user[3]

        return redirect("/dashboard")

    return "Usuário ou senha incorretos"


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "usuario_id" not in session:
        return redirect("/")

    usuario_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT SUM(valor) FROM receitas WHERE usuario_id=?",
        (usuario_id,)
    )
    receitas = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT SUM(valor) FROM despesas WHERE usuario_id=?",
        (usuario_id,)
    )
    despesas = cursor.fetchone()[0] or 0

    saldo = receitas - despesas

    cursor.execute(
        "SELECT * FROM receitas WHERE usuario_id=?",
        (usuario_id,)
    )
    lista_receitas = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM despesas WHERE usuario_id=?",
        (usuario_id,)
    )
    lista_despesas = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        receitas=receitas,
        despesas=despesas,
        saldo=saldo,
        lista_receitas=lista_receitas,
        lista_despesas=lista_despesas,
        usuario=session["usuario"],
        tipo=session["tipo"]
    )


# ---------------- GERENCIAR USUARIOS (ADMIN) ----------------

@app.route("/usuarios")
def usuarios():

    if session.get("tipo") != "admin":
        return redirect("/dashboard")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id, usuario, tipo FROM usuarios")
    lista = cursor.fetchall()

    conn.close()

    return render_template("usuarios.html", usuarios=lista)


# ---------------- EXCLUIR USUARIO ----------------

@app.route("/excluir_usuario/<int:id>")
def excluir_usuario(id):

    if session.get("tipo") != "admin":
        return redirect("/dashboard")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/usuarios")


# ---------------- ADICIONAR RECEITA ----------------

@app.route("/add_receita", methods=["POST"])
def add_receita():

    descricao = request.form["descricao"]
    valor = request.form["valor"]
    data = request.form["data"]
    usuario_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO receitas (descricao, valor, data, usuario_id)
        VALUES (?, ?, ?, ?)
    """, (descricao, valor, data, usuario_id))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- ADICIONAR DESPESA ----------------

@app.route("/add_despesa", methods=["POST"])
def add_despesa():

    descricao = request.form["descricao"]
    valor = request.form["valor"]
    data = request.form["data"]
    usuario_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO despesas (descricao, valor, data, usuario_id)
        VALUES (?, ?, ?, ?)
    """, (descricao, valor, data, usuario_id))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- EXCLUIR RECEITA ----------------

@app.route("/excluir_receita/<int:id>")
def excluir_receita(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM receitas WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- EXCLUIR DESPESA ----------------

@app.route("/excluir_despesa/<int:id>")
def excluir_despesa(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM despesas WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- INICIAR APP ----------------

if __name__ == "__main__":

    criar_tabelas()

app.run(host="0.0.0.0", port=10000)