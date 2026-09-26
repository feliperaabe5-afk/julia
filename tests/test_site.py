"""Testes do site (regras de SEO, CFP, Google Ads e LGPD).

Rodar na raiz do repositório:

    uv run --with flask==3.0.3 --with pytest pytest

test_liberado_para_deploy FALHA DE PROPÓSITO enquanto o nome completo e o
CRP não forem confirmados e a política de privacidade não for aprovada.
É a trava de deploy: não publique com esse teste vermelho.
"""
import json
import re
import sys
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app import PAGES, PAGINAS_POR_SLUG, SITE, app, identificacao_meta  # noqa: E402

PROD = "www.juliamonteiropsi.com.br"
VERCEL = "julia-z6kq.vercel.app"
BASE = SITE["base_url"]
CRP = "CRP 08/47211"
WA = "https://wa.me/554184137113"

PUBLICADAS = [p for p in PAGES if p["publicada"]]
IDS = [p["id"] for p in PUBLICADAS]
SAUDE = [p for p in PUBLICADAS if p["pagina_saude"]]
NAO_SAUDE = [p for p in PUBLICADAS if not p["pagina_saude"]]

PASSOS = [
    "contando um pouco do que te trouxe",
    "Agendamos uma primeira sessão",
    "Definimos juntas a frequência",
]

TERMOS_PROIBIDOS = [
    "grátis", "gratuit", "especialista", "constelação", "constellation",
    "hellinger", "desconto", "promoção", "r$", "depoimento", "individual",
    "psicóloga sistêmica", "resultado garantido", "garantimos",
    "garantia de resultado",
]
REGEX_PROIBIDOS = [r"\bcura\b", r"\bcurar\b", r"em \d+ sess"]


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def get(client, path, host=None):
    headers = {"X-Forwarded-Host": host} if host else {}
    return client.get(path, headers=headers)


def normalizar(texto):
    return " ".join(texto.split())


class Pagina(HTMLParser):
    """Coleta o que os testes precisam de um HTML."""

    HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.metas = {}
        self.canonical = None
        self.h1 = 0
        self.eventos = []  # dentro de <main>: ("h", tag, texto) / ("t", texto)
        self.scripts = []  # {"attrs": {...}, "conteudo": "..."}
        self.urls = []
        self._em_title = False
        self._script = None
        self._em_main = False
        self._heading = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._em_title = True
        elif tag == "meta":
            chave = a.get("name") or a.get("property")
            if chave:
                self.metas[chave] = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        elif tag == "script":
            self._script = {"attrs": a, "conteudo": ""}
        elif tag == "main":
            self._em_main = True
        if tag in self.HEADINGS:
            if tag == "h1":
                self.h1 += 1
            if self._em_main:
                self._heading = [tag, ""]
        for attr in ("href", "src"):
            if a.get(attr):
                self.urls.append(a[attr])
        if a.get("srcset"):
            self.urls += [parte.strip().split(" ")[0] for parte in a["srcset"].split(",")]

    def handle_endtag(self, tag):
        if tag == "title":
            self._em_title = False
        elif tag == "script" and self._script is not None:
            self.scripts.append(self._script)
            self._script = None
        elif tag == "main":
            self._em_main = False
        elif self._heading and tag == self._heading[0]:
            self.eventos.append(("h", self._heading[0], self._heading[1].strip()))
            self._heading = None

    def handle_data(self, data):
        if self._em_title:
            self.title += data
        elif self._script is not None:
            self._script["conteudo"] += data
        elif self._heading is not None:
            self._heading[1] += data
        elif self._em_main and data.strip():
            self.eventos.append(("t", data.strip()))

    def jsonld(self):
        return [
            json.loads(s["conteudo"])
            for s in self.scripts
            if s["attrs"].get("type") == "application/ld+json"
        ]

    def scripts_inline(self):
        return [s["conteudo"] for s in self.scripts if not s["attrs"].get("src")]


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("host", [None, PROD, VERCEL])
def test_todas_as_rotas_respondem_200(client, host):
    for p in PUBLICADAS:
        r = get(client, p["slug"], host)
        assert r.status_code == 200, p["slug"]
    for extra in ("/robots.txt", "/sitemap.xml", "/favicon.ico"):
        assert get(client, extra, host).status_code == 200, extra


