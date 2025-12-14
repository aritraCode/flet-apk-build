
import yfinance as yf 
import flet as ft 

def _price(symbol):
    symbol = symbol.strip().upper()
    try:
        return yf.Ticker(symbol).info.get("regularMarketPrice",0)
    except:
        return None

def main(page: ft.Page):

    sym_i = ft.TextField(label="Symbol")
    price_output = ft.Text()

    def get_price(e):
        symbol = sym_i.value
        if not symbol.strip():
            return
        price = _price(symbol)
        if price is not None:
            price_output.value = f"{symbol.strip().upper()} price: {price}"
        else:
            price_output.value = f"Unable to get price for '{symbol}'"
        page.update()

    page.add(ft.Column(controls=[
        sym_i, price_output, ft.ElevatedButton(text="show", on_click=get_price)
    ]))

if __name__=="__main__":
    ft.app(target=main)
