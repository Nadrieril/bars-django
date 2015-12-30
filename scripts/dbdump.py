#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file has been automatically generated.
# Instead of changing it, create a file called import_helper.py
# and put there a class called ImportHelper(object) in it.
#
# This class will be specially casted so that instead of extending object,
# it will actually extend the class BasicImportHelper()
#
# That means you just have to overload the methods you want to
# change, leaving the other ones inteact.
#
# Something that you might want to do is use transactions, for example.
#
# Also, don't forget to add the necessary Django imports.
#
# This file was generated with the following command:
# manage.py dumpscript bars_api
#
# to restore it, run
# manage.py runscript module_name.this_script_name
#
# example: if manage.py is at ./manage.py
# and the script is at ./some_folder/some_script.py
# you must make sure ./some_folder/__init__.py exists
# and run  ./manage.py runscript some_folder.some_script

import sys
import os

class BasicImportHelper(object):

    def pre_import(self):
        pass

    # You probably want to uncomment on of these two lines
    # @transaction.atomic  # Django 1.6
    # @transaction.commit_on_success  # Django <1.6
    def run_import(self, import_data):
        import_data()

    def post_import(self):
        pass

    def locate_similar(self, current_object, search_data):
        # You will probably want to call this method from save_or_locate()
        # Example:
        #   new_obj = self.locate_similar(the_obj, {"national_id": the_obj.national_id } )

        the_obj = current_object.__class__.objects.get(**search_data)
        return the_obj

    def locate_object(self, original_class, original_pk_name, the_class, pk_name, pk_value, obj_content):
        # You may change this function to do specific lookup for specific objects
        #
        # original_class class of the django orm's object that needs to be located
        # original_pk_name the primary key of original_class
        # the_class      parent class of original_class which contains obj_content
        # pk_name        the primary key of original_class
        # pk_value       value of the primary_key
        # obj_content    content of the object which was not exported.
        #
        # You should use obj_content to locate the object on the target db
        #
        # An example where original_class and the_class are different is
        # when original_class is Farmer and the_class is Person. The table
        # may refer to a Farmer but you will actually need to locate Person
        # in order to instantiate that Farmer
        #
        # Example:
        #   if the_class == SurveyResultFormat or the_class == SurveyType or the_class == SurveyState:
        #       pk_name="name"
        #       pk_value=obj_content[pk_name]
        #   if the_class == StaffGroup:
        #       pk_value=8

        search_data = {pk_name: pk_value}
        the_obj = the_class.objects.get(**search_data)
        # print(the_obj)
        return the_obj


    def save_or_locate(self, the_obj):
        # Change this if you want to locate the object in the database
        try:
            the_obj.save()
        except:
            print("---------------")
            print("Error saving the following object:")
            print(the_obj.__class__)
            print(" ")
            print(the_obj.__dict__)
            print(" ")
            print(the_obj)
            print(" ")
            print("---------------")

            raise
        return the_obj


importer = None
try:
    import import_helper
    # We need this so ImportHelper can extend BasicImportHelper, although import_helper.py
    # has no knowlodge of this class
    importer = type("DynamicImportHelper", (import_helper.ImportHelper, BasicImportHelper), {})()
except ImportError as e:
    if str(e) == "No module named import_helper":
        importer = BasicImportHelper()
    else:
        raise

try:
    import dateutil.parser
except ImportError:
    print("Please install python-dateutil")
    sys.exit(os.EX_USAGE)

def run():
    importer.pre_import()
    importer.run_import(import_data)
    importer.post_import()