def test_subpaginas_nao_publicadas_dao_404(client):
    for p in PAGES:
        if not p["publicada"]:
            assert get(client, p["slug"]).status_code == 404
            html = get(client, "/transicoes-de-vida").get_data(as_text=True)
            assert f'href="{p["slug"]}"' not in html


def test_robots_txt(client):
    txt = get(client, "/robots.txt", PROD).get_data(as_text=True)
    assert "User-agent: *" in txt and "Allow: /" in txt
    assert f"Sitemap: {BASE}/sitemap.xml" in txt


def test_sitemap_so_paginas_aprovadas(client):
    xml = get(client, "/sitemap.xml", PROD).get_data(as_text=True)
    locs = set(re.findall(r"<loc>(.*?)</loc>", xml))
    esperado = {BASE + p["slug"] for p in PUBLICADAS if p["texto_aprovado"]}
    assert locs == esperado
    assert all(loc.startswith(BASE) for loc in locs)


@pytest.mark.parametrize("pid", IDS)
def test_robots_meta_segue_texto_aprovado(client, pid):
    p = next(x for x in PUBLICADAS if x["id"] == pid)
    pg = Pagina(get(client, p["slug"], PROD).get_data(as_text=True))
    esperado = "index,follow" if p["texto_aprovado"] else "noindex,follow"
    assert pg.metas.get("robots") == esperado


def test_404_em_portugues(client):
    r = get(client, "/pagina-que-nao-existe", PROD)
    html = r.get_data(as_text=True)
    assert r.status_code == 404
    assert "Página não encontrada" in html
    assert "Not Found" not in html
    assert Pagina(html).metas.get("robots", "").startswith("noindex")
    assert html.count(WA) >= 2
    assert "wa-float" in html


# ---------------------------------------------------------------------------
# SEO e identificação (CFP)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("pid", IDS)
def test_seo_e_identificacao(client, pid):
    p = next(x for x in PUBLICADAS if x["id"] == pid)
    html = get(client, p["slug"], PROD).get_data(as_text=True)
    pg = Pagina(html)
    titulo = pg.title.strip()
    meta = pg.metas.get("description", "")
    assert pg.h1 == 1, f"{p['slug']}: {pg.h1} <h1>"
    assert 0 < len(titulo) <= 60, (titulo, len(titulo))
    assert 0 < len(meta) <= 155, (meta, len(meta))
    assert meta.endswith(identificacao_meta())
    assert "psicóloga" in (titulo + " " + meta).lower()
    assert CRP in titulo + " " + meta
    assert pg.canonical == BASE + p["slug"]
    assert pg.canonical.startswith("https://www.juliamonteiropsi.com.br")
    assert pg.metas.get("og:url") == pg.canonical
    assert pg.metas.get("og:image", "").startswith(BASE + "/static/img/og-image.jpg")
    assert pg.metas.get("twitter:card") == "summary_large_image"
    corpo = html.split("<body", 1)[1]
    assert CRP in corpo
    assert corpo.count(WA) >= 2


@pytest.mark.parametrize("pid", IDS)
def test_h2_nunca_fica_vazio(client, pid):
    p = next(x for x in PUBLICADAS if x["id"] == pid)
    pg = Pagina(get(client, p["slug"], PROD).get_data(as_text=True))
    ev = pg.eventos
    for i, e in enumerate(ev):
        if e[0] == "h" and e[1] == "h2":
            assert e[2], f"{p['slug']}: <h2> sem texto"
            # conteúdo da seção: texto (inclusive de <h3>) até o próximo h1/h2
            seguinte = []
            for f in ev[i + 1:]:
                if f[0] == "h" and f[1] in ("h1", "h2"):
                    break
                if f[0] == "t":
                    seguinte.append(f[1])
            assert any(seguinte), f"{p['slug']}: <h2> '{e[2]}' sem texto antes do próximo título"


