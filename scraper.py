import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import unicodedata
import re
import io
from PyPDF2 import PdfReader
from playwright.sync_api import sync_playwright

# 1. SEMENTE DE CONHECIMENTO (Garante que as escolas base nunca sumam)
SEMENTE_ESCOLAS = [
    {"Escola": "ETE Cícero Dias (NAVE)", "Tipo": "Técnico", "Cidade": "Recife", "Cursos / Disciplinas": "Programação, Jogos Digitais, Multimídia", "Endereço": "Rua Marques de Valença, 470", "Contato": "(81) 3181-3020", "Responsável": "Curadoria Original"},
    {"Escola": "ETE Porto Digital", "Tipo": "Técnico", "Cidade": "Recife", "Cursos / Disciplinas": "Desenvolvimento de Sistemas", "Endereço": "Av. Rio Branco, 193", "Contato": "(81) 3181-4868", "Responsável": "Curadoria Original"},
    {"Escola": "ETEPAM", "Tipo": "Técnico", "Cidade": "Recife", "Cursos / Disciplinas": "Desenvolvimento de Sistemas, Robótica", "Endereço": "Av. João de Barros, 1769", "Contato": "(81) 3181-3951", "Responsável": "Curadoria Original"},
    {"Escola": "IFPE - Campus Olinda", "Tipo": "Técnico", "Cidade": "Olinda", "Cursos / Disciplinas": "Design, Multimídia", "Endereço": "Av. Fagundes Varela, 375", "Contato": "(81) 3214-1804", "Responsável": "Curadoria Original"},
    {"Escola": "EREM Rotary Nova Descoberta", "Tipo": "Tempo Integral", "Cidade": "Recife", "Cursos / Disciplinas": "Programação", "Endereço": "Nova Descoberta", "Contato": "Secretaria Estadual", "Responsável": "Curadoria Original"},
    {"Escola": "Escola Mun. Dr. Rodolfo Aureliano", "Tipo": "Tempo Integral", "Cidade": "Recife", "Cursos / Disciplinas": "Robótica", "Endereço": "Várzea", "Contato": "(81) 3355-6677", "Responsável": "Curadoria Original"}
]

CATEGORIAS_CURSOS = {
    "Robótica": ["robotica", "mecatronica", "arduino", "maker", "cultura maker"],
    "Programação": ["programacao", "desenvolvimento de sistemas", "computacao", "python", "javascript"],
    "Design": ["design", "ux", "ui", "design grafico", "computacao grafica"],
    "Multimídia": ["multimidia", "audiovisual", "jogos digitais", "animacao"]
}

def limpar_texto(texto):
    if not texto: return ""
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower()

def extrair_texto_de_pdf(url_pdf):
    print(f"   -> [PDF Detectado] Lendo documento: {url_pdf[:50]}...")
    try:
        # Baixa o PDF temporariamente para a memória
        resposta = requests.get(url_pdf, timeout=10)
        if resposta.status_code == 200:
            arquivo_memoria = io.BytesIO(resposta.content)
            leitor = PdfReader(arquivo_memoria)
            texto_completo = ""
            # Lê as primeiras 5 páginas para não sobrecarregar
            for i in range(min(5, len(leitor.pages))):
                texto_completo += leitor.pages[i].extract_text()
            return texto_completo
    except Exception as e:
        print(f"   -> [x] Erro ao ler PDF: {e}")
    return ""

