from balethon import Client
from balethon.conditions import private, group, equals, is_joined, regex, at_state, contact, successful_payment, document, reply
from balethon.objects import ReplyKeyboard, InlineKeyboard, ReplyKeyboardButton, LabeledPrice, Message, CallbackQuery, PreCheckoutQuery
from balethon.errors import ForbiddenError, NotFoundError
import json
import random
import requests
from httpx import AsyncClient, get, post
import time
import re
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

bot = Client(TOKEN)

main_key = ReplyKeyboard(['ثبت محصول جدید➕', 'حذف محصول➖'], ['لیست محصولات من📃'], [
                         'جستجوی محصول 🧺'], ['حساب کاربری🔍'], ['قوانین و مقررات ⚖', 'پشتیبانی👮‍♂️'])
admin_key = ReplyKeyboard(['ثبت محصول جدید➕', 'حذف محصول➖'], ['لیست محصولات من📃'], [
                          'جستجوی محصول 🧺'], ['حساب کاربری🔍', 'پنل مدیریت👨‍💼'], ['قوانین و مقررات ⚖'])
action_key = ReplyKeyboard(['بازگشت🔙'])

products = {}
payments = {}
userid = {}
messages = {}

data_file = "data.json"
admin = ADMIN_ID
category = {
    'واسطه گری فایل': 'sendDoc',
    'واسطه گری اکانت': 'between',
    'وب سرویس': 'api'
}


def save_product(userid, product_id):
    products[str(userid)] = str(product_id)


def find_product(userid):
    return products[str(userid)]


def find_byname(name):
    with open(data_file, 'r') as file:
        data = json.load(file)
    results = []
    for i in data['products']:
        if data['products'][i]['name'] == name:
            results.append(i)
    return results


def unique(data):
    id = random.randint(1000, 10000)
    prods = data['products'].keys()
    while id in prods:
        id = random.randint(1000, 10000)
    return id


@bot.on_message(~is_joined(5802996341) & private & ~successful_payment)
async def not_joined(*, client, message):
    await message.reply("برای استفاده از ربات باید وارد کانال های زیر شوید 👇\n بعد از جوین شدن، ربات را دوباره [استارت](send:/start) کنید", InlineKeyboard([('کانال توسعه دهنده', 'SACChannel', 'https://ble.ir/sacgroup')]))


@bot.on_command(private)
async def testapi(id=-1, *, client, message):
    with open(data_file, 'r') as file:
        data = json.load(file)
    chatid = message.chat.id
    if id == -1:
        await message.reply("کد داده نشده")
    else:
        password = data['products'][id]['password']
        apiurl = data['products'][id]['host']
        apiparams = {'password': password}
        r = requests.get(url=apiurl, params=apiparams)
        res = r.json()
        if res['ok']:
            token = res['token']
            await client.send_message(chatid, f'خرید شما با موفقیت دریافت شد ✅\n\n توکن شما با موفقیت ساخته شد :\n {token}')
        else:
            await client.send_message(chatid, f'عملیات ساخت توکن ناموفق بود❌\n\n هرچه زودتر با پشتیبانی ربات تماس بگیرید')
        await message.reply(f"{res}")


@bot.on_command(private)
async def product_info(id=0, *, client, message):
    if id == 0:
        await message.reply("لطفا لینک را به درستی ارسال کنید")
    else:
        with open(data_file, 'r') as file:
            data = json.load(file)
        name = data['products'][id]['name']
        description = data['products'][id]['description']
        price = data['products'][id]['price']
        author = data['products'][id]['author']
        if data['products'][id]['mode'] == 'between':
            mode = 'واسطه‌گری (اکانت در ربات ثبت شده)'
        elif data['products'][id]['mode'] == 'sendDoc':
            mode = 'ارسال فایل (پس از خرید، فایل ذخیره شده ارسال خواهد شد)'
        elif data['products'][id]['mode'] == 'api':
            mode = 'وب سرویس : بعد از خرید، توکن دسترسی به شما داده میشود'
        user = await client.get_chat(int(author))
        await message.reply(f"نام محصول : {name} \n توضیحات : \n {description}\n قیمت : {price} ریال \n\n نوع محصول : {mode} \n\nفروشنده : {user}", InlineKeyboard([('خرید 🛒', f"buy:{id}")]))