@pytest.mark.parametrize("host", [None, PROD])
def test_termos_proibidos(client, host):
    paginas = [p["slug"] for p in PUBLICADAS] + ["/pagina-que-nao-existe"]
    for slug in paginas:
        html = get(client, slug, host).get_data(as_text=True).lower()
        for termo in TERMOS_PROIBIDOS:
            assert termo not in html, f"'{termo}' em {slug}"
        for rx in REGEX_PROIBIDOS:
            assert not re.search(rx, html), f"/{rx}/ em {slug}"


def test_passos_so_na_home_e_em_como_funciona(client):
    for p in PUBLICADAS:
        html = get(client, p["slug"], PROD).get_data(as_text=True)
        for frase in PASSOS:
            if p["slug"] in ("/", "/como-funciona"):
                assert frase in html, (p["slug"], frase)
            else:
                assert frase not in html, (p["slug"], frase)


def test_sem_erro_de_digitacao_videochamada(client):
    for p in PUBLICADAS:
        assert "vídeochamada" not in get(client, p["slug"]).get_data(as_text=True)


# ---------------------------------------------------------------------------
# JSON-LD
# ---------------------------------------------------------------------------
TIPOS_PROIBIDOS = {"ProfessionalService", "LocalBusiness", "MedicalBusiness",
                   "MedicalClinic", "Physician", "Psychiatric"}
CHAVES_PROIBIDAS = {"employee", "founder", "worksFor", "aggregateRating", "review",
                    "priceRange", "areaServed", "address", "telephone", "availableLanguage"}


def _percorrer(no, caminho, achados):
    if isinstance(no, dict):
        tipos = no.get("@type", [])
        tipos = [tipos] if isinstance(tipos, str) else tipos
        for t in tipos:
            achados.append((t, tuple(caminho)))
        for k, v in no.items():
            assert k not in CHAVES_PROIBIDAS, f"chave proibida no schema: {k}"
            _percorrer(v, caminho + [k], achados)
    elif isinstance(no, list):
        for item in no:
            _percorrer(item, caminho, achados)


@pytest.mark.parametrize("pid", IDS)
def test_jsonld_regras(client, pid):
    p = next(x for x in PUBLICADAS if x["id"] == pid)
    pg = Pagina(get(client, p["slug"], PROD).get_data(as_text=True))
    blocos = pg.jsonld()
    assert len(blocos) == 1
    achados = []
    _percorrer(blocos[0], [], achados)
    tipos = [t for t, _ in achados]
    assert "Person" in tipos and "WebSite" in tipos
    assert not TIPOS_PROIBIDOS & set(tipos)
    for t, caminho in achados:
        if t == "Organization":
            assert caminho[-2:] == ("hasCredential", "recognizedBy"), caminho
    pessoa = next(n for n in blocos[0]["@graph"] if n["@type"] == "Person")
    assert pessoa["name"] == SITE["nome_completo"]
    assert pessoa["hasCredential"]["name"] == CRP
    assert ("sameAs" in pessoa) == SITE["instagram_confirmado"]
    if not p["texto_aprovado"]:
        assert "Service" not in tipos and "FAQPage" not in tipos and "BreadcrumbList" not in tipos


def test_tema_aprovado_vira_indexavel_com_service(client, monkeypatch):
    p = PAGINAS_POR_SLUG["/ansiedade"]
    monkeypatch.setitem(p, "texto_aprovado", True)
    html = get(client, "/ansiedade", PROD).get_data(as_text=True)
    pg = Pagina(html)
    assert pg.metas["robots"] == "index,follow"
    grafo = pg.jsonld()[0]["@graph"]
    servico = next(n for n in grafo if n["@type"] == "Service")
    assert servico["provider"] == {"@id": BASE + "/#julia"}
    assert servico["audience"]["suggestedGender"] == "female"
    assert any(n["@type"] == "BreadcrumbList" for n in grafo)
    assert 'class="nav-temas"' in html and 'href="/ansiedade"' in html
    xml = get(client, "/sitemap.xml", PROD).get_data(as_text=True)
    assert f"<loc>{BASE}/ansiedade</loc>" in xml


