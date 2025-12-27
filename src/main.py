import flet as ft
import uuid

# ---- your existing functions (UNCHANGED) ----
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from tradingview_ta import TA_Handler

def get_stocks_data(symbols:list)->dict:
    """
    Retrieves technical analysis data for a list of stock symbols from TradingView.

    This function fetches various technical indicators for the specified stock symbols
    from the NSE exchange (India) with a daily interval.

    Args:
        symbols (list): A list of strings, where each string is a stock symbol (e.g., ["RELIANCE", "INFY"]).
                        Symbols are converted to lowercase internally.

    Returns:
        dict: A dictionary where keys are the input stock symbols and values are dictionaries
              containing rounded technical indicators for that symbol. If an error occurs
              during data retrieval for any symbol, the function returns a dictionary
              with a single key "error" and its corresponding error message.
    """
    results = {}
    for symbol in symbols:
        try:
            handler = TA_Handler(
                symbol=symbol.strip().lower(),
                exchange="nse",
                screener="india",
                interval="1d"
            )
            analysis = handler.get_analysis()
            indicators = analysis.indicators
            data = {}
            ilist = [
                "close","RSI","ADX", "ADX+DI", "ADX-DI",
                "Mom","Stoch.K", "Stoch.D",
                "MACD.macd","MACD.signal","EMA10", "EMA20",
                "EMA50", "EMA100", "EMA200",
                "Pivot.M.Classic.S3", "Pivot.M.Classic.S2","Pivot.M.Classic.S1",
                "Pivot.M.Classic.Middle", "Pivot.M.Classic.R3",
                "Pivot.M.Classic.R2", "Pivot.M.Classic.R1"
            ]
            for i in ilist:
                v = indicators.get(i)
                if v is not None:
                    data[i] = round(v,1)
            results[symbol] = data
        except Exception as e:
            results[symbol] = {"error": str(e)}
    return results

def run_stock_agent(model_name: str, api_key: str, thread_id:str, query: str) -> str:
    llm = ChatGroq(
        model=model_name,
        api_key=api_key
    )

    tools = [get_stocks_data]

    prompt = """
You are a helpfull stock analysis agent.

Your job is to use the 'get_stocks_data' tool to get stocks data,
analysis those data and come up with decisive trading plan.

if user ask for trading signal,
you should provide with STRONG_BUY / BUY / NEUTRAL / SELL / STRONG_SELL signal with
entry, take profit, stop loss for create new position,
or for existing position HOLD / PROFIT BOOK / PARTIAL PROFIT BOOL signal with price range.

Do NOT use tables or other complicated Markdown Format,
simple bullet points with simple easy to understand English language.

Do NOT give random stock analysis, use the tool to get stocks data and give analysis based on that.

if user's query is not about trading or finance,
politely decline to answer.
"""

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt,
        checkpointer=InMemorySaver()
    )

    response = agent.invoke(
        {"messages": [{"role": "user", "content": query}]},
        {"configurable": {"thread_id": thread_id}},
    )
    return response["messages"][-1].content

# ---- Flet UI ----
def main(page: ft.Page):
    page.title = "Stock Analysis Agent"
    page.scroll = ft.ScrollMode.AUTO
    

    # NEW thread per app launch
    thread_id = str(uuid.uuid4())

    # Restore settings
    model_input = ft.TextField(
        label="Model name",
        value=page.client_storage.get("model_name") or "llama-3.3-70b-versatile",
        expand=True,
    )

    api_key_input = ft.TextField(
        label="Groq API Key",
        password=True,
        can_reveal_password=True,
        value=page.client_storage.get("api_key") or "",
        expand=True,
    )

    def save_settings(e=None):
        page.client_storage.set("model_name", model_input.value)
        page.client_storage.set("api_key", api_key_input.value)

        page.open(
            ft.SnackBar(
                content=ft.Text("Settings saved")
            )
        )

    save_btn = ft.FilledButton("Save Settings", on_click=save_settings,width=500)

    chat_column = ft.Column(spacing=12)

    query_input = ft.TextField(
        label="Ask about a stock",
        multiline=True,
        min_lines=2,
        expand=True,
    )

    def send_query(e):
        if not query_input.value.strip():
            return

        save_settings()

        chat_column.controls.append(
            ft.Text(f"User: {query_input.value}", weight=ft.FontWeight.BOLD)
        )
        page.update()

        try:
            response = run_stock_agent(
                model_name=model_input.value,
                api_key=api_key_input.value,
                thread_id=thread_id,
                query=query_input.value,
            )
            chat_column.controls.append(ft.Markdown(response))
        except Exception as ex:
            chat_column.controls.append(
                ft.Text(f"Error: {ex}", color=ft.Colors.RED)
            )

        query_input.value = ""
        page.update()

    send_btn = ft.ElevatedButton("Analyze", on_click=send_query)

    def toggle_settings(e):
        settings.visible = not settings.visible
        page.update()

    settings = ft.Column(visible=False,controls =[
        ft.Text("Settings", size=18, weight=ft.FontWeight.BOLD),
        model_input,
        api_key_input,
        save_btn,
    ])


    page.add(
        ft.Container(
            padding=ft.Padding(20,5,20,5),
            expand=True,
            content=ft.Column(expand=True, spacing=10, controls=[
                ft.Row(
                    alignment = ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("StockInfo",size=18, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.SETTINGS, on_click=toggle_settings)
                    ]
                ),
                settings,
                ft.Divider(),
                chat_column,
                ft.Row([query_input, send_btn]),
            ])
        )
    )

ft.app(target=main)