def import_data():
    # Processing model: Bar

    from bars_core.models.bar import Bar

    bar_1 = Bar()
    bar_1.id = u'avironjone'
    bar_1.name = u'Aviron J\xf4ne'
    bar_1 = importer.save_or_locate(bar_1)

    bar_2 = Bar()
    bar_2.id = u'escrimejone'
    bar_2.name = u'Escrime J\xf4ne'
    bar_2 = importer.save_or_locate(bar_2)

    bar_3 = Bar()
    bar_3.id = u'natationjone'
    bar_3.name = u'Natation J\xf4ne'
    bar_3 = importer.save_or_locate(bar_3)

    # Processing model: User

    from bars_core.models.user import User

    User.objects.create_superuser('admin', 'admin')
    admin=User.objects.get(username="admin")
    admin.pseudo=u'admin'
    admin = importer.save_or_locate(admin)


    user_1 = User()
    user_1.username = u'nadri'
    user_1.set_password('nadri')
    user_1.firstname = u'Guillaume'
    user_1.lastname = u'Boisseau'
    user_1.pseudo = u'Nadri'
    user_1 = importer.save_or_locate(user_1)

    user_2 = User()
    user_2.username = u'ntag'
    user_2.set_password('ntag')
    user_2.firstname = u'Basile'
    user_2.lastname = u'Bruneau'
    user_2.pseudo = u'NTag'
    user_2 = importer.save_or_locate(user_2)

    user_3 = User()
    user_3.username = u'tizot'
    user_3.set_password('tizot')
    user_3.firstname = u'Camille'
    user_3.lastname = u'Masset'
    user_3.pseudo = u'Tizot'
    user_3 = importer.save_or_locate(user_3)

    user_4 = User()
    user_4.username = u'denis'
    user_4.set_password('denis')
    user_4.firstname = u'Denis M'
    user_4.lastname = u'M\xe9rigoux'
    user_4.pseudo = u''
    user_4 = importer.save_or_locate(user_4)


    # Processing model: Account

    from bars_core.models.account import Account

    account_1 = Account()
    account_1.bar = bar_1
    account_1.owner = user_1
    account_1 = importer.save_or_locate(account_1)

    account_2 = Account()
    account_2.bar = bar_1
    account_2.owner = user_2
    account_2 = importer.save_or_locate(account_2)

    account_3 = Account()
    account_3.bar = bar_1
    account_3.owner = user_3
    account_3 = importer.save_or_locate(account_3)

    account_4 = Account()
    account_4.bar = bar_1
    account_4.owner = user_4
    account_4 = importer.save_or_locate(account_4)

    account_5 = Account()
    account_5.bar = bar_3
    account_5.owner = user_2
    account_5 = importer.save_or_locate(account_5)

    account_6 = Account()
    account_6.bar = bar_2
    account_6.owner = user_4
    account_6 = importer.save_or_locate(account_6)

    account_7 = Account()
    account_7.bar = bar_1
    account_7.owner = admin
    account_7 = importer.save_or_locate(account_7)


    # Processing model: SellItem

    from bars_items.models.sellitem import SellItem

    sellitem_1 = SellItem()
    sellitem_1.bar = bar_1
    sellitem_1.name = "Chocolat"
    sellitem_1.unit_name = u'carre'
    sellitem_1.unit_name_plural = u'carres'
    sellitem_1.tax = 0.2
    sellitem_1 = importer.save_or_locate(sellitem_1)

    sellitem_2 = SellItem()
    sellitem_2.bar = bar_1
    sellitem_2.name = "Pizza"
    sellitem_2 = importer.save_or_locate(sellitem_2)

    # Processing model: ItemDetails

    from bars_items.models.itemdetails import ItemDetails

    itemdetails_1 = ItemDetails()
    itemdetails_1.name = u'Chocolat'
    itemdetails_1.unit_name = u'tablette'
    itemdetails_1.unit_name_plural = u'tablettes'
    itemdetails_1 = importer.save_or_locate(itemdetails_1)

    itemdetails_2 = ItemDetails()
    itemdetails_2.name = u'Pizza'
    itemdetails_2.unit_name = u''
    itemdetails_2.unit_name_plural = u''
    itemdetails_2 = importer.save_or_locate(itemdetails_2)

    # Processing model: BuyItem

    from bars_items.models.buyitem import BuyItem

    buyitem_1 = BuyItem()
    buyitem_1.details = itemdetails_1
    buyitem_1 = importer.save_or_locate(buyitem_1)

    buyitem_2 = BuyItem()
    buyitem_2.details = itemdetails_2
    buyitem_2 = importer.save_or_locate(buyitem_2)

    # Processing model: StockItem

    from bars_items.models.stockitem import StockItem

    stockitem_1 = StockItem()
    stockitem_1.bar = bar_1
    stockitem_1.sellitem = sellitem_1
    stockitem_1.details = itemdetails_1
    stockitem_1.price = 1
    stockitem_1 = importer.save_or_locate(stockitem_1)

    stockitem_2 = StockItem()
    stockitem_2.bar = bar_1
    stockitem_2.sellitem = sellitem_2
    stockitem_2.details = itemdetails_2
    stockitem_2.price = 2
    stockitem_2 = importer.save_or_locate(stockitem_2)

    # Processing model: News

    from bars_news.models import News

    news_1 = News()
    news_1.bar = bar_1
    news_1.author = user_3
    news_1.name = u"C'est du propre !"
    news_1.text = u"Bar d'\xe9tage d\xe9guelasse !! Faites votre vaisselle bande de p**** !"
    news_1.timestamp = dateutil.parser.parse("2015-01-30T02:37:14+00:00")
    news_1 = importer.save_or_locate(news_1)

    news_2 = News()
    news_2.bar = bar_1
    news_2.author = user_3
    news_2.name = u'Merci pour les photos'
    news_2.text = u"Bravo \xe0 Yoann qui a pris le temps de mettre toutes les photos sur les murs du bar d'\xe9tage !"
    news_2.timestamp = dateutil.parser.parse("2015-01-30T02:37:14+00:00")
    news_2 = importer.save_or_locate(news_2)

    # Processing model: Transaction

    from bars_transactions.models import Transaction
    from bars_transactions.models import AccountOperation
    from bars_transactions.models import ItemOperation

    for i in range(20):
        t = Transaction()
        t.bar = bar_1
        t.author = user_2
        t.type = u'buy'
        t = importer.save_or_locate(t)

        ao = AccountOperation()
        ao.transaction = t
        ao.fixed = False
        ao.delta = -2
        ao.target = account_2
        ao = importer.save_or_locate(ao)

        io = ItemOperation()
        io.transaction = t
        io.delta = -1.0
        io.target = stockitem_1
        io = importer.save_or_locate(io)
