"""Gera as imagens otimizadas do site a partir dos arquivos oficiais.

Rodar na raiz do repositório:

    uv run --with pillow python scripts/otimizar_imagens.py

Entrada: assets-originais/ (arquivos oficiais, NÃO publicados).
Saída:   static/img/ (o que o site usa) e static/favicon.ico.

Nada é redesenhado: as imagens são só redimensionadas e recortadas.
- Foto do Sobre (julia-sobre.jpg) -> 400/800 px em WebP + fallback JPG 800.
- Foto de perfil (perfil.jpg)     -> 600/900 px em WebP + fallback JPG 900.
- Logo (logo.png, 1080x1080)      -> logo-160.png (exibido com ~70 px no hero).
- Favicons                        -> recorte SÓ do símbolo Ψ do logo oficial.
- og-image.jpg (1200x630)         -> recorte do logo com o Ψ + "Julia Monteiro",
                                     SEM a linha do @ (o @ do logo ainda precisa
                                     ser confirmado pelo dono).
"""
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ORIG = RAIZ / "assets-originais"
IMG = RAIZ / "static" / "img"
IMG.mkdir(parents=True, exist_ok=True)

QUALIDADE_WEBP = 85
QUALIDADE_JPG = 86


def redimensionar(im: Image.Image, largura: int) -> Image.Image:
    if im.width <= largura:
        return im.copy()
    altura = round(im.height * largura / im.width)
    return im.resize((largura, altura), Image.LANCZOS)


def salvar_webp(im: Image.Image, nome: str) -> None:
    im.save(IMG / nome, "WEBP", quality=QUALIDADE_WEBP, method=6)


def salvar_jpg(im: Image.Image, nome: str) -> None:
    im.convert("RGB").save(
        IMG / nome, "JPEG", quality=QUALIDADE_JPG, optimize=True, progressive=True
    )


def bbox_do_conteudo(im: Image.Image, fundo, limiar=60, faixa_y=None):
    """Caixa (x0, y0, x1, y1) dos pixels que diferem do fundo."""
    px = im.load()
    y_ini, y_fim = faixa_y or (0, im.height)
    x0, y0, x1, y1 = im.width, None, -1, None
    for y in range(y_ini, y_fim):
        for x in range(im.width):
            p = px[x, y]
            if sum(abs(a - b) for a, b in zip(p, fundo)) > limiar:
                x0 = min(x0, x)
                x1 = max(x1, x)
                if y0 is None:
                    y0 = y
                y1 = y
    return x0, y0, x1 + 1, y1 + 1


def linhas_de_conteudo(im: Image.Image, fundo, limiar=60):
    """Faixas verticais (y0, y1) separadas por linhas só de fundo.
    No logo oficial: [Ψ, 'Julia Monteiro', '@PSI.JULIAMONTEIRO']."""
    px = im.load()
    faixas, inicio = [], None
    for y in range(im.height):
        tem = any(
            sum(abs(a - b) for a, b in zip(px[x, y], fundo)) > limiar
            for x in range(0, im.width, 2)
        )
        if tem and inicio is None:
            inicio = y
        elif not tem and inicio is not None:
            faixas.append((inicio, y))
            inicio = None
    if inicio is not None:
        faixas.append((inicio, im.height))
    return faixas


def fotos() -> None:
    sobre = Image.open(ORIG / "julia-sobre.jpg").convert("RGB")
    salvar_webp(redimensionar(sobre, 400), "julia-sobre-400.webp")
    salvar_webp(redimensionar(sobre, 800), "julia-sobre-800.webp")
    salvar_jpg(redimensionar(sobre, 800), "julia-sobre-800.jpg")

    perfil = Image.open(ORIG / "perfil.jpg").convert("RGB")
    salvar_webp(redimensionar(perfil, 600), "perfil-600.webp")
    salvar_webp(redimensionar(perfil, 900), "perfil-900.webp")
    salvar_jpg(redimensionar(perfil, 900), "perfil-900.jpg")


def logo_e_derivados() -> None:
    logo = Image.open(ORIG / "logo.png").convert("RGB")
    fundo = logo.getpixel((5, 5))

    # Logo inteiro, só reduzido (é o que aparece no círculo do hero)
    logo.resize((160, 160), Image.LANCZOS).save(IMG / "logo-160.png", optimize=True)

    faixas = linhas_de_conteudo(logo, fundo)
    if len(faixas) < 3:
        raise SystemExit(f"Layout do logo inesperado: {faixas}")
    (psi_y0, psi_y1), (nome_y0, nome_y1), (arroba_y0, _) = faixas[:3]

    # --- Favicons: só o Ψ, com margem, sobre o fundo original do logo ---
    x0, y0, x1, y1 = bbox_do_conteudo(logo, fundo, faixa_y=(psi_y0, psi_y1))
    psi = logo.crop((x0, y0, x1, y1))
    lado = round(max(psi.size) * 1.16)
    quadro = Image.new("RGB", (lado, lado), fundo)
    quadro.paste(psi, ((lado - psi.width) // 2, (lado - psi.height) // 2))
    quadro.resize((180, 180), Image.LANCZOS).save(
        IMG / "apple-touch-icon.png", optimize=True
    )
    quadro.resize((32, 32), Image.LANCZOS).save(IMG / "favicon-32.png", optimize=True)
    quadro.resize((48, 48), Image.LANCZOS).save(
        RAIZ / "static" / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)]
    )

    # --- og-image 1200x630: Ψ + "Julia Monteiro", sem a linha do @ ---
    margem = 24
    corte_y1 = min(nome_y1 + margem, arroba_y0 - 4)
    bx0, _, bx1, _ = bbox_do_conteudo(logo, fundo, faixa_y=(psi_y0, nome_y1))
    corte = logo.crop(
        (max(bx0 - margem, 0), max(psi_y0 - margem, 0), min(bx1 + margem, logo.width), corte_y1)
    )
    alvo_h = 560
    escala = alvo_h / corte.height
    corte = corte.resize((round(corte.width * escala), alvo_h), Image.LANCZOS)
    og = Image.new("RGB", (1200, 630), fundo)
    og.paste(corte, ((1200 - corte.width) // 2, (630 - corte.height) // 2))
    og.save(IMG / "og-image.jpg", "JPEG", quality=88, optimize=True, progressive=True)


if __name__ == "__main__":
    fotos()
    logo_e_derivados()
    for arq in sorted(list(IMG.iterdir()) + [RAIZ / "static" / "favicon.ico"]):
        with Image.open(arq) as im:
            print(f"{arq.relative_to(RAIZ)}: {im.size[0]}x{im.size[1]}, {arq.stat().st_size:,} B")