@bot.on_callback_query(private & regex("^buy:"))
async def buy_product(callback_query):
    with open(data_file, 'r') as file:
        data = json.load(file)
        id = str(callback_query.data.split(':')[1])
    name = data['products'][id]['name']
    description = data['products'][id]['description']
    price = data['products'][id]['price']
    author = data['products'][id]['author']
    card = data['card'][str(author)]
    if len(card) == 16 and card.isnumeric():
        with AsyncClient() as _cli:
            res = _cli.get("https://aladdin4api.pythonanywhere.com/card", params={
                           'token': 'aladdin4api token (token can be bought from @CodeWizaard)', 'card': card})
            if res.status_code == 200:
                cardr = res.json()
                if cardr['result']['isValid']:
                    card = card
    else:
        card = "6219861956842362"
    await bot.send_message(author, "فردی در حال خرید از شما است...")
    userid[str(id)] = str(callback_query.author.id)
    await bot.send_invoice(
        chat_id=callback_query.author.id,
        title=name,
        description=description,
        payload=str(id),
        provider_token=str(card),
        prices=[LabeledPrice(label=f"{name}", amount=int(price))]
    )
    payments[str(callback_query.author.id)] = str(id)


@bot.on_pre_checkout_query(private)
async def verify_wallet_payment(checkout: PreCheckoutQuery):
    await bot.execute("post", "answerPreCheckoutQuery", pre_checkout_query_id=checkout.id, ok=True)


@bot.on_callback_query(private & regex("^wallet:"))
async def buy_with_wallet(callback_query: CallbackQuery):
    with open(data_file, 'r') as file:
        data = json.load(file)
        id = str(callback_query.data.split(':')[1])
    name = data['products'][id]['name']
    description = data['products'][id]['description']
    price = data['products'][id]['price']
    author = data['products'][id]['author']
    wallet = data['wallet'][str(author)]
    if wallet:
        await bot.send_message(author, "فردی درحال خرید از شما با کیف پول است...")
        userid[str(id)] = str(callback_query.author.id)
        await bot.send_invoice(
            chat_id=callback_query.author.id,
            title=name,
            description=description,
            payload=f"wallet:{id}",
            provider_token=str(wallet),
            prices=[LabeledPrice(label=f"{name}", amount=int(price))]
        )
        payments[str(callback_query.author.id)] = str(id)
    else:
        await callback_query.answer("فروشنده این محصول کیف پول خود را ثبت نکرده")


@bot.on_message(successful_payment)
async def show_payment(*, client, message):
    id = message.successful_payment.invoice_payload
    with open(data_file, 'r') as file:
        data = json.load(file)
    author = data['products'][id]['author']
    chatid = userid[str(id)]
    user = await client.get_chat(author)
    customer = await client.get_chat(chatid)
    if re.search("^wallet:", id):
        await bot.send_message(author, 'خریدی از مبلغ دریافتی شما به کیف پولتان اضافه شده است')
    else:
        file = open(data_file, 'w')
        data['payments'][str(chatid)] = {}
        data['payments'][str(chatid)]['product'] = id
        data['payments'][str(
            chatid)]['price'] = message.successful_payment.total_amount
        data['payments'][str(chatid)]['user'] = str(chatid)
        data['payments'][str(chatid)]['author'] = str(author)
        json.dump(data, file, indent=4)
        file.close()
    if data['products'][id]['mode'] == 'between':
        await client.send_message(chatid, f"خرید شما با موفقیت دریافت شد ✅\n\n نام کاربری : {data['products'][id]['username']}\n\n رمز عبور : {data['products'][id]['password']}")
    elif data['products'][id]['mode'] == 'sendDoc':
        await client.send_document(chatid, data['products'][id]['fileId'], 'خرید شما با موفقیت انجام شد ✅\n فایل ثبت شده در محصول')
    elif data['products'][id]['mode'] == 'api':
        password = data['products'][id]['password']
        apiurl = data['products'][id]['host']
        apiparams = {'password': password}
        r = requests.get(url=apiurl, params=apiparams)
        res = r.json()
        if res['ok']:
            token = res['token']
            await client.send_message(chatid, f'خرید شما با موفقیت دریافت شد ✅\n\n توکن شما با موفقیت ساخته شد :\n {token}')
        else:
            await client.send_message(chatid, f'عملیات ساخت توکن ناموفق بود❌\n\n هرچه زودتر با پشتیبانی ربات تماس بگیرید')
    else:
        await client.send_message(chatid, f'خرید شما دریافت شد!\n میتوانید با خیال راحت برای ادامه ی فرایند خرید با فروشنده در ارتباط باشید')
    await client.send_message(chatid, f"مبلغ خرید شما، مستقیما به حساب ثبت شده توسط فروشنده واریز شده، و پشتیبانی هیچ مسئولیتی راجع به آن قبول نمیکند\n\n اگر مشکل فنی ای در کاربری ربات حین پرداخت ایجاد شده، از طریق پشتیبانی به ما اطلاع دهید\n در غیر این صورت بقیه مشکل ها را با فروشنده در میان بگذارید : {user}\n برای گزارش این محصول لطفا با پشتیبانی در ارتباط باشید")
    await client.send_message(author, f"{customer} از شما خرید کرد 🛍\n محصول خریداری شده {data['products'][id]['name']} \n\n منم کاری که باید انجام میدادمو انجام دادم\n بازار باشه😉")


