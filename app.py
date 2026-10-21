from flask import Flask, request, jsonify
import asyncio
import httpx
import os
from api2 import autoshopify

app = Flask(__name__)
app.json.sort_keys = False


def parse_proxy(p):
    if not p:
        return None
    p = p.strip()
    scheme = "http"
    if "://" in p:
        s = p.split("://", 1)
        if s[0].lower() in ("http", "https", "socks4", "socks5"):
            scheme = s[0].lower()
            p = s[1]
    if p.count(":") == 3:
        ip, port, user, pwd = p.split(":")
        p = f"{user}:{pwd}@{ip}:{port}"
    return f"{scheme}://{p}"


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "shopify-checker"})


@app.route("/shopify", methods=["GET"])
def shopify_check():
    site  = request.args.get("site", "").strip()
    cc    = request.args.get("cc", "").strip()
    proxy = request.args.get("proxy", "").strip()

    if not site:
        return jsonify({"Response": "site required", "Status": False}), 400
    if not cc:
        return jsonify({"Response": "cc required", "Status": False}), 400

    proxy_url = parse_proxy(proxy)

    async def run():
        kw = {"timeout": 60, "follow_redirects": True}
        if proxy_url:
            kw["proxy"] = proxy_url
        async with httpx.AsyncClient(**kw) as session:
            return await autoshopify(site, cc, session)

    try:
        result = asyncio.run(run())
    except Exception as e:
        result = {"Response": f"{type(e).__name__}: {e}", "Status": False}

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True)