def buscar_escolas_openstreetmap():
    print("Conectando ao banco de dados aberto do OpenStreetMap...")
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    area["name"="Recife"]->.recife;
    area["name"="Olinda"]->.olinda;
    (
      node["amenity"="school"](area.recife);
      way["amenity"="school"](area.recife);
      node["amenity"="school"](area.olinda);
      way["amenity"="school"](area.olinda);
    );
    out center;
    """
    escolas_mapa = []
    try:
        response = requests.post(overpass_url, data={'data': overpass_query}, timeout=25)
        for element in response.json().get('elements', []):
            tags = element.get('tags', {})
            nome, site = tags.get('name'), tags.get('website')
            if nome and site and site.startswith("http"):
                escolas_mapa.append({"nome": nome, "url": site, "cidade": "Recife" if "Recife" in str(tags) else "Olinda"})
        print(f"Sucesso! Encontradas {len(escolas_mapa)} escolas com site oficial no mapa.")
    except Exception as e:
        print(f"Erro ao acessar OpenStreetMap: {e}")
    return escolas_mapa

def procurar_cursos_no_texto(texto):
    texto_limpo = limpar_texto(texto)
    cursos_encontrados = set()
    for nome_oficial, variacoes in CATEGORIAS_CURSOS.items():
        for variacao in variacoes:
            if re.search(r'\b' + re.escape(variacao) + r'\b', texto_limpo):
                cursos_encontrados.add(nome_oficial)
                break
    return cursos_encontrados

def fazer_scraping_avancado(sites):
    dados_encontrados = SEMENTE_ESCOLAS.copy()
    print(f"\nIniciando Navegador Fantasma (Playwright) para {len(sites)} sites...\n")
    
    with sync_playwright() as p:
        # Inicia o navegador invisível
        navegador = p.chromium.launch(headless=True)
        pagina = navegador.new_page()
        
        for site in sites:
            print(f"Lendo: {site['nome']}")
            try:
                # Usa o navegador para acessar o site (espera até carregar tudo)
                pagina.goto(site['url'], timeout=15000, wait_until="networkidle")
                texto_site = pagina.content()
                
                # Procura cursos no texto da página principal
                cursos_detectados = procurar_cursos_no_texto(BeautifulSoup(texto_site, 'html.parser').get_text())
                
                # BÔNUS: Procura links de PDF na página para ler editais e ementas
                soup = BeautifulSoup(texto_site, 'html.parser')
                links_pdf = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.pdf')]
                
                # Lê até 2 PDFs por site para investigar
                for pdf_link in links_pdf[:2]:
                    # Corrige links relativos (ex: /edital.pdf) para absolutos
                    if pdf_link.startswith('/'):
                        pdf_link = site['url'].rstrip('/') + pdf_link
                    
                    texto_do_pdf = extrair_texto_de_pdf(pdf_link)
                    cursos_detectados.update(procurar_cursos_no_texto(texto_do_pdf))
                
                # Se achou algum curso, salva na planilha
                if cursos_detectados:
                    tipo_escola = "Privada/Outros"
                    if "EREM" in site['nome'].upper(): tipo_escola = "Tempo Integral"
                    elif "ETE" in site['nome'].upper() or "TÉCNICA" in site['nome'].upper(): tipo_escola = "Técnico"
                    
                    dados_encontrados.append({
                        "Escola": site['nome'],
                        "Tipo": tipo_escola,
                        "Cidade": site['cidade'],
                        "Cursos / Disciplinas": ", ".join(cursos_detectados),
                        "Endereço": "Verificar no site",
                        "Contato": site['url'],
                        "Responsável": "Robô Avancado (Navegador/PDF)"
                    })
                    print(f"   [!] Sucesso: Cursos validados: {cursos_detectados}")
                else:
                    print("   [-] Nenhum curso tech detectado.")
            except Exception as e:
                print(f"   [x] Falha ao analisar (Site fora do ar ou bloqueio pesado).")
            
            time.sleep(2) # Pausa respeitosa entre os acessos
            
        navegador.close()

    # Salva e remove escolas duplicadas
    df = pd.DataFrame(dados_encontrados)
    df.drop_duplicates(subset=['Escola'], keep='last', inplace=True)
    df.to_csv('novas_escolas_encontradas.csv', index=False, encoding='utf-8-sig')
    print(f"\nVarredura pesada concluída! O painel tem agora {len(df)} escolas tech mapeadas.")

if __name__ == "__main__":
    escolas_para_visitar = buscar_escolas_openstreetmap()
    if escolas_para_visitar:
        fazer_scraping_avancado(escolas_para_visitar)
    else:
        print("Nenhuma escola retornada do banco de dados para iniciar o processo.")