@bot.on_message(private & equals('پشتیبانی👮‍♂️'))
async def send_support(*, client, message):
    await message.reply("سلام، پشتیبانی کاسب هستم 👋\n مشکلی که داری رو در قالب یک پیام کامل ارسال کن تا به تیم منتقل کنم", InlineKeyboard([('بازگشت 🔙', 'Back')]))
    message.author.set_state("SUPPORT")


@bot.on_callback_query(at_state("SUPPORT"))
async def going_back_from_support(callback_query):
    if callback_query.data == 'Back':
        await callback_query.answer("به صفحه اصلی بازگشتید... 🚁", main_key)
        callback_query.author.del_state()
    else:
        pass


@bot.on_message(private & at_state("SUPPORT"))
async def send_to_support(*, client, message):
    support = await message.reply("در حال انتقال به تیم پشتیبانی...")
    try:
        await bot.send_message(admin, f'پشتیبانی از :{message.chat.id}\n\n {message.chat.first_name} : {message.text}', InlineKeyboard([('مسدود کردن کاربر', f'bant:{message.chat.id}')]))
    except:
        await bot.edit_message_text(message.chat.id, support.id, 'ارسال پیام ناموفق بود!', main_key)
    else:
        await bot.edit_message_text(message.chat.id, support.id, 'پیام ارسال شد!', main_key)
    finally:
        message.author.del_state()


@bot.on_message(reply)
async def check_and_send_support(*, client, message):
    userId = "0"
    lines = message.reply_to_message.text.splitlines()
    if re.search("^پشتیبانی از", lines[0]):
        userId = lines[0].split(":")[1]
        await bot.send_message(userId, f'پیام دریافت شده از پشتیبانی :\n\n {message.text}')
    else:
        pass


