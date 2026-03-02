from app import create_app

app = create_app()

if __name__ == "__main__":
    # 0.0.0.0 pour être accessible depuis Docker
    app.run(host="0.0.0.0", port=5000)