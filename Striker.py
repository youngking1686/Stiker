import tkinter as tk
from tkinter import END, ttk, messagebox
import tkinter.scrolledtext as scrolledtext
from numpy import sort
from tkinter.constants import CENTER, NORMAL
import config
from functools import partial
from prettytable import PrettyTable
import pandas as pd
import datetime
from nsepython import *
import operations

mainfolder = config.mainfolder

root = tk.Tk()
root.minsize(920, 650)
root.title("STRIKER")
# root.resizable(width=False, height=False)
root.configure(background='#2e2a2a')

sides = ('Long', 'Short')
expiry = ('Current', 'Next')
Instrument = ('NIFTY', 'BANKNIFTY')
sort_by = ('Strike', '%Reward', '%Risk','RR', 'IV', 'LTP', '%Change', 'Delta', 'Theta', 'OI', 'Chng-OI', '%Chng-OI', 'Volume', 'Location')
sell_options, buy_options = None, None
toggle1, toggle2 = 0, 0

class v:
    inst, side, expi, piv, sort_s, sort_b = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.IntVar(), tk.StringVar(), tk.StringVar()
    entry, stop, target, underlying_ltp = tk.IntVar(), tk.IntVar(), tk.IntVar(), 0

    inst.set('NIFTY')
    side.set('Long')
    expi.set('Current')
    piv.set(0)
    sort_s.set('Strike')
    sort_b.set('Strike')

    entry.set(0)
    stop.set(0)
    target.set(0)
    
class Action:
    def reset_trade(side, inst):
        side = side.get()
        inst = inst.get()
        undl_ltp = operations.fetch_ltp(inst)
        if side == 'Long':
            entry_v = int(undl_ltp)
            stop_v = int(undl_ltp - 30)
            target_v = int(undl_ltp + 100)
        else:
            entry_v = int(undl_ltp)
            stop_v = int(undl_ltp + 30)
            target_v = int(undl_ltp - 100)
        v.underlying_ltp = undl_ltp
        v.entry.set(entry_v)
        v.stop.set(stop_v)
        v.target.set(target_v)
        ttk.Label(mframe, text = v.underlying_ltp, font = ('calibre',10,'bold'), width=10).grid(row=2,column=8, padx=3, pady=3)

    def calculate(inst, expi, side, piv, sort_s, sort_b, entry, stop, target):
        global sell_options, buy_options
        entry, stop, target = entry.get(), stop.get(), target.get()
        if entry == 0 or stop == 0 or target == 0:
            Action.reset_trade(side, inst)
            messagebox.showerror("Error", "Trade inputs cannot be empty!")
        instrument, expiry, side, piv = inst.get(), expi.get(), side.get(), piv.get()
        sell_options = operations.opt_data(instrument, expiry, side, piv, entry, stop, target).get_sell_opt_data()
        buy_options = operations.opt_data(instrument, expiry, side, piv, entry, stop, target).get_buy_opt_data()
        totarget = abs(entry-target)
        tostop = abs(entry-stop)
        Action.display_sell(sort_s, inst, expi, totarget, tostop)
        Action.display_buy(sort_b, inst, expi, totarget, tostop)
        last_update = datetime.datetime.now().strftime("%H:%M:%S")
        ttk.Label(mframe, text = "Last updated \n" + last_update, font = ('calibre',10,'bold')).grid(row=1,column=9)
        v.underlying_ltp = operations.fetch_ltp(instrument)
        ttk.Label(mframe, text = v.underlying_ltp, font = ('calibre',10,'bold'), width=10).grid(row=2,column=8, padx=3, pady=3)
        
    def display_sell(sort_s, inst, expi, totarget, tostop):
        global toggle1
        sort, instrument, expiry = sort_s.get(), inst.get(), expi.get()
        if not toggle1:
            data1 = sell_options.sort_values(by=[sort], ascending=False).values.tolist()
            toggle1 = 1
        else:
            data1 = sell_options.sort_values(by=[sort], ascending=True).values.tolist()
            toggle1 = 0
        opti_sell=PrettyTable()
        opti_sell.field_names = ('Strike', 'Option','%Reward', '%Risk', 'RR',  'IV', 'LTP', '%Change', 'Delta', 'Theta', 'OI', 'Chng-OI', '%Chng-OI', 'Volume', 'Location')
        sorter = partial(Action.display_sell, v.sort_s, v.inst, v.expi, totarget, tostop)
        ttk.Label(frame0, text = f'Options Selling ({instrument} - {expiry} Week Expiry)', font = ('calibre',10,'bold')).grid(row=1,column=1)
        ttk.Label(frame0, text = f'Traget: {totarget} pnts; Stop: {tostop} pnts', font = ('calibre',10,'bold')).grid(row=1,column=2)
        ttk.Label(frame0, text = 'Sort by', font = ('calibre',10,'')).grid(row=1,column=3)
        ttk.Spinbox(frame0, values=sort_by, textvariable=v.sort_s, width=12, foreground="black").grid(row=1,column=4, padx=30, pady=10)
        tk.Button(frame0,text = 'Sort', font = ('',10,'bold'), command = sorter, width=5, state=NORMAL).grid(row=1,column=5, padx=10, pady=10)
        opt_sell = scrolledtext.ScrolledText(frame0, undo=True, wrap='word', font=('consolas', '8'), height = 15, width = 142, bg='#ff6666')
        opt_sell.grid(row=3,column = 1, columnspan=5, padx=3, pady=1)
        for ent in data1:
            opti_sell.add_row(ent)
        opt_sell.insert(tk.INSERT, opti_sell)
        
    def display_buy(sort_b, inst, expi, totarget, tostop):
        global toggle2
        sort, instrument, expiry = sort_b.get(), inst.get(), expi.get()
        if not toggle2:
            data2 = buy_options.sort_values(by=[sort], ascending=False).values.tolist()
            toggle2 = 1
        else:
            data2 = buy_options.sort_values(by=[sort], ascending=True).values.tolist()
            toggle2 = 0
        opti_buy=PrettyTable()
        opti_buy.field_names = ('Strike', 'Option','%Reward', '%Risk', 'RR',  'IV', 'LTP', '%Change', 'Delta', 'Theta', 'OI', 'Chng-OI', '%Chng-OI', 'Volume', 'Location')
        sorter = partial(Action.display_buy, v.sort_b, v.inst, v.expi, totarget, tostop)
        ttk.Label(frame1, text = f'Options Buying ({instrument} - {expiry} Week Expiry)', font = ('calibre',10,'bold')).grid(row=1,column=1)
        ttk.Label(frame1, text = f'Traget: {totarget} pnts; Stop: {tostop} pnts', font = ('calibre',10,'bold')).grid(row=1,column=2)
        ttk.Label(frame1, text = 'Sort by', font = ('calibre',10,'')).grid(row=1,column=3)
        ttk.Spinbox(frame1, values=sort_by, textvariable=v.sort_b, width=12, foreground="black").grid(row=1,column=4, padx=30, pady=10)
        tk.Button(frame1,text = 'Sort', font = ('',10,'bold'), command = sorter, width=5, state=NORMAL).grid(row=1,column=5, padx=10, pady=10)
        opt_buy = scrolledtext.ScrolledText(frame1, undo=True, wrap='word', font=('consolas', '8'), height = 15, width = 142, bg='#66ff66')
        opt_buy.grid(row=3,column = 1, columnspan=5, padx=3, pady=1)
        for ent in data2:
            opti_buy.add_row(ent)
        opt_buy.insert(tk.INSERT, opti_buy)
    
    def on_closing():
        if messagebox.askyesno("Quit", "Do you want to quit?"):
            root.destroy()