@bot.on_command(private)
async def start(referrer=0, *, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
        keys = userList['users'].keys()
        userid = message.chat.id
        strid = str(userid)
    if str(userid) not in keys:
        file = open(data_file, 'w')
        userList['users'][message.chat.id] = 'Basic'
        userList['phone'][message.chat.id] = ""
        userList['card'][message.chat.id] = ""
        userList['wallet'][message.chat.id] = ""
        json.dump(userList, file, indent=4)
        file.close()
        if referrer != 0:
            inviter = referrer
            if int(inviter) != int(message.chat.id):
                with open(data_file, 'r') as file:
                    userList = json.load(file)
                    invites = userList['invites'][str(inviter)]
                    coins = userList['users'][str(inviter)]
                file = open(data_file, 'w')
                userList['invites'][str(inviter)] = str(int(invites)+1)
                userList['users'][str(inviter)] = str(int(coins)+3)
                json.dump(userList, file, indent=4)
                file.close()
                invited = await client.get_chat(message.chat.id)
                await bot.send_message(referrer, f"{invited} توسط شما به ربات پیوست")
                referrer = await client.get_chat(referrer)
                await message.reply(f"شما توسط {referrer} به ربات دعوت شدید!")
            else:
                await message.reply("رفیق من\n خودت که به خودت دعوت نمیتونی بدی\n")
    if userList['users'][str(message.chat.id)] != 'Admin':
        await message.reply("سلام👋\n به ربات فروشنده ی *کاسب* خوش اومدید 💎\n اگر محصولی داری و دنبال پلتفرم برای پخش کردنشی، من در خدمتم\n قبل از استفاده از ربات پروفایل خود را از طریق بخش [پروفایل](send:حساب کاربری🔍) کامل کنید\n\n استفاده ی شما از این ربات نشانه ی موافقت شما با قوانین ربات است", main_key)
    else:
        await message.reply("سلام🕵️‍♀️\n من شمارو میشناسم؟\n اها، شما ادمین هستید❕\n بفرمایید، در خدمتم", admin_key)


@bot.on_message(private & equals('پیام همگانی'))
async def all_anonce(*, client, message):
    if message.chat.id == admin:
        await message.reply("پیام مورد نظر خود را ارسال کنید", action_key)
        message.author.set_state("ALLMESSAGE")
    else:
        await message.reply("شما دسترسی به این دستور ندارید")


@bot.on_message(private & at_state("ALLMESSAGE"))
async def send_all(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
        users = userList['users'].keys()
    send = 0
    err = 0
    nFound = 0
    noInf = 0
    if message.text != 'بازگشت🔙':
        for i in users:
            try:
                await client.send_message(i, message.text)
                time.sleep(2)
                send += 1
            except ForbiddenError:
                err += 1
            except NotFoundError:
                nFound += 1
            except:
                noInf += 1
        await message.reply(f"تعداد پیام های ارسال شده : {send}\n تعداد پیام های بلاک شده : {err}\n تعداد کاربر های یافت نشده : {nFound}\n تعداد پیام های ارسال نشده بدون اطلاعات : {noInf}", main_key)
        message.author.del_state()
    else:
        await message.reply("برگشتیم", main_key)
        message.author.del_state()


@bot.on_message(equals('پیام به کاربر'))
async def send_to_user_message(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    if userList['users'][str(message.chat.id)] == 'Admin':
        await message.reply("لطفا آیدی کاربر مورد نظر را ارسال کنید")
        message.author.set_state("GETUSERID")
    else:
        await message.reply('شما دسترسی به این دستور ندارید\n با تشکر')


@bot.on_message(at_state("GETUSERID"))
async def save_user_id(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    if message.text in userList['users'].keys():
        messages[str(message.chat.id)] = message.text
        await message.reply("پیامی که میخواهید به این کاربر ارسال شود را بفرستید")
        message.author.set_state("GETMESSAGEUSER")
    else:
        await message.reply("این کاربر در ربات وجود ندارد")


@bot.on_message(at_state("GETMESSAGEUSER"))
async def send_message_to_user(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    msg = await client.send_message(message.chat.id, "در حال ارسال پیام...")
    chat_id = messages[str(message.chat.id)]
    message_text = message.text
    await client.send_message(chat_id, message_text)
    await client.edit_message_text(msg.chat.id, msg.id, 'پیام با موفقیت ارسال شد!')
    message.author.del_state()


@bot.on_message(equals('جستجوی محصول 🧺'))
async def search_product(*, client: Client, message: Message):
    await message.reply("در چه دسته بندی به دنبال محصول میگردید؟", ReplyKeyboard(['واسطه گری فایل'], ['واسطه گری اکانت'], ['وب سرویس']))
    message.author.set_state("SEARCHFILTER")


@bot.on_message(at_state("SEARCHFILTER"))
async def filter_search(*, client: Client, message: Message):
    with open(data_file, 'r') as file:
        data = json.load(file)
    reply = ReplyKeyboard()
    if message.text in category.keys():
        cat = category[str(message.text)]
        for i in data['products'].keys():
            if data['products'][i]['mode'] == cat:
                reply.add_row(data['products'][i]['name'])
        reply.add_row('بازگشت🔙')
        await message.reply("محصولات یافت شده بر اساس خواسته های شما", reply)
        message.author.set_state("SEARCHPRO")
    else:
        await message.reply("لطفا از دسته بندی های خود ربات استفاده کنید")


@bot.on_message(private & at_state("SEARCHPRO") & equals('بازگشت🔙'))
async def back(*, client, message):
    await message.reply("بازگشت به صفحه اصلی... ✈", main_key)
    message.author.del_state()


@bot.on_message(at_state("SEARCHPRO"))
async def search_product_view(*, client: Client, message: Message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    res = find_byname(message.text)
    id = res[0]
    name = userList['products'][id]['name']
    description = userList['products'][id]["description"]
    price = userList['products'][id]['price']
    link = client.create_referral_link("product_info", id)
    author = userList['products'][id]['author']
    if userList['products'][id]['mode'] == 'between':
        mode = 'واسطه‌گری (اکانت در ربات ثبت شده)'
    elif userList['products'][id]['mode'] == 'sendDoc':
        mode = 'ارسال فایل (پس از خرید، فایل ذخیره شده ارسال خواهد شد)'
    elif userList['products'][id]['mode'] == 'api':
        mode = "وب سرویس : بعد از خرید، توکن دسترسی به شما داده میشود"
    await message.reply(f"اطلاعات محصول شما : \n\n نام محصول : {name}\n\n توضیحات : {description} \n\n قیمت محصول : {price} ریال\n\n شناسه فروشنده : {await client.get_chat(author)} \n\n نوع محصول : {mode} \n\nلینک اشتراک گذاری : {link}", InlineKeyboard([('گزارش محصول', f'report:{id}')]))
    await message.reply("در نظر داشته باشید که اگر بیهوده درخواست بازبینی محصولی را بدهید، حساب شما در ربات مسدود خواهد شد", main_key)
    message.author.del_state()


@bot.on_callback_query(regex("^report:"))
async def submit_report_request(callback_query: CallbackQuery):
    with open(data_file, 'r') as file:
        data = json.load(file)
    id = callback_query.data.split(':')[1]
    name = data['products'][id]['name']
    description = data['products'][id]["description"]
    price = data['products'][id]['price']
    link = bot.create_referral_link("product_info", id)
    author = data['products'][id]['author']
    await bot.send_message(admin, f'''درخواست بازبینی محصول توسط کاربر
    نام محصول : {name}
    توضیحات محصول : {description}
    قیمت : {price} ریال
    شناسه فروشنده : {author}
    مشاهده : {link}
''', InlineKeyboard([('مسدود کردن فروشنده', f'ban:{author}')]))
    await callback_query.answer("با تشکر از همکاری شما 🫂\n درخواست بازبینی محصول با موفقیت به ادمین های ربات ارسال شد")


@bot.on_callback_query(private & regex('^ban:'))
async def ban_from_inline(callback_query: CallbackQuery):
    with open(data_file, 'r') as file:
        data = json.load(file)
    seller = callback_query.data.split(':')[1]
    data['users'][str(seller)] = 'Banned'
    file = open(data_file, 'w')
    json.dump(data, file, indent=4)
    file.close()
    await callback_query.answer("کاربر مورد نظر با موفقیت مسدود شد")
    await bot.send_message(seller, '''با عرض پوزش 👛
    ناچار به این هستیم که اعلام کنیم شما به علت رعایت نکردن قوانین ربات،
    از ربات مسدود شدید''')


@bot.on_message(private & equals('لیست محصولات من📃'))
async def prod_list(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    string = ""
    reply = ReplyKeyboard()
    for i in userList['products'].keys():
        if userList['products'][i]['author'] == str(message.chat.id):
            string += f"{userList['products'][i]['author']}"
            reply.add_row(f"{userList['products'][i]['name']}")
    reply.add_row('بازگشت🔙')
    await message.reply("لیست محصولات شما : ", reply)
    message.author.set_state("LIST")


@bot.on_message(private & at_state("LIST") & equals('بازگشت🔙'))
async def back(*, client, message):
    await message.reply("بازگشت به صفحه اصلی... ✈", main_key)
    message.author.del_state()


@bot.on_message(private & at_state("LIST"))
async def prod_info(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    res = find_byname(message.text)
    id = res[0]
    name = userList['products'][id]['name']
    description = userList['products'][id]["description"]
    price = userList['products'][id]['price']
    link = client.create_referral_link("product_info", id)
    author = userList['products'][id]['author']
    if userList['products'][id]['mode'] == 'between':
        mode = 'واسطه‌گری (اکانت در ربات ثبت شده)'
    elif userList['products'][id]['mode'] == 'sendDoc':
        mode = 'ارسال فایل (پس از خرید، فایل ذخیره شده ارسال خواهد شد)'
    elif userList['products'][id]['mode'] == 'api':
        mode = "وب سرویس : بعد از خرید، توکن دسترسی به شما داده میشود"
    await message.reply(f"اطلاعات محصول شما : \n\n نام محصول : {name}\n\n توضیحات : {description} \n\n قیمت محصول : {price} ریال\n\n شناسه فروشنده : {author} \n\n نوع محصول : {mode} \n\nلینک اشتراک گذاری : {link}", main_key)
    message.author.del_state()


@bot.on_message(private & equals('پنل مدیریت👨‍💼'))
async def panel(*, client, message):
    if int(message.chat.id) == admin:
        await message.reply("به پنل مدیریت خوش اومدید 👮‍♂️", ReplyKeyboard(['دیدن محصولات ثبت شده'], ['مسدود کردن کاربر', 'باز کردن حساب'], ['دیدن اطلاعات کاربر'], ['پیام همگانی', 'پیام به کاربر'], ['بازگشت🔙']))
    else:
        await message.reply("شما دسترسی به این دستور ندارید")


@bot.on_message(private & equals('بازگشت🔙'))
async def back_main(*, client, message):
    await message.reply("بازگشت به صفحه اصلی... ✈", main_key)
    message.author.del_state()


@bot.on_message(private & equals('مسدود کردن کاربر'))
async def ban_bot_user(*, client: Client, message: Message):
    with open(data_file, 'r') as file:
        data = json.load(file)
    if data['users'][str(message.author.id)] == 'Admin':
        pass
    else:
        await message.reply("شما به این دستور دسترسی ندارید\n فضولی موقوف")


@bot.on_message(private & equals('دیدن محصولات ثبت شده'))
async def admin_list(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    reply = ReplyKeyboard()
    for i in userList['products']:
        reply.add_row(f"{userList['products'][i]['name']}")
    reply.add_row('بازگشت🔙')
    await message.reply("لیست محصولات ثبت شده : ", reply)
    message.author.set_state("ADMINLIST")


@bot.on_message(at_state("ADMINLIST"))
async def admin_product(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    res = find_byname(message.text)
    id = res[0]
    name = userList['products'][id]['name']
    description = userList['products'][id]["description"]
    price = userList['products'][id]['price']
    link = client.create_referral_link("product_info", id)
    author = userList['products'][id]['author']
    await message.reply(f"اطلاعات محصول شما : \n\n نام محصول : {name}\n\n توضیحات : {description} \n\n قیمت محصول : {price} ریال\n\n شناسه فروشنده : {author} \n\n لینک اشتراک گذاری : {link}", InlineKeyboard([('حذف محصول', f'del:{id}'), ('دیدن جزئیات', f'see:{id}')], [('مسدود کردن کاربر', f'block:{author}')]))
    message.author.set_state("ADMININFO")


@bot.on_callback_query(at_state("ADMININFO") & regex("^see:"))
async def see_saves_in_product_admin(callback_query):
    with open(data_file, 'r') as file:
        data = json.load(file)
    id = callback_query.data.split(":")[1]
    try:
        mode = data['products'][str(id)]['mode']
        if mode == 'sendDoc':
            await bot.send_document(callback_query.author.id, data['products'][str(id)]['fileId'], 'فایل ذخیره شده در محصول')
        elif mode == 'between':
            user = data['products'][str(id)]['username']
            passs = data['products'][str(id)]['password']
            await callback_query.answer(f'نام کاربری و رمز عبور ذخیره شده\n نام کاربری : {user}\n رمز عبور : {passs}')
        else:
            await callback_query.answer("حالت محصول یافت نشد")
    except:
        await callback_query.answer("حالت محصول پیدا نشد")


@bot.on_callback_query(at_state("ADMININFO") & regex("^del:"))
async def delete_admin(callback_query):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    id = int(callback_query.data.split(":")[1])
    author = userList['products'][str(id)]['author']
    name = userList['products'][str(id)]['name']
    del userList['products'][str(id)]
    with open(data_file, 'w') as file:
        json.dump(userList, file, indent=4)
    await callback_query.answer("محصول با موفقیت حذف شد", main_key)
    await bot.send_message(author, f"محصول شما با نام *{name}* توسط ادمین ها حذف شد")
    callback_query.author.del_state()


@bot.on_message(private & equals('حذف محصول➖'))
async def delete_prod(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    reply = ReplyKeyboard()
    for i in userList['products'].keys():
        if userList['products'][i]['author'] == str(message.chat.id):
            reply.add_row(f"{userList['products'][i]['name']}")
    reply.add_row('بازگشت🔙')
    await message.reply("محصولی که میخواهید حذف کنید را انتخاب کنید", reply)
    message.author.set_state("DELETE")


@bot.on_message(at_state("DELETE") & equals('بازگشت🔙'))
async def back_del(*, client, message):
    await message.reply("بازگشت به صفحه اصلی... ✈", main_key)
    message.author.del_state()


@bot.on_message(at_state("DELETE"))
async def delete_product(*, client, message):
    await message.reply("ایا از حذف این محصول اطمینان دارید؟\n پس از حذف هیچ کس قادر به دیدن این محصول نیست!", InlineKeyboard([('نه، برگرد', 'no')], [('اره، پاکش کن', message.text)]))
    message.author.set_state("CONFIRM")


@bot.on_callback_query(at_state("CONFIRM"))
async def del_confirm(callback_query):
    if callback_query.data == 'no':
        await callback_query.answer("پس برمیگردیم...", main_key)
        callback_query.author.del_state()
    else:
        with open(data_file, 'r') as file:
            userList = json.load(file)
        res = find_byname(callback_query.data)
        id = res[0]
        del userList['products'][id]
        with open(data_file, 'w') as file:
            json.dump(userList, file, indent=4)
        await callback_query.answer("محصول مورد نظر با موفقیت حذف شد🗑", main_key)
        callback_query.author.del_state()


@bot.on_message(private & equals('حساب کاربری🔍'))
async def profile(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    phone = userList['phone'][str(message.chat.id)]
    card = userList['card'][str(message.chat.id)]
    wallet = userList['wallet'][str(message.chat.id)]
    if phone == "":
        phone = "اطلاعاتی ثبت نشده"
    if card == "":
        card = "اطلاعاتی ثبت نشده!"
    if wallet == "":
        wallet = "اطلاعاتی ثبت نشده!"
    await message.reply(f"حساب کاربری شما 🧾\n 🚹 نام کاربری : {message.chat.username}\n\n\n 📞 شماره تلفن : {phone}\n\n\n 💳 شماره کارت : {card} \n\n\n 👛 توکن کیف پول : {wallet}", InlineKeyboard([('ارسال شماره تلفن 🤙', 'phonesend')], [('ثبت شماره کارت 💲', 'cardNO'), ('اتصال کیف پول 💰', 'walletToken')]))


@bot.on_callback_query(private)
async def callback_query(callback_query):
    if callback_query.data == 'phonesend':
        await callback_query.answer("لطفا شماره تلفن خود را ارسال کنید (از طریق دکمه زیر)", ReplyKeyboard([ReplyKeyboardButton('ارسال', request_contact=True)]))
        callback_query.author.set_state("PHONESEND")
    elif callback_query.data == 'cardNO':
        await callback_query.answer("لطفا شماره کارت خود را ارسال کنید")
        callback_query.author.set_state("CARDSEND")
    elif callback_query.data == 'walletToken':
        await callback_query.answer("هنوز نسخه نهایی پرداخت با کیف پول توسط بله منتشر نشده\n به زودی...")


@bot.on_message(at_state("PHONESEND") & contact)
async def save_phone(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    file = open(data_file, 'w')
    userList['phone'][str(message.chat.id)] = message.contact.phone_number
    json.dump(userList, file, indent=4)
    file.close()
    await message.reply("شماره تلفن شما با موفقیت ثبت شد ✅", main_key)
    message.author.del_state()


@bot.on_message(private & at_state("CARDSEND"))
async def save_card(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    check_url = "https://aladdin4api.pythonanywhere.com/card"
    params = {
        'token': "key-Z2ePukbraZcZScH0Al",
        'card': message.text
    }
    response = requests.get(check_url, params=params)
    r = response.json()
    if r['ok'] == True:
        if len(message.text) == 16 and message.text.isnumeric() and r['result']['isValid']:
            file = open(data_file, 'w')
            userList['card'][str(message.chat.id)] = message.text
            json.dump(userList, file, indent=4)
            file.close()
            await message.reply("شماره کارت شما با موفقیت ثبت شد ✅", main_key)
            message.author.del_state()
        else:
            await message.reply("شماره کارت معتبر نیست \n از صحت آن اطمینان حاصل کنید و در صورتی که بازم با مشکل برخوردید با پشتیبانی در ارتباط باشید")
    else:
        await message.reply("ارتباط با سرور برای بررسی شماره کارت برقرار نشد، لطفا لحظاتی دیگر دوباره امتحان کنید")


@bot.on_message(private & equals('ثبت محصول جدید➕'))
async def add_prod(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    if userList['card'][str(message.chat.id)] == "" and userList['phone'][str(message.chat.id)] == "":
        await message.reply("لطفا ابتدا پروفایل خود را از طریق بخش [پروفایل](send:حساب کاربری🔍) کامل کنید")
    elif userList['users'][str(message.chat.id)] == 'Banned':
        await message.reply("حساب شما توسط ادمین ها بن شده\n دیگر نمیتوانید از قابلیت های ربات استفاده کنید در صورتی که فکر میکنید این انتخاب به اشتباه صورت گرفته با پشتیبانی در تماس باشید")
    else:
        await message.reply("نام محصول مورد نظر را وارد کنید :")
        message.author.set_state("NAME")


@bot.on_message(private & at_state("NAME"))
async def name(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    id = unique(userList)
    file = open(data_file, 'w')
    userList['products'][str(id)] = {}
    userList['products'][str(id)]['name'] = message.text
    json.dump(userList, file, indent=4)
    file.close()
    await message.reply("توضیحات محصول خود را وارد کنید : ", ReplyKeyboard(['لازم نیست']))
    save_product(message.chat.id, id)
    message.author.set_state("DESC")


@bot.on_message(private & at_state("DESC"))
async def description(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
        id = find_product(message.chat.id)
        file = open(data_file, 'w')
    if message.text != 'لازم نیست':
        userList['products'][str(id)]['description'] = message.text
        json.dump(userList, file, indent=4)
        file.close()
        await message.reply("قیمت محصول خود را وارد کنید : ", main_key)
        message.author.set_state("PRICE")
    else:
        userList['products'][str(id)]['description'] = "بدون توضیحات..."
        json.dump(userList, file, indent=4)
        file.close()
        await message.reply("قیمت محصول خود را وارد کنید : (به ریال)", main_key)
        message.author.set_state("PRICE")


@bot.on_message(private & at_state("PRICE"))
async def price(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    price = message.text
    if price.isnumeric():
        id = find_product(message.chat.id)
        file = open(data_file, 'w')
        userList['products'][str(id)]['price'] = message.text
        userList['products'][str(id)]['author'] = str(message.chat.id)
        json.dump(userList, file, indent=4)
        file.close()
        reply = ReplyKeyboard(['ثبت نام (دریافت اطلاعات)'], [
                              'واسطه‌گری'], ['ارسال فایل'])
        await message.reply("محصول شما چه نوع است؟", reply)
        message.author.set_state("MODE")
    else:
        await message.reply("فقط عدد بفرستید")


@bot.on_message(at_state("MODE"))
async def set_mode(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    id = find_product(message.author.id)
    file = open(data_file, 'w')
    if message.text == 'ثبت نام (دریافت اطلاعات)':
        await message.reply("به زودی...")
    elif message.text == 'واسطه‌گری':
        userList['products'][str(id)]['mode'] = 'between'
        await message.reply("نام کاربری حساب را ارسال کنید")
        message.author.set_state("USERNAME")
    elif message.text == 'ارسال فایل':
        userList['products'][str(id)]['mode'] = 'sendDoc'
        await message.reply("فایل خود را ارسال کنید (مطمئن شوید که به فرمت فایل ارسال میشود)")
        message.author.set_state("FILE")
    json.dump(userList, file, indent=4)
    file.close()


@bot.on_message(at_state("FILE") & document)
async def saverfile(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    id = find_product(message.author.id)
    file = open(data_file, 'w')
    userList['products'][str(id)]['fileId'] = message.document.id
    json.dump(userList, file, indent=4)
    file.close()
    await message.reply("محصول شما با موفقیت ثبت شد", main_key)
    message.author.del_state()


@bot.on_message(at_state("USERNAME"))
async def username_save(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    id = find_product(message.author.id)
    file = open(data_file, 'w')
    userList['products'][str(id)]['username'] = message.text
    json.dump(userList, file, indent=4)
    file.close()
    await message.reply("رمز عبور حساب را ارسال کنید : ")
    message.author.set_state("PASSWORD")


@bot.on_message(at_state("PASSWORD"))
async def saver_pssword(*, client, message):
    with open(data_file, 'r') as file:
        userList = json.load(file)
    id = find_product(message.author.id)
    file = open(data_file, 'w')
    userList['products'][str(id)]['password'] = message.text
    json.dump(userList, file, indent=4)
    file.close()
    await message.reply("محصول شما با موفقیت ثبت شد", main_key)
    message.author.del_state()


@bot.on_message(private & equals('قوانین و مقررات ⚖'))
async def laws(*, client, message):
    await message.reply("قوانین و مقررات استفاده از ربات *کاسب* :\n 1. *ربات و توسعه دهندگان ان هیچ مسئولیتی در قبال محصولات ثبت شده ندارد*\n 2. *ربات و توسعه دهندگان ان حق دارند در هر زمان قوانین ربات را تغییر دهند*\n 3. *توسعه دهندگان تا حد امکان برای امنیت و سالم بودن ربات تلاش میکنند اما هیچ مسئولیتی برای محصولات کاربران قبول نمیکند*\n 4. *توسعه دهندگان ربات حق دارند در صورت نیاز اطلاعات کاربر را به مراجع قضایی تحویل دهند*\n 5. *مسئولیت تمامی محصولات ثبت شده به عهده کاربر میباشد*\n 6. *در صورت مشاهده شدن محصولات غیر مجاز توسط ادمین ها، حساب شما مسدود خواهد شد*\n 7. *ربات کاسب تابع قوانین جمهوری اسلامی ایران است *\n 8. *در صورتی که کاربری شماره کارت خود را ثبت نکند، مبلغ به کارت سازنده ربات واریز خواهد شد و پس از پیگیری و تایید به حساب فروشنده واریز خواهد شد*\n 9. *سازنده ربات هیچ مسئولیتی در قبال شماره کارت ثبت شده ندارد و ربات فقط یک واسطه است*\n 10. *سازنده ربات هیچ مسئولیتی در قبال کلاهبرداری ندارد، لطفا قبل از خرید از فرستنده ان مطمئن شوید* \n\n تجربه خوبی را برای شما آرزومندیم ✨")

bot.run()
