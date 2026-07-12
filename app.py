from flask import Flask, render_template

app = Flask(__name__)

# Dados da psicóloga — edite aqui para atualizar o site sem mexer no HTML
CONTEXT = {
    "nome": "Julia Monteiro",
    "crp": "CRP 08/47211",
    "instagram_handle": "psi_juliamonteiro",
    "instagram_url": "https://instagram.com/psi_juliamonteiro",
    "whatsapp_numero": "554184137113",
    "whatsapp_mensagem": "Olá, Julia! Vim pelo Instagram e gostaria de saber mais sobre as sessões online.",
}

CONTEXT["whatsapp_url"] = (
    f"https://wa.me/{CONTEXT['whatsapp_numero']}"
    f"?text={CONTEXT['whatsapp_mensagem'].replace(' ', '%20')}"
)


@app.route("/")
def home():
    return render_template("index.html", **CONTEXT)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
