from symtable import Symbol
import ccxt 
import time
import datetime
import pandas as pd

api_key = '6zHOZK1HIAidFdxoGxHR5GB85VOqCZ7VbbKXdBz8Ne6XfFUG4feKcPfVw15o0Ew1'
secret = 'PevYip6CONYhgYKdNTVnGjIYGS03hptq09jqUgsCUlLFlJJXJ7KcTXUyGmJmEVcl'

binance = ccxt.binance(config={
    'apiKey': api_key, 
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

def cal_target(self,coin,origin):
    btc = binance.fetch_ohlcv(
        symbol=coin,
        timeframe='1d', 
        since=None, 
        limit=10)

    df = pd.DataFrame(data=btc, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    target = today['open'] + (yesterday['high'] - yesterday['low']) * 0.5
    if origin == True:
     return target 
    if origin == False:
     return today['open']

def cal_amount(usdt_balance, cur_price):
   try: 
    amount = ((usdt_balance * 1000000)/cur_price) / 1000000
    return amount 
   except Exception as e:
     print(e)  

def enter_position(exchange, coin, cur_price,target, amount, position):
    origin = False
    open = cal_target(binance,'BTCUSDT',origin)
    bitcoin = binance.fetch_ticker("BTC/USDT")
    if open <= bitcoin['last']:
        btc = True
    else:
        btc = False
    if (cur_price >= target) and btc:      
        position['type'] = 'long'
        position['amount'] = amount
        exchange.create_market_buy_order(symbol=coin, amount=amount)
        print("지구 롱")
        buy_price = cur_price
    if (cur_price >= target) and btc == False:      
        position['type'] = 'short'
        position['amount'] = amount
        exchange.create_market_sell_order(symbol=coin, amount=amount)
        print("지구 숏")
        buy_price = cur_price

def exit_position(exchange, coin, position):
    amount = position['amount']
    if position['type'] == 'short':
        exchange.create_market_buy_order(symbol=coin, amount=amount)
        position['type'] = None 
    if position['type'] == 'long':
        exchange.create_market_sell_order(symbol=coin, amount=amount)
        position['type'] = None 

coin = ""
start = True
position = {"type": None,"amount": 0} 
buy_price = 0

while True: 
    now = datetime.datetime.now()                      #현재시간
    markets = binance.load_markets()                    
    for m in markets.keys():                            #종목수만큼 반복
       if 'USDT' in m:                                  #USDT라면
        coin = m                                
        if now.hour == 9 and now.minute == 00 and (0 <= now.second < 10): #지금이 9:00시라면 올매도
            if op_mode and position['type'] is not None:                               
                exit_position(binance, coin, position)
                op_mode = False
                start = False
                buy_price = 0
        if now.hour == 10 and now.minute == 30:                              #지금이 10시반이면 시작하기
            start = True
        if start:
         origin = True
         target = cal_target(binance, coin,origin)      #타켓을 coin으로 정하기
         balance = binance.fetch_balance()          
         usdt = balance['total']['USDT']   #잔고 불러오기
         op_mode = True
        ticker = binance.fetch_ticker(coin)
        
        cur_price = ticker['last']#코인 현재가 불러오기
        if cur_price == None:
          continue
        amount = cal_amount(usdt, cur_price)#코인 양 세기
        if op_mode and position['type'] is None:  #조건 만족하면 코인 올매수하기
            print(coin,usdt,cur_price,target)
            enter_position(binance, coin, cur_price,target, amount, position)
        time.sleep(0.5)
       else:
        continue