# ---------------------------------------------------------------------------
# Google Ads + Consent Mode (host de produção)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("pid", IDS)
def test_gtag_no_dominio_de_producao(client, pid):
    p = next(x for x in PUBLICADAS if x["id"] == pid)
    r = get(client, p["slug"], PROD)
    html = r.get_data(as_text=True)
    assert "X-Robots-Tag" not in r.headers
    i_default = html.find("gtag('consent', 'default'")
    assert i_default != -1
    trecho_default = html[i_default:html.find(");", i_default)]
    for sinal in ("ad_storage: 'denied'", "ad_user_data: 'denied'",
                  "ad_personalization: 'denied'", "analytics_storage: 'denied'"):
        assert sinal in trecho_default
    i_tag = html.find("googletagmanager.com/gtag/js")
    assert 'data-ads-id="AW-18383511999"' in html
    if p["pagina_saude"]:
        assert i_tag == -1, "página de saúde não pode ter gtag.js no HTML"
        assert 'data-modo-consentimento="basico"' in html
        assert 'data-pagina-saude="1"' in html
        assert "googletagmanager" not in html
        for codigo in Pagina(html).scripts_inline():
            assert p["slug"] not in codigo
            assert "page_location" not in codigo
    else:
        assert i_tag != -1 and i_default < i_tag
        assert "gtag/js?id=AW-18383511999" in html
        assert 'data-modo-consentimento="avancado"' in html


@pytest.mark.parametrize("host", [None, "127.0.0.1", VERCEL, "julia-seven-henna.vercel.app"])
def test_sem_gtag_fora_de_producao(client, host):
    for p in PUBLICADAS:
        r = get(client, p["slug"], host)
        html = r.get_data(as_text=True)
        assert "googletagmanager" not in html
        assert "AW-18383511999" not in html
        assert "gtag(" not in html
        if host and host.endswith(".vercel.app"):
            assert r.headers.get("X-Robots-Tag") == "noindex"
        else:
            assert "X-Robots-Tag" not in r.headers


def _corpo_funcao(js, assinatura):
    inicio = js.index(assinatura)
    abre = js.index("{", inicio)
    nivel = 0
    for i in range(abre, len(js)):
        if js[i] == "{":
            nivel += 1
        elif js[i] == "}":
            nivel -= 1
            if nivel == 0:
                return js[abre:i + 1]
    raise AssertionError("função sem fim: " + assinatura)


def test_script_js_consentimento_e_conversao():
    js = (RAIZ / "static" / "js" / "script.js").read_text(encoding="utf-8")
    # A injeção do gtag.js existe num único lugar e só com consentimento "granted"
    assert js.count('createElement("script")') == 1
    injetar = _corpo_funcao(js, "function injetarGtagSeAceito()")
    guarda = 'window.consentimentoAtual() !== "granted") return;'
    assert guarda in injetar
    assert injetar.index(guarda) < injetar.index('createElement("script")')
    # Conversão: no modo básico sem aceite, sai antes de chamar o gtag
    conv = _corpo_funcao(js, "window.trackWhatsAppConversion = function")
    guarda_conv = 'd.modoConsentimento === "basico" && window.consentimentoAtual() !== "granted") return;'
    assert guarda_conv in conv
    assert conv.index(guarda_conv) < conv.index('window.gtag("event", "conversion"')
    assert conv.index("!d.adsId || !d.adsLabel) return;") < conv.index('window.gtag("event"')
    # Config sempre sem personalização e com endereço genérico nas páginas de saúde
    config = _corpo_funcao(js, "function parametrosDaPagina()")
    assert "allow_ad_personalization_signals: false" in config
    assert "p.page_location = urlGenerica();" in config
    assert '"/tema"' in _corpo_funcao(js, "function urlGenerica()")
    # Consentimento: ad_personalization e analytics nunca viram "granted"
    assert "ad_personalization: \"granted\"" not in js
    assert "analytics_storage: \"granted\"" not in js
    # Falha no localStorage = "denied"
    atual = _corpo_funcao(js, "window.consentimentoAtual = function")
    assert '=== "granted" ? "granted" : "denied"' in atual


