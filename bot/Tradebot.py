#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from binance.client import Client
from binance.enums import *
import json
import time
from tabulate import tabulate
import os

def notify(title, text):
    os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format(text, title))

# Configuración

# Binance API conf
API_SECRET = ''
SECRET_KEY = ''

# Moneda
coin = 'C98USDT'

# % a comprar o vender en cada iteración
trade_percent = 0.95

# Distancia en % para realizar compra o venta
dist_percent = 0.003

# Distancia en % respecto al min o max para concretar
dist_lim_percent = 0.9952763819095477

# Variables
conf = {}

# Redondeo decimales tabla
d = 4

# Contador para refrescar sesión
loops = 0

# Loop
while 1 == 1:

    if loops == 0:

        # Refresca sesión
        client = Client(API_SECRET,SECRET_KEY,tld='com')
        loops = 6
    else:
        loops -= 1

    
    # Load Conf
    with open('conf.json') as json_file:
        conf = json.load(json_file)
    
    # Obtiene el precio actual de la moneda
    current_price = float(client.get_avg_price(symbol=coin)['price'])

    alcanzado = conf['best_last_price'] != 0.0
    
    # Si la siguiente acción es vender (esperar a que el precio suba)
    if conf['next_action'] == 'sell':

        vf = 0.0
        if alcanzado:
            vf = round(current_price/conf['best_last_price'],d)

        print()
        print(tabulate([['VENTA',round(current_price, d),round(conf['previous_price'], d),round(100.0*(1.0 - conf['previous_price']/current_price),d),alcanzado,round(conf['best_last_price'],d),vf]], headers=['Modo', 'Precio','Precio Inicial','%','Alcanzado','Best Price','Dist'], tablefmt="grid"))
        
        # Si acaba de superar el dist_percent
        if not alcanzado and current_price >= conf['previous_price']*(1.0 + dist_percent):
            
            # Guarda el max alcanzado
            conf['best_last_price'] = current_price
            
        # Si ya superó el dist_percent
        elif alcanzado:
            
            # Si el precio es mejor que el anterior
            if current_price > conf['best_last_price']:
                conf['best_last_price'] = current_price

            # Si cae abruptamente menor al mínimo actualiza el máximo
            elif current_price <= conf['previous_price']*(1.0 + dist_percent):
                conf['best_last_price'] = current_price
                
            # Si el precio es peor que el mejor pero mayor que el limite dist_lim_percent
            elif current_price/conf['best_last_price'] <= dist_lim_percent and current_price >= conf['previous_price']*(1.0 + dist_percent):
                
                # ------------ REALIZA VENTA ------------------------
                current_balance_coin = float(client.get_asset_balance(asset='C98')['free'])
                quantity = int(current_balance_coin*trade_percent)
                order = client.order_market_sell(symbol=coin,quantity=quantity)
                conf['best_last_price'] = 0
                conf['next_action'] = 'buy'
                ganancia = float(order['cummulativeQuoteQty']) - conf['previous_price'] * quantity
                conf['earned'] += ganancia
                conf['previous_price'] = float(order['cummulativeQuoteQty'])/float(order['executedQty'])
                print("----------------------------------------------------------------------")
                print("REALIZA VENTA:{:.3f} C98,${:.3f} de ganancia,${:.3f} ganancias totales".format(quantity,ganancia,conf['earned']))
                print("----------------------------------------------------------------------")
                notify("Venta realizada!", "Has vendido {:.3f} C98, ${:.3f} de ganancia, ${:.3f} ganancias totales".format(quantity,ganancia,conf['earned']))
                
    
    # Si la siguiente acción es comprar (el precio debe bajar)
    elif conf['next_action'] == 'buy':
        
        print()
        print(tabulate([['COMPRA',round(current_price, d),round(conf['previous_price'], d),round(100.0*(conf['previous_price']/current_price - 1.0),d),alcanzado,round(conf['best_last_price'],d),round(conf['best_last_price']/current_price,d)]], headers=['Modo', 'Precio','Precio Inicial','%','Alcanzado','Best Price','Dist'], tablefmt="grid"))
        
        # Si acaba de superar el dist_percent
        if not alcanzado and current_price <= conf['previous_price']*(1.0 - dist_percent):
            
            # Guarda el min alcanzado
            conf['best_last_price'] = current_price
        
        # Si ya superó el dist_percent
        elif alcanzado:
            
            # Si el precio es mejor que el anterior
            if current_price < conf['best_last_price']:
                conf['best_last_price'] = current_price
        
            # Si sube abruptamente mayor al máximo actualiza el mínimo
            elif current_price >= conf['previous_price']*(1.0 - dist_percent):
                conf['best_last_price'] = current_price
            
            # Si el precio es peor que el mejor pero menor que el limite dist_lim_percent
            elif conf['best_last_price']/current_price <= dist_lim_percent and current_price <= conf['previous_price']*(1.0 - dist_percent):
                
                # ------------ REALIZA COMPRA ------------------------
                current_balance_usdt = float(client.get_asset_balance(asset='USDT')['free'])
                quantity = int((trade_percent*current_balance_usdt)/current_price)
                order = client.order_market_buy(symbol=coin,quantity=quantity)
                conf['best_last_price'] = 0
                conf['next_action'] = 'sell'
                newPrice = float(order['cummulativeQuoteQty'])/float(order['executedQty'])
                print("----------------------------------------------------------------------")
                print("COMPRA REALIZADA:{:.3f} C98 a {:.3f}% del precio anterior".format(float(order['executedQty']),100.0*newPrice/conf['previous_price']))
                print("----------------------------------------------------------------------")
                notify("Compra realizada!", "Has comprado {:.3f} C98 a {:.3f}% del precio anterior".format(float(order['executedQty']),100.0*newPrice/conf['previous_price']))
                conf['previous_price'] = newPrice
                
    # Saves conf
    with open('conf.json', 'w') as json_file:
        json.dump(conf, json_file)
    
    time.sleep(5*60)