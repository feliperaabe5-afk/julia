# Site — Julia Monteiro, psicóloga

Site em Flask (Python) com várias páginas, WhatsApp flutuante, SEO por
página, schema (JSON-LD), aviso de cookies (Consent Mode v2) e a conversão
"Contato" do Google Ads.

> ⚠️ **Push na branch `main` = deploy automático no Vercel.** O repositório
> está ligado aos projetos `julia` e `julia-z6kq` do Vercel. Não dê push na
> `main` antes de liberar as travas de deploy (ver abaixo).

## Rodar localmente

Não precisa instalar Python no Windows: o [uv](https://docs.astral.sh/uv/) baixa tudo.

```bash
uv run --with flask==3.0.3 python app.py
```

Abra **http://localhost:5000**. As páginas:

| Página | Endereço | Situação |
|---|---|---|
| Home | `/` | no ar (novo título aguardando aprovação) |
| Psicóloga online | `/psicologa-online` | rascunho (noindex) |
| Terapia para mulheres | `/terapia-para-mulheres` | rascunho (noindex) |
| Terapia sistêmica | `/terapia-sistemica` | rascunho (noindex) |
| Ansiedade e sobrecarga | `/ansiedade` | rascunho, página de saúde |
| Relações e vínculos | `/relacionamentos` | rascunho, página de saúde |
| Transições de vida | `/transicoes-de-vida` | rascunho, página de saúde |
| Autoconhecimento | `/autoconhecimento` | rascunho, página de saúde |
| Sobre | `/sobre` | rascunho (noindex) |
| Como funciona (+ FAQ) | `/como-funciona` | rascunho (noindex) |
| Contato | `/contato` | rascunho (noindex) |
| Política de privacidade | `/privacidade` | rascunho (noindex) |
| Maternidade / Luto | `/transicoes-de-vida/maternidade`, `/luto` | ainda não publicadas (404) |

No `localhost` aparecem **notas amarelas "Pendente"** com o que falta a Julia
escrever ou aprovar. Elas nunca aparecem no domínio de produção. Para ver as
páginas como ficarão no ar, sem as notas:

```bash
OCULTAR_RASCUNHOS=1 uv run --with flask==3.0.3 python app.py
```

No `localhost` a tag do Google Ads **não carrega** (os IDs só entram no domínio
de produção), então testar o site não suja os dados das campanhas.

## Onde editar

Tudo fica em `app.py`:

- **`SITE`**: nome completo, CRP, Instagram, WhatsApp (número e mensagem),
  IDs do Google Ads e as chaves de liberação:
  - `nome_completo` / `nome_completo_confirmado`: o CFP exige o nome completo
    em toda divulgação. Trocar o nome aqui atualiza títulos, metas, schema,
    rodapé e identificação de todas as páginas. Depois de trocar, rode os
    testes: o título de `/relacionamentos` tem 1 caractere de folga.
  - `crp_conferido_cfp`: marcar `True` depois de conferir o registro no
    Cadastro Nacional do CFP.
  - `instagram_confirmado`: o logo diz `@PSI.JULIAMONTEIRO` (com ponto) e o
    link diz `psi_juliamonteiro` (com underline). Com `True`, o @ entra no
    schema e nas páginas novas.
  - `google_ads_id` / `google_ads_label_whatsapp`: conversão "Contato" (já é a
    que roda hoje). Deixe `""` para desligar a tag.
  - `remarketing_desligado_confirmado`: só o dono muda, **depois** de desligar a
    coleta de remarketing na conta do Google Ads. Libera a frase sobre
    remarketing na política de privacidade.
  - `modo_basico_em_todo_site`: `True` = modo básico do consentimento no site
    inteiro (mais conservador).
  - `aviso_cookies_ativo`: `False` = sem aviso (alternativa mínima: as páginas
    de saúde nunca carregam a tag e as demais só mandam sinais sem cookie).
  - `aviso_emergencia_aprovado`: libera o aviso "não é serviço de emergência
    (188/192)".
- **`PAGES`**: título, meta, H1 e as chaves de cada página:
  - `texto_aprovado`: com `False` a página responde normalmente, mas sai com
    `noindex` e fica fora do sitemap. Só mude para `True` quando a Julia tiver
    escrito/aprovado o texto próprio da página (sugestão: 250+ palavras
    exclusivas). **Só use como destino de anúncio/sitelink páginas com `True`.**
  - `pagina_saude`: liga o modo básico do consentimento.
  - `publicada`: `False` = a rota ainda não existe (404).
- **Texto próprio de cada página**: no template da página (`templates/*.html`),
  bloco `{% block texto_proprio %}`. Vazio, a seção não aparece.
- **FAQ de /como-funciona**: lista `FAQ_COMO_FUNCIONA` em `app.py`.

## Consentimento e Google Ads (Consent Mode v2)

- Em toda página, antes de qualquer tag: consentimento padrão **"denied"**.
- **Modo avançado** (home, /psicologa-online, /terapia-para-mulheres,
  /terapia-sistemica, /sobre, /como-funciona, /contato, /privacidade): o
  `gtag.js` carrega já; sem aceite, o Google recebe só sinais sem cookie.
- **Modo básico** (páginas de saúde: /ansiedade, /relacionamentos,
  /transicoes-de-vida e subpáginas, /autoconhecimento): o `gtag.js` **não** está
  no HTML e só é injetado depois do "Aceitar". Mesmo com aceite, o Google recebe
  o endereço genérico `/tema` (com gclid/gbraid/wbraid), nunca o tema.
- `allow_ad_personalization_signals: false` sempre; `ad_personalization` e
  `analytics_storage` nunca viram "granted" (não há remarketing nem GA4).
- A conversão dispara no clique de qualquer `.js-whatsapp-cta` (header, menu
  mobile, hero, meio, contato e botão flutuante), num único listener.
- A tag só roda nos hosts de `SITE["hosts_producao"]` (lidos do
  `X-Forwarded-Host`). Em `*.vercel.app` o site manda `X-Robots-Tag: noindex`.

## Testes

```bash
uv run --with flask==3.0.3 --with pytest pytest
```

Conferem rotas, SEO por página, regras do CFP (termos proibidos, identificação
com CRP), JSON-LD, consentimento, sitemap e cache.

**`test_liberado_para_deploy` falha de propósito** enquanto o nome completo e o
CRP não forem confirmados e a política de privacidade não for aprovada pela
Julia. Não publique com esse teste vermelho.

## Travas de deploy

Nada vai para a `main` antes de:

1. nome completo da Julia confirmado e CRP 08/47211 conferido no CFP;
2. aprovação da Julia para os textos (novo H1 da home, aviso de cookies,
   política de privacidade e o texto de cada página que for virar destino de
   anúncio);
3. para dizer "sem remarketing": coleta de remarketing desligada na conta.

Depois do deploy, antes de ligar campanhas, confira com `curl`:

```bash
curl -sI https://www.juliamonteiropsi.com.br/ | grep -i x-robots-tag          # vazio
curl -s  https://www.juliamonteiropsi.com.br/ | grep -c AW-18383511999        # >= 1
curl -s  https://www.juliamonteiropsi.com.br/ | grep -c ad_storage            # >= 1
curl -s  https://www.juliamonteiropsi.com.br/ansiedade | grep -c googletagmanager.com/gtag/js  # 0
curl -sI https://julia-z6kq.vercel.app/ | grep -i x-robots-tag                # noindex
curl -sI -H 'X-Forwarded-Host: julia-z6kq.vercel.app' https://www.juliamonteiropsi.com.br/ | grep -i x-robots-tag  # vazio
```

## Imagens

Os arquivos oficiais ficam em `assets-originais/` (não publicados). As versões
otimizadas em `static/img/` são geradas por:

```bash
uv run --with pillow python scripts/otimizar_imagens.py
```

## Estrutura

```
app.py                  # SITE, PAGES, rotas, schema, cabeçalhos
templates/
  base.html             # head (SEO, gtag, schema), header, footer, flutuante
  _interna.html         # layout das páginas internas
  index.html            # home
  *.html                # uma por página + 404.html
  partials/             # header, footer, CTA, passos, consentimento etc.
static/
  css/style.css
  js/script.js          # menu, consentimento, conversão, botão flutuante
  img/                  # imagens otimizadas (WebP + fallback)
assets-originais/       # originais (não servidos)
scripts/otimizar_imagens.py
tests/test_site.py
```