class gui_contents:
    def strike_selection(mframe):
        ttk.Label(mframe, text = 'Instrument', font = ('calibre',10,'bold')).grid(row=1,column=1, padx=5, pady=5)
        ttk.Label(mframe, text = 'Trade', font = ('calibre',10,'bold')).grid(row=2,column=1, padx=3, pady=3)
        ttk.Label(mframe, text = 'Expiry', font = ('calibre',10,'bold')).grid(row=1,column=3, padx=3, pady=3)
        ttk.Label(mframe, text = '%Change IV', font = ('calibre',10,'bold')).grid(row=2,column=3, padx=3, pady=3)
        ttk.Label(mframe, text = 'Entry', font = ('calibre',10,'bold')).grid(row=1,column=5, padx=3, pady=3)
        ttk.Label(mframe, text = 'Stop', font = ('calibre',10,'bold')).grid(row=2,column=5, padx=3, pady=3)
        ttk.Label(mframe, text = 'Target', font = ('calibre',10,'bold')).grid(row=1,column=7, padx=3, pady=3)
        update_param = partial(Action.reset_trade, v.side, v.inst)
        tk.Button(mframe,text = 'LTP', font = ('',10,'bold'), command = update_param, width=4, state=NORMAL).grid(row=2,column=7, padx=3, pady=3)
        ttk.Spinbox(mframe, values=Instrument, textvariable=v.inst, command = update_param, width=8, foreground="black").grid(row=1,column=2, padx=30, pady=10)
        ttk.Spinbox(mframe, values=sides, textvariable=v.side, command = update_param, width=8, foreground="black").grid(row=2,column=2, padx=30, pady=10)
        ttk.Spinbox(mframe, values=expiry, textvariable=v.expi, width=8, foreground="black").grid(row=1,column=4, padx=30, pady=10)
        ttk.Spinbox(mframe, from_=-100, to=100, increment=2, textvariable=v.piv, width=10, foreground="black").grid(row=2, column=4, padx=30, pady=10)
        ttk.Spinbox(mframe, from_=0, to=100000, increment=1, textvariable=v.entry, width=10, foreground="black").grid(row=1, column=6, padx=3, pady=10)
        ttk.Spinbox(mframe, from_=0, to=100000, increment=1, textvariable=v.stop, width=10, foreground="black").grid(row=2, column=6, padx=3, pady=10)
        ttk.Spinbox(mframe, from_=0, to=100000, increment=1, textvariable=v.target, width=10, foreground="black").grid(row=1, column=8, padx=3, pady=10)
        ttk.Label(mframe, text = v.underlying_ltp, font = ('calibre',10,'bold'), width=10).grid(row=2,column=8, padx=3, pady=3)
        calculator = partial(Action.calculate, v.inst, v.expi, v.side, v.piv, v.sort_s, v.sort_b, v.entry, v.stop, v.target)
        tk.Button(mframe,text = 'Calculate', font = ('',12,'bold'), command = calculator, width=10, state=NORMAL).grid(row=2,column=9, padx=5, pady=10)
        

mframe = ttk.Frame(root, width=920, height=200)
mframe.pack()
frame0 = ttk.Frame(root, width=920, height=270)
frame0.pack(padx=10, pady=10)
frame1 = ttk.Frame(root, width=920, height=270)
frame1.pack(padx=10, pady=10)
gui_contents.strike_selection(mframe)

if __name__=='__main__':    
    root.protocol("WM_DELETE_WINDOW", Action.on_closing)
    root.mainloop()
