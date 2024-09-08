import datetime

from exceptions.LimitReachedError import LimitReachedError
from exceptions.NotEnoughCookiesError import NotEnoughCookiesError

ARP = 0.20
limit = 15000


def interest_amount():
    interest = ARP / 365
    interest *= limit
    return interest * 30


class Account:
    def __init__(self, cookies: int, loan: int, payment_date, due: int):
        self.cookies = cookies
        self.loan = loan
        self.due = due

        if payment_date is not None:
            self.payment_date = datetime.datetime.strptime(payment_date, '%Y-%m-%d %H:%M:%S.%f')
        else:
            self.payment_date = None

    def pay_due(self, amount: int):
        self.check_payment_date()
        if amount > self.cookies:
            raise NotEnoughCookiesError()
        self.due -= amount
        self.cookies -= amount
        if self.due < 0:
            self.due = 0

    def check_payment_date(self):
        if self.payment_date is not None:
            if datetime.datetime.now() > self.payment_date and self.due > 0:
                self.due += round(interest_amount())
                self.payment_date += datetime.timedelta(days=30)
            elif datetime.datetime.now() - self.payment_date >= datetime.timedelta(hours=20):
                self.loan = 0

    def make_loan(self, amount: int):
        try_loan = self.loan + amount
        if try_loan > limit:
            raise LimitReachedError()
        self.check_payment_date()
        self.cookies += amount
        self.loan += amount
        self.due += amount
        if self.payment_date is None:
            self.payment_date = datetime.datetime.now() + datetime.timedelta(days=30)
