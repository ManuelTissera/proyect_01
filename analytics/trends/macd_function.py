"""Optimised version focused on PriceStreaks
================================================
Only the logic strictly needed to compute PriceStreaks is kept; everything
else was removed.  The public entry-point is `compute_price_streaks`, which
returns **one single dict** called *DataInfo* containing:
    - PriceStreaks  (exactly the same structure as before)
    - stats          (mean & std of MACD ±)
    - all runtime parameters (RSI refs, TP/SL, max_candles, startDate)

The numerical result is **bit-for-bit identical** to the original implementation
— it just runs quite a bit faster by relying on NumPy arrays and avoiding
DataFrame row-by-row access.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

__all__ = ["compute_price_streaks"]


def compute_price_streaks(
    df: pd.DataFrame,
    *,
    target: float = 500,
    limit: float = 500,
    max_candles: int = 350,
    rsi_ref_pos: int = 0,
    rsi_ref_neg: int = 0,
) -> Dict[str, object]:
    """Return a *DataInfo* dict with PriceStreaks & stats.

    Parameters
    ----------
    df : DataFrame (required columns: Date, MACD, MACD_Hist, RSI_14,
                    Open, High, Low, Close)
    target : float   Take-profit distance, in points.
    limit  : float   Stop-loss distance,   in points.
    max_candles : int  Horizon in candles for the simulation.
    rsi_ref_pos  : int  RSI threshold for bullish MACD samples (0 ⇒ no filter).
    rsi_ref_neg  : int  RSI threshold for bearish MACD samples (0 ⇒ no filter).
    """
    # ------------------------------------------------------------------
    # Fast column access ------------------------------------------------
    if not np.issubdtype(df["Date"].dtype, np.datetime64):
        df = df.copy()
        df["Date"] = pd.to_datetime(df["Date"])

    macd = df["MACD"].to_numpy(float)
    rsi = df["RSI_14"].to_numpy(float)
    macd_hist = df["MACD_Hist"].to_numpy(float)
    open_p, high_p, low_p, close_p = (
        df[c].to_numpy(float) for c in ("Open", "High", "Low", "Close")
    )
    dates = df["Date"].astype(str).to_numpy()

    # ------------------------------------------------------------------
    # Stats -------------------------------------------------------------
    mask_pos = macd > 0
    mask_neg = macd < 0
    if rsi_ref_pos > 0:
        mask_pos &= rsi > rsi_ref_pos
    if rsi_ref_neg > 0:
        mask_neg &= rsi < rsi_ref_neg

    macd_pos, macd_neg = macd[mask_pos], macd[mask_neg]
    mean_macd_pos = float(np.nanmean(macd_pos)) if macd_pos.size else 0.0
    mean_macd_neg = float(np.nanmean(macd_neg)) if macd_neg.size else 0.0

    stats = {
        "mean_macd_pos": round(mean_macd_pos, 4),
        "std_macd_pos": round(float(np.nanstd(macd_pos)), 4),
        "mean_macd_neg": round(mean_macd_neg, 4),
        "std_macd_neg": round(float(np.nanstd(macd_neg)), 4),
    }

    # ------------------------------------------------------------------
    # Helpers -----------------------------------------------------------
    def _detect_streaks(
        side: str, zone: str, mean_value: float, direction: str
    ) -> List[Dict[str, int]]:
        """Return StartIdx / EndIdx pairs for each valid MACD streak."""
        idxs = np.flatnonzero(~np.isnan(macd))
        res: List[Dict[str, int]] = []
        i, n = 0, idxs.size

        def _side_ok(v: float) -> bool:
            return (side == "Negative" and v < 0) or (side == "Positive" and v > 0)

        def _zone_ok(v: float) -> bool:
            return (zone == "Lower" and v < mean_value) or (
                zone == "Higher" and v >= mean_value
            )

        while i < n:
            idx = idxs[i]
            val = macd[idx]
            if not (_side_ok(val) and _zone_ok(val)):
                i += 1
                continue

            last_val, j, valid = val, i + 1, False
            while j < n:
                idx_j = idxs[j]
                nxt = macd[idx_j]
                if (direction == "ascending" and nxt <= last_val) or (
                    direction == "descending" and nxt >= last_val
                ):
                    break
                last_val = nxt
                if (side == "Negative" and nxt >= 0) or (
                    side == "Positive" and nxt <= 0
                ):
                    valid = True
                    break
                j += 1
            if valid:
                res.append({"StartIdx": idx, "EndIdx": idxs[j]})
                i = j + 1
            else:
                i += 1
        return res

    # Build the four streak families -----------------------------------
    streaks_neg_lower = _detect_streaks("Negative", "Lower", mean_macd_neg, "ascending")
    streaks_neg_higher = _detect_streaks("Negative", "Higher", mean_macd_neg, "ascending")
    streaks_pos_lower = _detect_streaks("Positive", "Lower", mean_macd_pos, "descending")
    streaks_pos_higher = _detect_streaks("Positive", "Higher", mean_macd_pos, "descending")

    # ------------------------------------------------------------------
    # Price simulation --------------------------------------------------
    def _sim(streaks: List[Dict[str, int]], mode: str) -> Dict[str, list]:
        out = {"ObjectiveProfit": [], "LimitLoss": [], "NoResult": []}
        is_buy = mode == "buy"
        for s in streaks:
            start, end = s["StartIdx"], s["EndIdx"]
            for i in range(start + 1, end):
                crossed = (
                    macd_hist[i - 1] < 0 and macd_hist[i] >= 0
                    if is_buy
                    else macd_hist[i - 1] > 0 and macd_hist[i] <= 0
                )
                if not crossed:
                    continue

                entry_price = open_p[i]
                tp, sl = (
                    (entry_price + target, entry_price - limit)
                    if is_buy
                    else (entry_price - target, entry_price + limit)
                )
                rec = {
                    "From": str(dates[i]),
                    "StartValue": float(entry_price),
                    "MACD_Hist_Cross_Date": str(dates[i]),
                    "MACD_Hist_Cross_Idx": int(i),
                    "RSI_14": float(rsi[i]),
                }

                hit, last = False, min(i + max_candles, len(df) - 1)
                for j in range(i + 1, last + 1):
                    if is_buy:
                        if low_p[j] <= sl:
                            rec.update(
                                {"To": str(dates[j]), "EndValue": float(close_p[j]), "Result": "Limit"}
                            )
                            out["LimitLoss"].append(rec)
                            hit = True
                            break
                        if high_p[j] >= tp:
                            rec.update(
                                {"To": str(dates[j]), "EndValue": float(close_p[j]), "Result": "Objective"}
                            )
                            out["ObjectiveProfit"].append(rec)
                            hit = True
                            break
                    else:  # sell
                        if high_p[j] >= sl:
                            rec.update(
                                {"To": str(dates[j]), "EndValue": float(close_p[j]), "Result": "Limit"}
                            )
                            out["LimitLoss"].append(rec)
                            hit = True
                            break
                        if low_p[j] <= tp:
                            rec.update(
                                {"To": str(dates[j]), "EndValue": float(close_p[j]), "Result": "Objective"}
                            )
                            out["ObjectiveProfit"].append(rec)
                            hit = True
                            break
                if not hit:
                    rec.update(
                        {"To": str(dates[last]), "EndValue": float(close_p[last]), "Result": "NoResult"}
                    )
                    out["NoResult"].append(rec)
        return out

    price_streaks = {
        "Negative_Lower": _sim(streaks_neg_lower, "buy"),
        "Negative_Higher": _sim(streaks_neg_higher, "buy"),
        "Positive_Lower": _sim(streaks_pos_lower, "sell"),
        "Positive_Higher": _sim(streaks_pos_higher, "sell"),
    }

    # ------------------------------------------------------------------
    # Final package -----------------------------------------------------
    data_info = {
        "PriceStreaks": price_streaks,
        "stats": stats,
        "RSI_reference_positive": rsi_ref_pos,
        "RSI_reference_negative": rsi_ref_neg,
        "target": target,
        "limit": limit,
        "max_candles": max_candles,
        "startDate": int(df["Date"].dt.year.min()),
    }
    return data_info
