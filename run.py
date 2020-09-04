from auth import CoinbaseExchangeAuth
from config import API_KEY, API_SECRET, API_PASSPHRASE
from pprint import pprint
import cbpro
import numpy as np
import datetime as dt
import time



socket_url = 'wss://ws-feed.pro.coinbase.com'
authenticated_client = cbpro.AuthenticatedClient(API_KEY, API_SECRET, API_PASSPHRASE)
# --- Key Items: ------------------------------
#----------------------------------------------
iteration = 1
funding = 20.00

buy = True
# - granularity=60: data from every 1 minute.
# - Rate Limit: 5 requests per second, 10 requests per second in bursts
# ----------------------------------------------------------------------
while True:
    try:
        historical_data = authenticated_client.get_product_historic_rates('BTC-USD', granularity=30)
        price = np.squeeze(np.asarray(np.matrix(historical_data)[:,4]))

        time.sleep(1) # wait one second

        new_data = authenticated_client.get_product_ticker(product_id='BTC-USD')
        print("NEW DATA: ", new_data)
        current_price = new_data['price']
    except:
        print("Error in feed.py")

#---------------------------------
# - Calculating indicator values.
#----------------------------------
    ROC11 = np.zeros(13)
    ROC14 = np.zeros(13)
    ROCSUM = np.zeros(13)

    for ii in range(0,13):
        ROC11[ii] = (100*(price[ii]-price[ii+11]) / float(price[ii+11]))
        ROC14[ii] = (100*(price[ii]-price[ii+14]) / float(price[ii+14]))
        ROCSUM[ii] = ( ROC11[ii] + ROC14[ii] )

    for ll in range(0,4):
        coppock[ll] = (
            ((1*ROCSUM[ll+9])
            + (2*ROCSUM[ll+8])
            + (3*ROCSUM[ll+7])
            + (4*ROCSUM[ll+6])
            + (5*ROCSUM[ll+5])
            + (6*ROCSUM[ll+4])
            + (7*ROCSUM[ll+3])
            + (8*ROCSUM[ll+2])
            + (9*ROCSUM[ll+1])
            + (10*ROCSUM[ll])) / float(55)
        )

    coppockD1 = np.zeros(3)
    for mm in range(3):
        coppockD1[mm] = coppock[mm] - coppock[mm+1]
# --------------------------------------------|
# ------------ End indicator calc. -----------|
# --------------------------------------------|
    purchase_size = float(funding)/float(current_price)
    available = float(authenticated_client.get_account('USD')['available']) # - Should equal funding while looking for buy; and 0 when looking for sell
    owned = float(authenticated_client.get_account('BTC')['available']) # - Should equal 0 while looking for buy; and current_price * purchase when looking for sell
    potInflow = float(current_price) * owned
# -------------------------------------------------|
# Buy Condition: looking for change in the slope...|
# from negative to positive. ----------------------|
#--------------------------------------------------|


    if buy == True and (coppockD1[0]/abs(coppockD1[0])) == 1.0 and (coppockD1[1]/abs(coppockD1[1])) == -1.0:

        # - Place limit @ current price.
        authenticated_client.place_limit_order(product_id='BTC-USD', side='buy',
                                            price=current_price, size=purchase_size)
        # - Buy value:
        dollar_cost_basis = (current_price*purchase_size)
        # - Print message.
        print("Buying {purchase_size} ".format(purchase_size=str(purchase_size))+"BTC "+"${current_price}".format(current_price=str(current_price)))

        # - Turn of buy watch.
        buy = False
        funding = 0

    # -----------------------|
    # Sell Conditions: -(Buy)|
    # -----------------------|
    if buy == False and (coppockD1[0]/abs(coppockD1[0])) == -1.0 and (coppockD1[1]/abs(coppockD1[1])) == 1.0:

        # - Place sell order @ current_price.
        authenticated_client.place_market_order(product_id='BTC-USD', side='sell', size=str(owned))
    
        # - Print message.
        print("Selling {long_currency} ".format(long_currency=str(owned))+"BTC "+"${current_price}".format(current_price=str(current_price)))

        buy = True
        funding = int(potInflow)
        # ------------|
        # - Make-Shift Stop-Loss |
        # ------------|
 
        if (potInflow) <= (0.98 * funding):
            if owned > 0:
                authenticated_client.place_market_order(product_id='BTC-USD', side='sell', size=str(owned))
                print("Stop-loss hit - sold all BTC.")

            break
    print("---------------------------------")
    print("Iteration Number: ", iteration)


    print("Current Price of BTC: ", current_price)
    print("Dollars Available:  ", "$"+funding)
    print("BTC Owned: ", owned)
    print("Value of BTC Owned: " "$"+(current_price*owned))
    
    # - Wait on repeat - 30 seconds (should equal granularity): 
    time.sleep(30)




    



                                

