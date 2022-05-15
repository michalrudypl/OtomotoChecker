import sqlite3


class Database:
    def __init__(self) -> None:
        self.con = sqlite3.connect("otomoto_cars.db")
        self.cur = self.con.cursor()
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS cars (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT
                                            UNIQUE
                                            NOT NULL,
                    brand            STRING  NOT NULL,
                    model            STRING  NOT NULL,
                    milage           INTEGER NOT NULL,
                    production_year  INTEGER NOT NULL,
                    price            INTEGER NOT NULL,
                    from_who         BOOLEAN NOT NULL,
                    is_damaged       BOOLEAN NOT NULL,
                    ad_date_created  DATE    NOT NULL,
                    ad_date_finished DATE
                )"""
        )

    def checked_car_in_db(self, car_id: str) -> bool:
        sql = "SELECT * FROM cars WHERE id=?"
        try:
            res = self.cur.execute(sql, [car_id]).fetchall()
            if res == []:
                return False
            else:
                return True
        except:
            self.cur.close()

    def insert_car(self, car) -> None:
        sql = """INSERT INTO cars (
                     id,
                     brand,
                     model,
                     milage,
                     production_year,
                     price,
                     from_who,
                     is_damaged,
                     ad_date_created
                 )
                 VALUES (
                     ?,
                     ?,
                     ?,
                     ?,
                     ?,
                     ?,
                     ?,
                     ?,
                     ?
                 )"""
        try:
            self.cur.execute(
                sql,
                [
                    car.id,
                    car.brand,
                    car.model,
                    car.milage,
                    car.production_year,
                    car.price,
                    car.from_who,
                    car.is_damaged,
                    car.ad_date_created,
                ],
            )
            self.con.commit()
        except:
            self.cur.close()

    def get_cars_with_not_finished_ad(self) -> list:
        sql = "SELECT id FROM cars WHERE ad_date_finished is NULL"

        try:
            res = self.cur.execute(sql).fetchall()
            return [str(r[0]) for r in res]
        except:
            self.cur.close()

    def end_ad_of_car(self, cars_ids: list) -> None:
        sql = "UPDATE cars SET ad_date_finished = DateTime('now') WHERE id = ?"

        try:
            self.cur.executemany(sql, cars_ids)
            self.con.commit()

        except:
            self.cur.close()
