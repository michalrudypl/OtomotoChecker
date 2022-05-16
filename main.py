import decimal
from database import Database
import requests
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import pydantic
import datetime


class Car(pydantic.BaseModel):
    id: str
    brand: str = None
    model: str = None
    milage: int = None
    production_year: datetime.date = None
    price: int = None
    from_who: str = None
    is_damaged: bool = False
    ad_date_created: datetime.date = None


def get_number_of_pages(link: str) -> int:
    while True:
        try:
            soup = BeautifulSoup(requests.get(link).text, "html.parser")

            pages_qty = [
                li.text
                for li in soup.find("ul", class_="pagination-list").find_all("li")
                if li["data-testid"] == "pagination-list-item"
            ]
            break
        except:
            time.sleep(1)

    return int(pages_qty[-1])


def get_cars_id(number_of_pages: int, link: str) -> list:
    links = [link + "&page=" + str(x) for x in range(1, number_of_pages + 1)]
    cars = []

    for link in tqdm(links, desc="Reading cars IDs from otomoto"):
        cars.append(get_cars_from_page(link))

    cars = sum(cars, [])
    return cars


def get_cars_from_page(link: str) -> list:
    cars = []
    while True:
        try:
            soup = BeautifulSoup(requests.get(link).text, "html.parser")
            for a in soup.main.find_all("article"):
                if a["data-testid"] == "listing-ad":
                    cars.append(a["id"])
            break
        except:
            time.sleep(1)

    return list(dict.fromkeys(cars))


def get_info_about_car(car_id: str) -> Car:
    link = "https://www.otomoto.pl/" + car_id
    r = requests.get(link)

    if r.ok:
        soup = BeautifulSoup(r.text, "html.parser")
        car = Car(id=car_id)

        car.price = int(
            decimal.Decimal(
                "".join(
                    soup.find("span", class_="offer-price__number").text.split()[0:-1]
                ).replace(",", ".")
            )
        )
        car.ad_date_created = get_date_from_span(
            soup.find("span", class_="offer-meta__value").text
        )

        soup_parameters = soup.find(id="parameters")
        for li in soup_parameters.find_all("li", class_="offer-params__item"):
            splited_li = li.text.split()
            if splited_li[0] == "Marka":
                car.brand = " ".join(splited_li[2::])
            if splited_li[0] == "Model":
                car.model = " ".join(splited_li[2::])
            if splited_li[0] == "Rok":
                car.production_year = datetime.date(
                    year=int(splited_li[-1]), month=1, day=1
                )
            if splited_li[0] == "Przebieg":
                car.milage = int("".join([x for x in splited_li[1:-1] if x != "km"]))
            if splited_li[0] == "Uszkodzony":
                car.is_damaged = True
            if splited_li[0] == "Oferta":
                car.from_who = " ".join(splited_li[2::])
        return car
    else:
        return False


def get_date_from_span(date: str) -> datetime.datetime:
    splited_date = date.split(",")
    polish_months = {
        "stycznia": 1,
        "lutego": 2,
        "marca": 3,
        "kwietnia": 4,
        "maja": 5,
        "czerwca": 6,
        "lipca": 7,
        "sierpnia": 8,
        "września": 9,
        "października": 10,
        "listopada": 11,
        "grudnia": 12,
    }
    day = splited_date[1].split()[0]
    month = polish_months[splited_date[1].split()[1]]
    year = splited_date[1].split()[2]

    return datetime.date(int(year), int(month), int(day))


def main():
    db = Database("test.db")

    # link_to_otomoto = "https://www.otomoto.pl/osobowe?search%5Bfilter_enum_country_origin%5D=usa&search%5Border%5D=created_at_first%3Adesc"
    link_to_otomoto = (
        "https://www.otomoto.pl/osobowe?search%5Bfilter_float_price%3Ato%5D=2000"
    )

    number_of_pages = get_number_of_pages(link_to_otomoto)
    cars_ids_from_otomoto = get_cars_id(number_of_pages, link_to_otomoto)

    for car_id in tqdm(cars_ids_from_otomoto, desc="Geeting info about car"):
        is_car_checked = db.checked_car_in_db(car_id)
        if is_car_checked == True:
            db.set_null_to_ad_date_finished(car_id)
        else:
            time.sleep(1)  # set time.sleep because otomoto blocks my IP
            car = get_info_about_car(car_id)
            if car == False:
                continue
            else:
                db.insert_car(car)

    cars_with_not_finished_ad = db.get_cars_with_not_finished_ad()
    cars_with_finished_ad = [
        x.split("#")  # this make me sublist from each ID
        for x in cars_with_not_finished_ad
        if x not in cars_ids_from_otomoto
    ]
    db.end_ad_of_car(cars_with_finished_ad)
    db.cur.close()


if __name__ == "__main__":
    main()
