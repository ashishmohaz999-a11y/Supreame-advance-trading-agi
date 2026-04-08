import torch
import torch.nn as nn
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

class LSTMModel(nn.Module):
    """
    LSTM Neural Network
    - Input  : 60 days price history
    - Output : Kal ka price prediction
    - Layers : 2 LSTM + 1 Dense
    """
    def __init__(self, input_size=1, hidden=64, layers=2):
        super(LSTMModel, self).__init__()
        self.hidden = hidden
        self.layers = layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden,
            num_layers=layers,
            batch_first=True,
            dropout=0.2
        )
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x):
        h0 = torch.zeros(self.layers, x.size(0), self.hidden)
        c0 = torch.zeros(self.layers, x.size(0), self.hidden)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :])

def prepare_data(prices, seq_len=60):
    """
    Price list ko LSTM input format mein convert karo
    seq_len = kitne din ka data ek baar dekhe
    """
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(
        np.array(prices).reshape(-1, 1)
    )
    X, y = [], []
    for i in range(seq_len, len(scaled)):
        X.append(scaled[i-seq_len:i])
        y.append(scaled[i])
    return (
        torch.FloatTensor(np.array(X)),
        torch.FloatTensor(np.array(y)),
        scaler
    )

def train_model(prices, epochs=50, seq_len=60):
    """
    Model ko train karo price history se
    epochs = kitni baar data dekhe
    """
    if len(prices) < seq_len + 10:
        print("❌ Data kam hai training ke liye")
        return None, None

    print(f"🧠 Training LSTM...")
    print(f"   Data points : {len(prices)}")
    print(f"   Epochs      : {epochs}")

    X, y, scaler = prepare_data(prices, seq_len)

    model = LSTMModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(X)
        loss = criterion(output, y)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"   Epoch {epoch+1}/{epochs} | Loss: {loss.item():.6f}")

    # Model save karo
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), "models/lstm_model.pth")
    print("✅ Model saved: models/lstm_model.pth")

    return model, scaler

def predict_next(model, scaler, prices, seq_len=60):
    """
    Kal ka price predict karo
    Returns: predicted price aur signal
    """
    if len(prices) < seq_len:
        return None, "HOLD"

    model.eval()
    with torch.no_grad():
        last_seq = np.array(prices[-seq_len:]).reshape(-1, 1)
        scaled   = scaler.transform(last_seq)
        x_input  = torch.FloatTensor(scaled).unsqueeze(0)
        pred     = model(x_input)
        predicted_price = scaler.inverse_transform(
            pred.numpy()
        )[0][0]

    current_price = prices[-1]
    change_pct = (predicted_price - current_price) / current_price * 100

    if change_pct > 1.0:
        signal = "BUY"
    elif change_pct < -1.0:
        signal = "SELL"
    else:
        signal = "HOLD"

    return round(predicted_price, 2), signal, round(change_pct, 2)

if __name__ == "__main__":
    import yfinance as yf

    print("📥 Downloading RELIANCE data...")
    ticker = yf.Ticker("RELIANCE.NS")
    hist   = ticker.history(period="1y")
    prices = hist["Close"].tolist()

    print(f"✅ Got {len(prices)} days data")

    # Train karo
    model, scaler = train_model(prices, epochs=50)

    if model and scaler:
        # Predict karo
        pred_price, signal, change = predict_next(
            model, scaler, prices
        )
        current = prices[-1]

        print(f"\n=== LSTM PREDICTION ===")
        print(f"Current Price : ₹{round(current, 2)}")
        print(f"Predicted     : ₹{pred_price}")
        print(f"Change        : {change}%")
        print(f"AI Signal     : {signal}")
