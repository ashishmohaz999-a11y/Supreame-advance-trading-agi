import torch
import numpy as np
import os
from trading_system.lstm_model import (
    LSTMModel, predict_next,
    prepare_data, train_model
)
from sklearn.preprocessing import MinMaxScaler

MODEL_PATH  = "models/lstm_model.pth"
SCALER_PATH = "models/scaler.npy"

def get_ai_signal(prices):
    """
    LSTM se AI signal lo.
    Agar model nahi hai to pehle train karo.
    """
    if len(prices) < 60:
        return "HOLD", 0, 0

    try:
        # Model load ya train karo
        if os.path.exists(MODEL_PATH):
            model = LSTMModel()
            model.load_state_dict(
                torch.load(MODEL_PATH, 
                weights_only=True)
            )
            # Scaler dobara fit karo
            scaler = MinMaxScaler()
            data = np.array(prices).reshape(-1, 1)
            scaler.fit(data)
        else:
            print("🧠 Training new LSTM model...")
            model, scaler = train_model(prices)
            if not model:
                return "HOLD", 0, 0

        pred_price, signal, change = predict_next(
            model, scaler, prices
        )
        return signal, pred_price, change

    except Exception as e:
        print(f"❌ AI signal error: {e}")
        return "HOLD", 0, 0

if __name__ == "__main__":
    import yfinance as yf
    ticker = yf.Ticker("TCS.NS")
    hist   = ticker.history(period="1y")
    prices = hist["Close"].tolist()

    signal, pred, change = get_ai_signal(prices)
    print(f"\n=== AI SIGNAL ===")
    print(f"Signal    : {signal}")
    print(f"Predicted : ₹{pred}")
    print(f"Change    : {change}%")
