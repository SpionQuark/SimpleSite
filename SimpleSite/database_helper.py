from SimpleSite.database_handler import Database
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

db = Database("./application.db")

pw = PasswordHasher()

async def start():
    await db.connect()

async def register_user(name: str, password:str, perms:int=10):
    query = "INSERT INTO users(name, pass_hash, perms) VALUES ($1, $2, $3)"
    return await db.execute(query, (name, pw.hash(password), perms,))

async def check_login(name, password) -> bool:
    query = "SELECT pass_hash FROM users WHERE name=$1"
    row = await db.query_one(query, (name,))
    if row is None:
        return False
    try:
        return pw.verify(row["pass_hash"], password)
    except VerifyMismatchError:
        return False

