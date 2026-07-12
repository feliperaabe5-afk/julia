# Site — Julia Monteiro Psicóloga

Landing page em Flask (Python) no estilo "link na bio", com WhatsApp e Instagram.

## Como rodar localmente

```bash
pip install -r requirements.txt
python app.py
```

Depois acesse **http://localhost:5000** no navegador.

## Estrutura

```
julia-site/
├── app.py                 # servidor Flask + dados de contato
├── templates/
│   └── index.html         # página única (hero, sobre, especialidades, contato)
├── static/
│   ├── css/style.css      # paleta, tipografia e layout
│   ├── js/script.js       # destaque do menu ao rolar
│   └── img/               # pasta para foto de perfil, se quiser adicionar
└── requirements.txt
```

## Para editar as informações

Abra `app.py` e altere o dicionário `CONTEXT` no topo do arquivo:
nome, CRP, Instagram e número de WhatsApp. O texto da mensagem automática
do WhatsApp também pode ser ajustado ali.

Os textos das seções (Sobre, Para quem é, Como funciona) ficam em
`templates/index.html` — são só parágrafos HTML normais.

## Publicar o site (hospedagem)

Este é um app Flask simples, funciona em qualquer serviço que rode Python,
por exemplo Render, Railway, PythonAnywhere ou um VPS com gunicorn:

```bash
gunicorn app:app
```

Se preferir só um site estático (sem servidor Python), me avise que gero
uma versão em HTML puro também.
