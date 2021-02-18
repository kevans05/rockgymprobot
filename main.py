from datetime import datetime
from re import split
from dotenv import load_dotenv
from pyvirtualdisplay import Display
from selenium import webdriver

import os
import dataset
import discord
import threading

class DatabaseTools():
    def __init__(self, table_name):
        db = dataset.connect('sqlite:///databease.db')
        self.table = db[table_name]

    def add_items_to_database(self, list_of_scraps):
        self.table.insert_many(list_of_scraps)

    def add_item_to_database(self, item_scrap):
        self.table.insert(item_scrap)

    def return_item(self, item_dictionary):
        return self.table.find_one(start_of_session=item_dictionary['start_of_session'], order_by='-id')

class ScanRockgympro():
    def __init__(self,
                 url='https://app.rockgympro.com/b/widget/?a=offering&offering_guid=6216fbbc80424c31b9123b7d13ca22d7&widget_guid=4e2caadf21ed4455ba6f8b094b618f7f&random=5fd7eea6d8305&iframeid=&mode=p'):
        self.url = url
        self.calander_months = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6, "July": 7,
                                "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
        self.display = Display(visible=0, size=(1440, 2560))
        self.display.start()
        self.driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')

    def _return_avalability(self, string):
        availability_string = split("\s|[:. ]", string)[1]
        if availability_string.isnumeric():
            return int(availability_string)
        else:
            return 0

    def _return_meridiem(self, hour, meridiem):
        if meridiem == 'PM' and hour != 12:
            meridiem_modifier = 12
        else:
            meridiem_modifier = 0
        return meridiem_modifier

    def _return_datetimes(self, string_date):
        result = split("\s|[:.]", string_date)
        if result.index("to") == 5 and len(result) == 9:
            hour_alpha = int(result[3]) + self._return_meridiem(int(result[3]), result[4])
            minute_alpha = 0
            hour_bravo = int(result[6]) + self._return_meridiem(int(result[6]), result[8])
            minute_bravo = int(result[7])
        elif result.index("to") == 6 and len(result) == 9:
            hour_alpha = int(result[3]) + self._return_meridiem(int(result[3]), result[5])
            minute_alpha = int(result[4])
            hour_bravo = int(result[7]) + self._return_meridiem(int(result[7]), result[8])
            minute_bravo = 0
        elif result.index("to") == 6 and len(result) == 10:
            hour_alpha = int(result[3]) + self._return_meridiem(int(result[3]), result[5])
            minute_alpha = int(result[4])
            hour_bravo = int(result[7]) + self._return_meridiem(int(result[7]), result[9])
            minute_bravo = int(result[8])

        start_of_the_session = datetime(year=2020, month=self.calander_months[result[1]],
                                        day=int(result[2].replace(',', '')), hour=hour_alpha, minute=minute_alpha)
        end_of_the_session = datetime(year=2020, month=self.calander_months[result[1]],
                                      day=int(result[2].replace(',', '')), hour=hour_bravo, minute=minute_bravo)
        time_elapsed = end_of_the_session - start_of_the_session
        return start_of_the_session, end_of_the_session, time_elapsed

    def scan_sites(self):
        self.driver.get(self.url)
        temp_list = []
        for current_datepickers_targets in ["datepicker-available-day", "datepicker-soldout-day"]:
            for days in range(len(self.driver.find_elements_by_class_name(current_datepickers_targets))):
                self.driver.find_elements_by_class_name(current_datepickers_targets)[days].click()
                schedule_table = self.driver.find_elements_by_id("containing-div-for-event-table")
                for row in schedule_table:
                    temp_dic = {'scrape_time': datetime.now(), 'start_of_session': None, 'number_of_spots': None,
                                'end_of_session': None, 'not_available_yet': None}
                    for idx, column in enumerate(row.find_elements_by_css_selector("td")):
                        if idx % 4 == 0:
                            temp_dic.update({'start_of_session': self._return_datetimes(column.text)[0],
                                             'end_of_session': self._return_datetimes(column.text)[1]})
                        elif idx % 4 == 1:
                            temp_dic.update({'number_of_spots': self._return_avalability(column.text)})
                        elif idx % 4 == 3:
                            if column.text == 'NOT AVAILABLE YET':
                                temp_dic.update({'not_available_yet': True})
                            else:
                                temp_dic.update({'not_available_yet': False})
                        temp_list.append(temp_dic)
        self.driver.close()
        self.display.stop()
        return temp_list

class TestThread(threading.Thread):
    def __init__(self, name='TestThread'):
        """ constructor, setting initial variables """
        self._stopevent = threading.Event(  )
        self._sleepperiod = 1.0

        threading.Thread.__init__(self, name=name)

    def run(self):
        """ main control loop """
        print ("%s starts" % (self.getName(  ),))

        count = 0
        while not self._stopevent.isSet(  ):
            count += 1
            print ("loop %d" % (count,))
            self._stopevent.wait(self._sleepperiod)

        print ("%s ends" % (self.getName(  ),))

    def join(self, timeout=None):
        """ Stop the thread. """
        self._stopevent.set(  )
        threading.Thread.join(self, timeout)

class DiscordBot(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        self.weekDays = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")

    async def on_message(self, message):

        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        if message.content.startswith('$add'):
            input_string = split(" ", message.content)
            if len(input_string) != 2:
                await message.channel.send('format is $add [URL]')
            else:
                try:
                    #channel = ScanRockgympro(input_string[1])
                    x = 'This Bot will alert the channel ' + message.channel.name + ' any time a new spot opens up on '  + input_string[1] + ' \r\r\r To stop it type $stop [URL]'
                    await message.channel.send(x)

                except:
                    await message.channel.send("Something went wrong, check to make sure the URL was correct. "
                                       "If it persists contact the Bot Designer.")
        elif message.content.startswith('$stop'):

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()
client = DiscordBot()
client.run(TOKEN)
