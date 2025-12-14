import yfinance as yf
import flet as ft

def _price(symbol):
    symbol = symbol.strip().upper()
    try:
        df = yf.Ticker(symbol).history()
        return {"close": df.iloc[-1].Close}
    except Exception as e:
        return {"error": str(e)}

def main(page: ft.Page):

    sym_i = ft.TextField(label="Symbol")
    price_output = ft.Text()

    def get_price(e):
        symbol = sym_i.value
        if not symbol.strip():
            return
        price = _price(symbol)
        if "close" in price:
            price_output.value = f"{symbol.strip().upper()} price: {price["close"]}"
        elif "error" in price:
            price_output.value = f"Unable to get price for '{symbol}' due to - {price["error"]}"
        else:
            price_output.value = str(price)
        page.update()

    page.add(ft.Column(controls=[
        sym_i, price_output, ft.ElevatedButton(text="show", on_click=get_price)
    ]))

if __name__=="__main__":
    ft.app(target=main)
