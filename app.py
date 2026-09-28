"""Site da psicóloga Julia Monteiro (Flask).

Rodar localmente:  uv run --with flask python app.py   ->  http://localhost:5000

TUDO o que identifica a Julia (nome, CRP, @, WhatsApp) e os IDs do Google Ads
fica no dicionário SITE logo abaixo. As páginas ficam na lista PAGES.
ATENÇÃO: push na branch main do GitHub = deploy automático no Vercel.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
from pathlib import Path

from flask import (
    Flask,
    Response,
    g,
    render_template,
    request,
    send_from_directory,
    url_for,
)

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)

# ---------------------------------------------------------------------------
# Dados do site — edite AQUI (não precisa mexer no HTML)
# ---------------------------------------------------------------------------
SITE = {
    # Identificação exigida pelo CFP (nome completo + CRP em toda divulgação).
    # PENDENTE: confirmar o nome completo registrado no CRP e trocar abaixo.
    "nome_completo": "Julia Monteiro",
    "nome_completo_confirmado": False,
    "crp": "CRP 08/47211",
    # PENDENTE: conferir o CRP no Cadastro Nacional do CFP.
    "crp_conferido_cfp": False,
    # O logo diz "@PSI.JULIAMONTEIRO" (ponto) e o link diz "psi_juliamonteiro"
    # (underline). Enquanto não for confirmado, o @ não entra no schema, na
    # imagem de compartilhamento nem nas páginas novas.
    "instagram_handle": "psi_juliamonteiro",
    "instagram_url": "https://instagram.com/psi_juliamonteiro",
    "instagram_confirmado": False,
    # WhatsApp: número exato do site no ar. A mensagem é a mesma em todas as
    # páginas e não cita o tema da página (privacidade).
    "whatsapp_numero": "554184137113",
    "whatsapp_mensagem": "Olá, Julia! Vim pelo site e gostaria de saber mais sobre as sessões online.",
    "base_url": "https://www.juliamonteiropsi.com.br",
    # Google Ads: os mesmos IDs que já rodam no site hoje. Deixe "" para
    # desligar a tag e a conversão.
    "google_ads_id": "AW-18383511999",
    "google_ads_label_whatsapp": "jHp7CKaLvPYcEL_D-L1E",
    # Só o dono muda para True, DEPOIS de desligar a coleta de remarketing na
    # conta do Google Ads. Libera a frase sobre remarketing na /privacidade.
    "remarketing_desligado_confirmado": False,
    # True = modo básico do consentimento no site inteiro (mais conservador).
    "modo_basico_em_todo_site": False,
    # False = sem aviso de cookies (alternativa mínima; ver README).
    "aviso_cookies_ativo": True,
    # Aviso "não é serviço de emergência" (188/192): entra após aprovação.
    "aviso_emergencia_aprovado": False,
    "hosts_producao": {"www.juliamonteiropsi.com.br", "juliamonteiropsi.com.br"},
    "ultima_atualizacao": "2026-09-26",
}

SITE["whatsapp_url"] = (
    "https://wa.me/"
    + SITE["whatsapp_numero"]
    + "?text="
    + urllib.parse.quote(SITE["whatsapp_mensagem"], safe="")
)

# ---------------------------------------------------------------------------
# Páginas. Títulos e metas usam {nome} e {crp}: trocar o nome em SITE já
# atualiza tudo. A meta sempre termina com "Psicóloga {nome}, {crp}."
#
# texto_aprovado=False -> a página responde 200 (links internos funcionam),
#   mas sai com noindex e fica fora do sitemap. Só vire True depois que a
#   Julia escrever/aprovar o texto próprio da página.
# pagina_saude=True -> modo básico do consentimento: nada vai ao Google antes
#   do "Aceitar" e, mesmo depois, o endereço enviado é genérico ("/tema").
# publicada=False -> a rota ainda não existe (404).
# ---------------------------------------------------------------------------
PAGES = [
    {
        "id": "home", "slug": "/", "template": "index.html", "tipo": "home",
        "title": "Psicóloga Online para Mulheres | {nome}",
        "meta_texto": "Atendimento psicológico online para mulheres, com abordagem sistêmica familiar. Sessões por videochamada.",
        "h1": "Psicoterapia online para mulheres, com abordagem sistêmica familiar",
        "breadcrumb": "Início", "servico": None,
        # Texto atual do site. PENDENTE: aprovação do novo H1 pela Julia.
        "texto_aprovado": True, "pagina_saude": False, "publicada": True,
    },
    {
        "id": "psicologa-online", "slug": "/psicologa-online", "template": "psicologa_online.html", "tipo": "tema",
        "title": "Psicóloga Online por Videochamada | {nome}",
        "meta_texto": "Psicoterapia 100% online por videochamada, em horário combinado, de onde for mais confortável.",
        "h1": "Psicóloga online: atendimento por videochamada",
        "breadcrumb": "Psicóloga online", "servico": "Psicoterapia online por videochamada",
        "texto_aprovado": False, "pagina_saude": False, "publicada": True,
    },
    {
        "id": "terapia-para-mulheres", "slug": "/terapia-para-mulheres", "template": "terapia_para_mulheres.html", "tipo": "tema",
        "title": "Terapia Online para Mulheres | Psicóloga {nome}",
        "meta_texto": "Um cuidado pensado para mulheres: relações, transições de vida, autoconhecimento, ansiedade e sobrecarga.",
        "h1": "Terapia online para mulheres",
        "breadcrumb": "Terapia para mulheres", "servico": "Terapia online para mulheres",
        "texto_aprovado": False, "pagina_saude": False, "publicada": True,
    },
    {
        "id": "terapia-sistemica", "slug": "/terapia-sistemica", "template": "terapia_sistemica.html", "tipo": "tema",
        "title": "Terapia Sistêmica Online | Psicóloga {nome}",
        "meta_texto": "Terapia que enxerga a pessoa dentro da sua rede de relações. Atendimento online com abordagem sistêmica familiar.",
        "h1": "Terapia online com abordagem sistêmica familiar",
        "breadcrumb": "Terapia sistêmica", "servico": "Terapia online com abordagem sistêmica familiar",
        "texto_aprovado": False, "pagina_saude": False, "publicada": True,
    },
    {
        "id": "ansiedade", "slug": "/ansiedade", "template": "ansiedade.html", "tipo": "tema",
        "title": "Terapia Online para Ansiedade | Psicóloga {nome}",
        "meta_texto": "Cuidado com a saúde mental de quem carrega múltiplos papéis no dia a dia. Psicoterapia online.",
        "h1": "Psicoterapia online para ansiedade e sobrecarga",
        "breadcrumb": "Ansiedade e sobrecarga", "servico": "Psicoterapia online para ansiedade e sobrecarga",
        "texto_aprovado": False, "pagina_saude": True, "publicada": True,
    },
    {
        "id": "relacionamentos", "slug": "/relacionamentos", "template": "relacionamentos.html", "tipo": "tema",
        "title": "Terapia para Relações e Vínculos | Psicóloga {nome}",
        "meta_texto": "Padrões em relacionamentos, conflitos familiares e dificuldade de colocar limites. Terapia online.",
        "h1": "Terapia online para relações e vínculos",
        "breadcrumb": "Relações e vínculos", "servico": "Terapia online para relações e vínculos",
        "texto_aprovado": False, "pagina_saude": True, "publicada": True,
    },
    {
        "id": "transicoes-de-vida", "slug": "/transicoes-de-vida", "template": "transicoes_de_vida.html", "tipo": "tema",
        "title": "Terapia para Transições de Vida | Psicóloga {nome}",
        "meta_texto": "Maternidade, mudança de carreira, luto, término de ciclos e novos começos. Terapia online para mulheres.",
        "h1": "Terapia online para transições de vida",
        "breadcrumb": "Transições de vida", "servico": "Terapia online para transições de vida",
        "texto_aprovado": False, "pagina_saude": True, "publicada": True,
    },
    {
        # CRIAR SÓ QUANDO a Julia escrever o texto: preencher o bloco
        # texto_proprio do template e mudar publicada=True.
        "id": "maternidade", "slug": "/transicoes-de-vida/maternidade", "template": "maternidade.html", "tipo": "tema",
        "pai": "/transicoes-de-vida",
        "title": "Terapia Online e Maternidade | Psicóloga {nome}",
        "meta_texto": "Terapia online para mulheres na maternidade, com abordagem sistêmica familiar.",
        "h1": "Terapia online na maternidade",
        "breadcrumb": "Maternidade", "servico": "Terapia online na maternidade",
        "texto_aprovado": False, "pagina_saude": True, "publicada": False,
    },
    {
        "id": "luto", "slug": "/transicoes-de-vida/luto", "template": "luto.html", "tipo": "tema",
        "pai": "/transicoes-de-vida",
        "title": "Terapia Online no Luto | Psicóloga {nome}",
        "meta_texto": "Psicoterapia online para mulheres no luto, com abordagem sistêmica familiar.",
        "h1": "Psicoterapia online no luto",
        "breadcrumb": "Luto", "servico": "Psicoterapia online no luto",
        "texto_aprovado": False, "pagina_saude": True, "publicada": False,
    },
    {
        "id": "autoconhecimento", "slug": "/autoconhecimento", "template": "autoconhecimento.html", "tipo": "tema",
        "title": "Terapia para Autoconhecimento | Psicóloga {nome}",
        "meta_texto": "Entender a sua história para viver o presente com mais autonomia emocional. Psicoterapia online para mulheres.",
        "h1": "Terapia online para autoconhecimento",
        "breadcrumb": "Autoconhecimento", "servico": "Terapia online para autoconhecimento",
        "texto_aprovado": False, "pagina_saude": True, "publicada": True,
    },
    {
        "id": "sobre", "slug": "/sobre", "template": "sobre.html", "tipo": "institucional",
        "title": "Sobre {nome}, Psicóloga | {crp}",
        "meta_texto": "Pós-graduanda em Terapia Familiar Sistêmica, com atendimento psicológico online para mulheres.",
        "h1": "Sobre {nome}, psicóloga ({crp})",
        "breadcrumb": "Sobre a Julia", "servico": None,
        "texto_aprovado": False, "pagina_saude": False, "publicada": True,
    },
    {
        "id": "como-funciona", "slug": "/como-funciona", "template": "como_funciona.html", "tipo": "institucional",
        "title": "Como Funciona a Terapia Online | Psicóloga {nome}",
        "meta_texto": "Sessões por videochamada em horário combinado: envie uma mensagem e agende a primeira sessão.",
        "h1": "Como funciona a terapia online",
        "breadcrumb": "Como funciona", "servico": None,
        "texto_aprovado": False, "pagina_saude": False, "publicada": True,
    },
    {
        "id": "contato", "slug": "/contato", "template": "contato.html", "tipo": "institucional",
        "title": "Contato pelo WhatsApp | Psicóloga {nome}",
        "meta_texto": "Tire dúvidas ou agende sua primeira sessão online pelo WhatsApp.",
        "h1": "Contato: vamos conversar?",
        "breadcrumb": "Contato", "servico": None,
        "texto_aprovado": False, "pagina_saude": False, "publicada": True,
    },
    {
        "id": "privacidade", "slug": "/privacidade", "template": "privacidade.html", "tipo": "institucional",
        "title": "Política de Privacidade | {nome}, Psicóloga",
        "meta_texto": "Como este site trata dados pessoais: cookies, contato pelo WhatsApp e medição de anúncios do Google.",
        "h1": "Política de privacidade",
        "breadcrumb": "Privacidade", "servico": None,
        "texto_aprovado": False, "pagina_saude": False, "publicada": True,
    },
]

PAGINA_404 = {
    "id": "404", "slug": None, "template": "404.html", "tipo": "erro",
    "title": "Página não encontrada | Psicóloga {nome}",
    "meta_texto": "O endereço procurado não existe neste site.",
    "h1": "Página não encontrada", "breadcrumb": None, "servico": None,
    # URL desconhecida: tratada como página de saúde (modo básico), por cautela.
    "texto_aprovado": False, "pagina_saude": True, "publicada": True,
}

PAGINAS_POR_SLUG = {p["slug"]: p for p in PAGES}

# Os 4 temas do site (seção "Para quem é"), texto exato do site.
TEMAS_CARDS = [
    {"titulo": "Relações e vínculos", "href": "/relacionamentos",
     "texto": "Padrões repetidos em relacionamentos, conflitos familiares e dificuldade de colocar limites."},
    {"titulo": "Transições de vida", "href": "/transicoes-de-vida",
     "texto": "Maternidade, mudanças de carreira, luto, término de ciclos e novos começos."},
    {"titulo": "Autoconhecimento", "href": "/autoconhecimento",
     "texto": "Entender sua história para viver o presente com mais autonomia emocional."},
    {"titulo": "Ansiedade e sobrecarga", "href": "/ansiedade",
     "texto": "Cuidado com a saúde mental de quem carrega múltiplos papéis no dia a dia."},
]

# FAQ de /como-funciona: só com o que já está no site.
# PENDENTE: aprovação da Julia (o FAQPage do schema só sai com texto_aprovado).
FAQ_COMO_FUNCIONA = [
    {"pergunta": "O atendimento é presencial?",
     "resposta": "Não. O atendimento é 100% online: as sessões acontecem por videochamada, em um horário combinado semanalmente, de onde for mais confortável para você."},
    {"pergunta": "Como é a primeira sessão?",
     "resposta": "A primeira sessão é para nos conhecermos. Depois dela, definimos juntas a frequência e o formato do acompanhamento."},
    {"pergunta": "Com que frequência são as sessões?",
     "resposta": "As sessões acontecem em um horário combinado semanalmente. A frequência e o formato do acompanhamento são definidos juntas."},
    {"pergunta": "Como faço para agendar?",
     "resposta": "Pelo WhatsApp: é só enviar uma mensagem para tirar dúvidas ou agendar a primeira sessão."},
    {"pergunta": "Para quem é o atendimento?",
     "resposta": "É um cuidado pensado para mulheres, com abordagem sistêmica familiar: relações e vínculos, transições de vida, autoconhecimento, ansiedade e sobrecarga."},
]

KNOWS_ABOUT = [
    "Psicoterapia online para mulheres",
    "Relações e vínculos",
    "Transições de vida",
    "Autoconhecimento",
    "Ansiedade e sobrecarga",
    "Abordagem sistêmica familiar",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fmt(texto: str) -> str:
    return texto.format(nome=SITE["nome_completo"], crp=SITE["crp"])


def identificacao_meta() -> str:
    return f"Psicóloga {SITE['nome_completo']}, {SITE['crp']}."


def page_title(pagina) -> str:
    return fmt(pagina["title"])


def page_meta(pagina) -> str:
    return f"{pagina['meta_texto']} {identificacao_meta()}"


def page_h1(pagina) -> str:
    return fmt(pagina["h1"])


def paginas_publicadas():
    return [p for p in PAGES if p["publicada"]]


def paginas_indexaveis():
    return [p for p in PAGES if p["publicada"] and p["texto_aprovado"]]


def caminhos_saude():
    return [p["slug"] for p in PAGES if p["pagina_saude"]]


def host_publico() -> str:
    """Host que o visitante digitou: 1º valor de X-Forwarded-Host (Vercel),
    em minúsculas e sem porta; se não houver, o Host da requisição."""
    bruto = request.headers.get("X-Forwarded-Host", "") or request.host or ""
    host = bruto.split(",")[0].strip().lower()
    if host.startswith("["):  # IPv6 [::1]:5000
        return host.split("]")[0] + "]"
    return host.split(":")[0]


def eh_producao() -> bool:
    return host_publico() in SITE["hosts_producao"]


def eh_local() -> bool:
    h = host_publico()
    return h in {"localhost", "127.0.0.1", "[::1]"} or h.endswith(".localhost") or h.endswith(".test")


_hash_cache: dict[str, str] = {}


def static_v(filename: str) -> str:
    """URL de /static com ?v=<hash curto do conteúdo> (cache longo e seguro)."""
    if app.debug or filename not in _hash_cache:
        caminho = BASE_DIR / "static" / filename
        _hash_cache[filename] = hashlib.md5(caminho.read_bytes()).hexdigest()[:10]
    return url_for("static", filename=filename, v=_hash_cache[filename])


def modo_consentimento(pagina) -> str:
    if pagina["pagina_saude"] or SITE["modo_basico_em_todo_site"]:
        return "basico"
    return "avancado"


def montar_schema(pagina) -> str | None:
    """JSON-LD em @graph. A entidade principal é a PESSOA (Julia).
    Nenhum nó representa a prática dela como organização/estabelecimento:
    o único Organization é o emissor do CRP, dentro de hasCredential."""
    if pagina["tipo"] == "erro":
        return None
    base = SITE["base_url"]
    julia_id = base + "/#julia"
    pessoa = {
        "@type": "Person",
        "@id": julia_id,
        "name": SITE["nome_completo"],
        "jobTitle": "Psicóloga",
        "url": base + "/sobre",
        "image": base + "/static/img/julia-sobre-800.jpg",
        "hasCredential": {
            "@type": "EducationalOccupationalCredential",
            "name": SITE["crp"],
            "credentialCategory": "Registro profissional",
            "recognizedBy": {
                "@type": "Organization",
                "name": "Conselho Regional de Psicologia da 8ª Região (Paraná)",
            },
        },
        "knowsAbout": KNOWS_ABOUT,
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "agendamento",
            "url": SITE["whatsapp_url"],
        },
    }
    if SITE["instagram_confirmado"]:
        pessoa["sameAs"] = [SITE["instagram_url"]]

    graph = [
        {
            "@type": "WebSite",
            "@id": base + "/#website",
            "url": base + "/",
            "name": f"{SITE['nome_completo']}, psicóloga",
            "inLanguage": "pt-BR",
            "publisher": {"@id": julia_id},
        },
        pessoa,
    ]
    url = base + pagina["slug"]
    if pagina["tipo"] == "tema" and pagina["texto_aprovado"] and pagina["servico"]:
        graph.append({
            "@type": "Service",
            "@id": url + "#servico",
            "name": pagina["servico"],
            "serviceType": "Psicoterapia",
            "url": url,
            "provider": {"@id": julia_id},
            "audience": {"@type": "PeopleAudience", "suggestedGender": "female"},
            "availableChannel": {"@type": "ServiceChannel", "serviceUrl": SITE["whatsapp_url"]},
        })
    if pagina["slug"] != "/" and pagina["texto_aprovado"]:
        itens = [{"@type": "ListItem", "position": 1, "name": "Início", "item": base + "/"}]
        pai = PAGINAS_POR_SLUG.get(pagina.get("pai"))
        if pai:
            itens.append({"@type": "ListItem", "position": 2, "name": pai["breadcrumb"], "item": base + pai["slug"]})
        itens.append({"@type": "ListItem", "position": len(itens) + 1, "name": pagina["breadcrumb"], "item": url})
        graph.append({"@type": "BreadcrumbList", "itemListElement": itens})
    if pagina["id"] == "como-funciona" and pagina["texto_aprovado"]:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": f["pergunta"],
                 "acceptedAnswer": {"@type": "Answer", "text": f["resposta"]}}
                for f in FAQ_COMO_FUNCIONA
            ],
        })
    dados = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(dados, ensure_ascii=False, indent=1).replace("</", "<\\/")


def nav_itens(pagina):
    if pagina["id"] == "home":
        return [
            {"label": "Sobre", "href": "#sobre", "secao": "sobre"},
            {"label": "Para quem é", "href": "#para-quem", "secao": "para-quem"},
            {"label": "Como funciona", "href": "#atendimento", "secao": "atendimento"},
            {"label": "Contato", "href": "#contato", "secao": "contato"},
        ]
    itens = [
        {"label": "Sobre", "href": "/sobre"},
        {"label": "Para quem é", "href": "/terapia-para-mulheres"},
        {"label": "Como funciona", "href": "/como-funciona"},
        {"label": "Contato", "href": "/contato"},
    ]
    for item in itens:
        item["atual"] = item["href"] == pagina["slug"]
    return itens


@app.context_processor
def contexto_global():
    pagina = getattr(g, "pagina", None) or PAGINA_404
    producao = eh_producao()
    canonical = SITE["base_url"] + pagina["slug"] if pagina["slug"] else None
    temas = [p for p in PAGES if p["tipo"] == "tema" and p["publicada"] and not p.get("pai")]
    return {
        "site": SITE,
        "whatsapp_url": SITE["whatsapp_url"],
        "pagina": pagina,
        "page_title": page_title(pagina),
        "page_meta": page_meta(pagina),
        "page_h1": page_h1(pagina),
        "canonical": canonical,
        "robots_meta": "index,follow" if pagina["texto_aprovado"] else "noindex,follow",
        "is_producao": producao,
        "is_local": eh_local(),
        "ocultar_rascunhos": os.environ.get("OCULTAR_RASCUNHOS") == "1",
        "modo_consentimento": modo_consentimento(pagina),
        "caminhos_saude": caminhos_saude(),
        "google_ads_id": SITE["google_ads_id"] if producao else "",
        "google_ads_label_whatsapp": SITE["google_ads_label_whatsapp"] if producao else "",
        "schema_json": montar_schema(pagina),
        "nav_itens": nav_itens(pagina),
        "temas": temas,
        "temas_aprovados": [p for p in temas if p["texto_aprovado"]],
        "temas_cards": TEMAS_CARDS,
        "faq_como_funciona": FAQ_COMO_FUNCIONA,
        "subpaginas": [p for p in PAGES if p.get("pai") == pagina["slug"] and p["publicada"]],
        "pai": PAGINAS_POR_SLUG.get(pagina.get("pai")),
        "paginas": PAGINAS_POR_SLUG,
        "static_v": static_v,
        "ano": SITE["ultima_atualizacao"][:4],
    }


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
def _registrar(pagina):
    def view():
        g.pagina = pagina
        return render_template(pagina["template"])

    endpoint = "pagina_" + pagina["id"].replace("-", "_")
    app.add_url_rule(pagina["slug"], endpoint, view)


for _p in paginas_publicadas():
    _registrar(_p)


@app.route("/robots.txt")
def robots_txt():
    corpo = f"User-agent: *\nAllow: /\n\nSitemap: {SITE['base_url']}/sitemap.xml\n"
    return Response(corpo, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in paginas_indexaveis():
        linhas.append(
            f"  <url><loc>{SITE['base_url']}{p['slug']}</loc>"
            f"<lastmod>{p.get('lastmod', SITE['ultima_atualizacao'])}</lastmod></url>"
        )
    linhas.append("</urlset>")
    return Response("\n".join(linhas) + "\n", mimetype="application/xml")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(BASE_DIR / "static", "favicon.ico", mimetype="image/x-icon")


@app.errorhandler(404)
def nao_encontrada(_erro):
    g.pagina = PAGINA_404
    return render_template("404.html"), 404


@app.after_request
def cabecalhos(resp):
    caminho = request.path
    if caminho.startswith("/static/"):
        if request.args.get("v"):
            resp.headers["Cache-Control"] = "public, max-age=31536000, s-maxage=31536000, immutable"
        else:
            resp.headers["Cache-Control"] = "public, max-age=86400"
    elif caminho in ("/robots.txt", "/sitemap.xml", "/favicon.ico"):
        resp.headers["Cache-Control"] = "public, max-age=3600"
    elif resp.mimetype == "text/html" and resp.status_code == 200:
        resp.headers["Cache-Control"] = "public, max-age=0, s-maxage=300, stale-while-revalidate=86400"
    if host_publico().endswith(".vercel.app"):
        resp.headers["X-Robots-Tag"] = "noindex"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))