# ---------------------------------------------------------------------------
# WhatsApp, flutuante e privacidade
# ---------------------------------------------------------------------------
def test_whatsapp_url_codificada():
    esperado = WA + "?text=" + urllib.parse.quote(SITE["whatsapp_mensagem"], safe="")
    assert SITE["whatsapp_url"] == esperado
    assert " " not in SITE["whatsapp_url"] and "!" not in SITE["whatsapp_url"]


@pytest.mark.parametrize("pid", IDS + ["404"])
def test_botao_flutuante_em_todas_as_paginas(client, pid):
    slug = "/pagina-que-nao-existe" if pid == "404" else next(p["slug"] for p in PUBLICADAS if p["id"] == pid)
    html = get(client, slug).get_data(as_text=True)
    assert 'class="wa-float js-whatsapp-cta"' in html
    assert 'data-cta-origem="flutuante"' in html
    trecho = html[html.index('class="wa-float'):]
    assert f'href="{SITE["whatsapp_url"]}"' in trecho[:600]


def test_privacidade(client, monkeypatch):
    html = normalizar(get(client, "/privacidade", PROD).get_data(as_text=True))
    assert "Os dados de navegação podem ser processados fora do Brasil (Google e Vercel, nos EUA)." in html
    assert "remarketing" not in html.lower()
    monkeypatch.setitem(SITE, "remarketing_desligado_confirmado", True)
    html2 = get(client, "/privacidade", PROD).get_data(as_text=True)
    assert "remarketing" in html2.lower()


def test_aviso_de_cookies_e_link_de_preferencias(client):
    html = get(client, "/", PROD).get_data(as_text=True)
    assert 'id="avisoCookies"' in html and "hidden" in html.split('id="avisoCookies"')[1][:120]
    assert 'data-consentimento="granted"' in html and 'data-consentimento="denied"' in html
    assert "js-preferencias-cookies" in html
    assert 'href="/privacidade"' in html


# ---------------------------------------------------------------------------
# Estáticos e cache
# ---------------------------------------------------------------------------
def test_arquivos_estaticos_referenciados_existem(client):
    vistos = set()
    for p in PUBLICADAS:
        pg = Pagina(get(client, p["slug"]).get_data(as_text=True))
        for url in pg.urls:
            if url.startswith("/static/") and url not in vistos:
                vistos.add(url)
                assert client.get(url).status_code == 200, url
    assert any("julia-sobre-800.webp" in u for u in vistos)


def test_cache_de_estaticos_e_html(client):
    html = get(client, "/", PROD).get_data(as_text=True)
    css = re.search(r'href="(/static/css/style\.css\?v=[0-9a-f]+)"', html).group(1)
    r = client.get(css)
    assert "immutable" in r.headers["Cache-Control"]
    assert "s-maxage=300" in get(client, "/", PROD).headers["Cache-Control"]
    r2 = get(client, "/", PROD)
    assert r2.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert r2.headers["X-Content-Type-Options"] == "nosniff"


# ---------------------------------------------------------------------------
# TRAVA DE DEPLOY — falha de propósito até o dono confirmar
# ---------------------------------------------------------------------------
def test_liberado_para_deploy():
    pendentes = []
    if not SITE["nome_completo_confirmado"]:
        pendentes.append("nome completo da Julia (SITE['nome_completo_confirmado'])")
    if not SITE["crp_conferido_cfp"]:
        pendentes.append("CRP conferido no Cadastro Nacional do CFP (SITE['crp_conferido_cfp'])")
    if not PAGINAS_POR_SLUG["/privacidade"]["texto_aprovado"]:
        pendentes.append("política de privacidade e aviso de cookies aprovados pela Julia")
    assert not pendentes, "NÃO PUBLICAR. Pendente: " + "; ".join(pendentes)
