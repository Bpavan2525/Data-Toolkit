import base64

from flask import Flask, render_template, request

from .core import clean, read_any, to_bytes

MAX_BYTES = 4 * 1024 * 1024  # Vercel's request body limit is about 4.5 MB


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES

    @app.errorhandler(413)
    def too_big(_):
        return render_template("index.html", error="That file is over 4 MB. Try a smaller one."), 413

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.post("/")
    def upload():
        f = request.files.get("file")
        sample = request.form.get("sample")
        try:
            if sample:
                with open(app.root_path + "/../samples/customers_messy.csv", "rb") as fh:
                    name, data = "customers_messy.csv", fh.read()
            elif f and f.filename:
                name, data = f.filename, f.read()
            else:
                return render_template("index.html", error="Choose a file first."), 400
            df = read_any(name, data)
            out, report = clean(df)
        except Exception as e:  # show the reason instead of a 500 page
            return render_template("index.html", error=f"Couldn't read that file: {e}"), 400
        fmt = request.form.get("format", "csv")
        fmt = "xlsx" if fmt == "xlsx" else "csv"
        payload = base64.b64encode(to_bytes(out, fmt)).decode()
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if fmt == "xlsx" else "text/csv"
        stem = name.rsplit(".", 1)[0]
        return render_template(
            "index.html",
            report=report.as_dict(),
            before=df.head(8).fillna("").to_html(index=False, classes="t"),
            after=out.head(8).fillna("").to_html(index=False, classes="t"),
            download=f"data:{mime};base64,{payload}",
            download_name=f"{stem}_clean.{fmt}",
        )

    return app
