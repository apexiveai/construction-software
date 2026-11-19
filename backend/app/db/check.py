
from sqlalchemy import text
from app.db.session import engine


def check_database():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT current_database(), version()")
            )

            database_name, version = result.fetchone()

            print("=" * 50)
            print("DATABASE CONNECTION: SUCCESS")
            print("DATABASE:", database_name)
            print("VERSION:", version)
            print("=" * 50)

    except Exception as error:
        print("DATABASE CONNECTION: FAILED")
        print("ERROR:", str(error))
        raise


if __name__ == "__main__":
    check_database()
