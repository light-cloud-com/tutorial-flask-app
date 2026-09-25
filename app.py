import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Shown next to every amount. Set CURRENCY on Light Cloud to change it.
CURRENCY = os.environ.get("CURRENCY", "$")


def split_bill(total: str, people: str, tip_percent: str) -> dict:
    """Validate the form values and return the split, or raise ValueError."""
    try:
        total_d = Decimal(total)
        people_n = int(people)
        tip_d = Decimal(tip_percent)
    except (InvalidOperation, ValueError):
        raise ValueError("Enter numbers only.")
    if total_d <= 0 or people_n < 1 or tip_d < 0:
        raise ValueError("The total and the number of people must be above zero.")

    cents = Decimal("0.01")
    tip = (total_d * tip_d / 100).quantize(cents, ROUND_HALF_UP)
    grand_total = total_d + tip
    each = (grand_total / people_n).quantize(cents, ROUND_HALF_UP)
    return {
        "total": str(total_d.quantize(cents)),
        "tip": str(tip),
        "grand_total": str(grand_total.quantize(cents)),
        "people": people_n,
        "each": str(each),
        "currency": CURRENCY,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    result, error = None, None
    form = {"total": "", "people": "2", "tip": "10"}
    if request.method == "POST":
        form = {key: request.form.get(key, "").strip() for key in form}
        try:
            result = split_bill(form["total"], form["people"], form["tip"])
        except ValueError as exc:
            error = str(exc)
            app.logger.warning("invalid input: %s", form)
    return render_template("index.html", form=form, result=result, error=error, currency=CURRENCY)


@app.get("/api/split")
def api_split():
    try:
        return jsonify(
            split_bill(
                request.args.get("total", ""),
                request.args.get("people", "1"),
                request.args.get("tip", "0"),
            )
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # Only for `python app.py` on your machine. Light Cloud runs gunicorn instead.
    app.run(debug=True)
