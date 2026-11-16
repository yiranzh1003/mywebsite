"""Compare the classroom model, a tuned model, and benchmarks."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parent
TEST_START = pd.Timestamp("2024-01-01")
VALIDATION_START = pd.Timestamp("2023-07-01")
END = pd.Timestamp("2026-11-13")
SIGNAL_TO_ENTRY = 1
SIGNAL_TO_EXIT = 20
HOLD = SIGNAL_TO_EXIT - SIGNAL_TO_ENTRY
COST = 0.001
CAP = 0.15
RAW = ["open", "high", "low", "close", "volume", "adjusted"]
FEATURES = RAW + ["return", "spy_ret", "mom_1m", "mom_3m", "mom_6m",
                  "vol_1m", "ret_5d", "excess_ret"]


def make_panel(price_file):
    data = pd.read_csv(price_file, parse_dates=["date"], usecols=["symbol", "date", *RAW])
    data = data[data.date.between("2022-01-01", END)]
    symbols = (ROOT / "data/tickers.txt").read_text().split()
    missing = set(symbols) - set(data.symbol)
    if missing:
        raise ValueError(f"Missing tickers: {sorted(missing)}")
    data = data[data.symbol.isin(symbols)].set_index(["date", "symbol"]).sort_index()
    spy = data.xs("SPY", level="symbol").adjusted.dropna()
    if spy.index.min() > pd.Timestamp("2022-01-04") or spy.index.max() != END:
        raise ValueError("SPY prices must cover the full specified range, through November 13, 2026.")
    if not spy.index.is_unique or (spy <= 0).any():
        raise ValueError("Invalid SPY data.")
    calendar = spy.index
    calendar_series = pd.Series(calendar, index=calendar)
    price_matrix = data.adjusted.unstack("symbol").reindex(calendar)
    panel = []
    for symbol in symbols:
        if symbol == "SPY":
            continue
        frame = data.xs(symbol, level="symbol").reindex(calendar).copy()
        adj = frame.adjusted
        frame["symbol"] = symbol
        frame["return"] = adj / adj.shift(1) - 1
        frame["spy_ret"] = spy / spy.shift(1) - 1
        for name, lag in [("mom_1m", 21), ("mom_3m", 63),
                          ("mom_6m", 126), ("ret_5d", 5)]:
            frame[name] = adj.shift(lag) / adj.shift(1) - 1
        frame["vol_1m"] = frame["return"].shift(1).rolling(22).std()
        frame["excess_ret"] = frame["return"] - frame["spy_ret"]
        frame["label_end"] = calendar_series.shift(-SIGNAL_TO_EXIT)
        frame["target"] = adj.shift(-SIGNAL_TO_EXIT) / adj.shift(-SIGNAL_TO_ENTRY) - 1
        panel.append(frame.reset_index())
    combined = pd.concat(panel, ignore_index=True)
    return combined.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURES), price_matrix


def fit_predict(train, rows, depth):
    model = XGBRegressor(n_estimators=300, max_depth=depth, learning_rate=0.05,
                         min_child_weight=10, gamma=0, random_state=123, n_jobs=4,
                         objective="reg:squarederror", tree_method="hist")
    model.fit(train[FEATURES], train.target)
    return model.predict(rows[FEATURES])


def format_pct(value):
    return f"{value:.2%}"


def rmse(actual, predicted):
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def allocation(scores, cap=None):
    selected = scores.nlargest(10).astype(float).clip(lower=0)
    if selected.empty:
        raise ValueError("No eligible stock on a scheduled signal date.")
    desired = selected / selected.sum() if selected.sum() else selected * 0 + 1 / len(selected)
    if cap is None:
        return desired
    # Excess allocation stays in zero-interest cash.
    return desired.clip(upper=cap)


def evaluate(predictions, prices):
    idx = prices.index
    first = idx.searchsorted(TEST_START)
    nav = dict.fromkeys(["Classroom XGBoost", "Tuned XGBoost", "Tuned + 15% cap", "SPY"], 1.0)
    previous = {key: pd.Series(dtype=float) for key in nav}
    rows, trades = [], []
    for k in range(first, len(idx) - SIGNAL_TO_EXIT, HOLD):
        signal, entry, exit_date = idx[k], idx[k + SIGNAL_TO_ENTRY], idx[k + SIGNAL_TO_EXIT]
        signals = predictions.loc[predictions.date.eq(signal)].set_index("symbol")
        positions = {
            "Classroom XGBoost": allocation(signals["Classroom XGBoost"]),
            "Tuned XGBoost": allocation(signals["Tuned XGBoost"]),
            "Tuned + 15% cap": allocation(signals["Tuned XGBoost"], CAP),
            "SPY": pd.Series({"SPY": 1.0}),
        }
        if not rows:
            rows.append({"date": entry, **nav})
        for key, weights in positions.items():
            weights = weights[weights.gt(0)]
            assert weights.sum() <= 1 + 1e-10
            gross = prices.loc[exit_date, weights.index] / prices.loc[entry, weights.index]
            if gross.isna().any() or (gross <= 0).any() or np.isinf(gross).any():
                raise ValueError(f"Missing executable price for {key} over {entry.date()}–{exit_date.date()}.")
            turnover = weights.subtract(previous[key], fill_value=0).abs().sum()
            wealth_factor = 1 - weights.sum() + (weights * gross).sum()
            nav[key] *= (1 - COST * turnover) * wealth_factor
            previous[key] = weights * gross / wealth_factor
            trades.append({"signal": signal, "entry": entry, "exit": exit_date,
                           "strategy": key, "stock_weight": weights.sum(),
                           "max_weight": weights.max() if len(weights) else 0,
                           "turnover": turnover})
        rows.append({"date": exit_date, **nav})
    if len(rows) < 3:
        raise ValueError("Insufficient backtest history.")
    return pd.DataFrame(rows).set_index("date"), pd.DataFrame(trades)


def main():
    panel, prices = make_panel(ROOT / "data/prices.csv")
    labeled = panel.dropna(subset=["target", "label_end"])
    early = labeled[labeled.label_end.lt(VALIDATION_START)]
    validation = labeled[labeled.date.ge(VALIDATION_START) & labeled.label_end.lt(TEST_START)]
    train = labeled[labeled.label_end.lt(TEST_START)]
    test = panel[panel.date.ge(TEST_START)].copy()
    if any(frame.empty for frame in [early, validation, train, test]):
        raise ValueError("Training, validation, or test set is empty.")
    depth_scores = {depth: rmse(validation.target, fit_predict(early, validation, depth))
                    for depth in [1, 2, 3, 5]}
    best = min((1, 2, 3), key=depth_scores.get)
    test["Classroom XGBoost"] = fit_predict(train, test, 5)
    test["Tuned XGBoost"] = fit_predict(train, test, best)
    test["Historical mean"] = train.target.mean()
    scored = test.dropna(subset=["target"])
    metrics = {name: rmse(scored.target, scored[name])
               for name in ["Historical mean", "Classroom XGBoost", "Tuned XGBoost"]}
    nav, trades = evaluate(test, prices)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    nav.to_csv(out / "wealth.csv")
    trades.to_csv(out / "rebalances.csv", index=False)
    pd.Series(depth_scores, name="validation_rmse").to_csv(out / "validation.csv")
    summary = pd.DataFrame({"RMSE": pd.Series(metrics), "Net return": nav.iloc[-1] - 1,
                            "Max drawdown at rebalances": (nav / nav.cummax() - 1).min()})
    summary.to_csv(out / "summary.csv")
    ax = nav.plot(figsize=(9, 4.6), color=["#006768", "#ca5730", "#803d8d", "#52647a"])
    ax.set(xlabel="", ylabel="Value of $1", title="Growth of $1 in the backtest")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.22)
    ax.figure.savefig(out / "wealth.png", dpi=180, bbox_inches="tight")
    plt.close(ax.figure)
    table = ["| Model | Out-of-sample RMSE |", "|---|---:|"]
    table += [f"| {name} | {format_pct(value)} |" for name, value in metrics.items()]
    period = f"{nav.index[0]:%b %d, %Y} to {nav.index[-1]:%b %d, %Y}"
    forecast = (
        f"Among the shallower alternatives, depth {best} had the lowest validation error. "
        f"The model with the lowest forecast error on the test data was "
        f"**{min(metrics, key=metrics.get)}**.\n\n" + "\n".join(table)
    )
    totals = nav.iloc[-1] - 1
    drawdowns = (nav / nav.cummax() - 1).min()
    performance = (
        f"From {period}, $1 earned **{format_pct(totals['Classroom XGBoost'])}** "
        f"with the classroom model, **{format_pct(totals['Tuned XGBoost'])}** with the tuned model, "
        f"and **{format_pct(totals['SPY'])}** with SPY after the assumed trading costs."
    )
    cap_text = (
        f"The same tuned predictions earned **{format_pct(totals['Tuned + 15% cap'])}** with the cap. "
        f"Measured at the end of each holding period, maximum drawdown was "
        f"**{format_pct(drawdowns['Tuned + 15% cap'])}** with the cap and "
        f"**{format_pct(drawdowns['Tuned XGBoost'])}** without it."
    )
    draft = (ROOT / "index.qmd").read_text(encoding="utf-8")
    for marker, value in {"FORECAST": forecast, "PERFORMANCE": performance,
                          "CAP": cap_text}.items():
        start, stop = f"<!-- BEGIN {marker} -->", f"<!-- END {marker} -->"
        before, rest = draft.split(start, 1)
        _, after = rest.split(stop, 1)
        draft = before + start + "\n" + value + "\n" + stop + after
    draft = draft.replace("<!-- WEALTH_FIGURE -->",
                          "![Growth of $1 after assumed trading costs](results/wealth.png)")
    (ROOT / "index.qmd").write_text(draft, encoding="utf-8")
    print(f"Validation selected depth {best}. Backtest: {period}.")
    print(summary.to_string())


if __name__ == "__main__":
    main()
