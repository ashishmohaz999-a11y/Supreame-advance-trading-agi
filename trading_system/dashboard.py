import json
import os
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading AGI Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <style>
        body {
            background: #0d1117;
            color: #e6edf3;
            font-family: monospace;
            padding: 10px;
            margin: 0;
        }
        h1 { color: #58a6ff; text-align: center; }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .green { color: #3fb950; }
        .red   { color: #f85149; }
        .yellow{ color: #d29922; }
        .blue  { color: #58a6ff; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            background: #21262d;
            padding: 8px;
            text-align: left;
            color: #58a6ff;
        }
        td { padding: 8px; border-bottom: 1px solid #21262d; }
        .badge {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        .buy  { background: #1a4731; color: #3fb950; }
        .sell { background: #3d1c1c; color: #f85149; }
        .hold { background: #2d2a1e; color: #d29922; }
        .stat {
            display: inline-block;
            margin: 5px;
            padding: 10px 15px;
            background: #21262d;
            border-radius: 8px;
            text-align: center;
        }
        .stat-val { font-size: 22px; font-weight: bold; }
        .stat-lbl { font-size: 11px; color: #8b949e; }
    </style>
</head>
<body>
    <h1>🤖 Trading AGI Dashboard</h1>
    <p style="text-align:center; color:#8b949e;">
        Auto-refresh: 30s | {{ time }}
    </p>

    <!-- Stats Row -->
    <div class="card">
        <div class="stat">
            <div class="stat-val blue">₹{{ capital }}</div>
            <div class="stat-lbl">Capital</div>
        </div>
        <div class="stat">
            <div class="stat-val {{ 'green' if pnl >= 0 else 'red' }}">
                ₹{{ pnl }}
            </div>
            <div class="stat-lbl">Total PnL</div>
        </div>
        <div class="stat">
            <div class="stat-val">{{ total_trades }}</div>
            <div class="stat-lbl">Trades</div>
        </div>
        <div class="stat">
            <div class="stat-val green">{{ wins }}</div>
            <div class="stat-lbl">Wins</div>
        </div>
        <div class="stat">
            <div class="stat-val red">{{ losses }}</div>
            <div class="stat-lbl">Losses</div>
        </div>
        <div class="stat">
            <div class="stat-val yellow">{{ win_rate }}%</div>
            <div class="stat-lbl">Win Rate</div>
        </div>
    </div>

    <!-- Open Positions -->
    <div class="card">
        <h3 class="blue">📈 Open Positions</h3>
        {% if positions %}
        <table>
            <tr>
                <th>Symbol</th>
                <th>Entry</th>
                <th>SL</th>
                <th>Target</th>
                <th>Qty</th>
            </tr>
            {% for sym, pos in positions.items() %}
            <tr>
                <td><b>{{ sym }}</b></td>
                <td>₹{{ pos.entry_price }}</td>
                <td class="red">₹{{ pos.stop_loss }}</td>
                <td class="green">₹{{ pos.target }}</td>
                <td>{{ pos.quantity }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p class="yellow">No open positions</p>
        {% endif %}
    </div>

    <!-- Trade History -->
    <div class="card">
        <h3 class="blue">📋 Recent Trades</h3>
        <table>
            <tr>
                <th>Type</th>
                <th>Symbol</th>
                <th>Price</th>
                <th>PnL</th>
                <th>Time</th>
            </tr>
            {% for t in trades[-10:]|reverse %}
            <tr>
                <td>
                    <span class="badge {{ t.type|lower }}">
                        {{ t.type }}
                    </span>
                </td>
                <td><b>{{ t.symbol }}</b></td>
                <td>₹{{ t.price }}</td>
                <td class="{{ 'green' if t.get('pnl', 0) > 0 else 'red' if t.get('pnl', 0) < 0 else '' }}">
                    {% if t.get('pnl') %}₹{{ t.pnl }}{% else %}-{% endif %}
                </td>
                <td style="font-size:11px">{{ t.time[11:19] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

</body>
</html>
"""

def get_data():
    try:
        with open("paper_trades.json") as f:
            acc = json.load(f)
    except:
        acc = {
            "capital": 100000,
            "trades": [],
            "open_positions": {}
        }

    trades = acc.get("trades", [])
    sells  = [t for t in trades if t["type"] == "SELL"]
    wins   = [t for t in sells if t.get("pnl", 0) > 0]
    pnl    = sum(t.get("pnl", 0) for t in sells)
    wr     = round(len(wins)/len(sells)*100) if sells else 0

    return {
        "capital"     : round(acc["capital"], 2),
        "pnl"         : round(pnl, 2),
        "total_trades": len(sells),
        "wins"        : len(wins),
        "losses"      : len(sells) - len(wins),
        "win_rate"    : wr,
        "positions"   : acc.get("open_positions", {}),
        "trades"      : trades,
        "time"        : datetime.now().strftime("%d %b %Y %H:%M:%S")
    }

@app.route("/")
def index():
    data = get_data()
    return render_template_string(HTML, **data)

if __name__ == "__main__":
    print("🌐 Dashboard: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
