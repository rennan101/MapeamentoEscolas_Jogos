import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import unicodedata
import re
from duckduckgo_search import DDGS

# O que o robô vai pesquisar no buscador
TERMOS_BUSCA = [
    "escola técnica robótica recife",
    "EREM programação recife",
    "ETE multimídia olinda",
    "escola particular maker recife",
    "ensino médio design olinda",
    "escola desenvolvimento de sistemas recife"
]

# DICIONÁRIO BLINDADO: A Chave é como vai aparecer no CSV, a Lista é o que o robô vai procurar.
# Escreva TODAS as variações SEM ACENTO e minúsculas aqui (o robô fará a limpeza do site para combinar)
CATEGORIAS_CURSOS = {
    "Robótica": ["robotica", "mecatronica", "arduino", "maker", "cultura maker", "robotics", "automacao"],
    "Programação": ["programacao", "coding", "software", "desenvolvimento de sistemas", "desenvolvimento web", "computacao", "ti", "tecnologia da informacao", "algoritmos", "python", "javascript", "programador", "front-end", "back-end"],
    "Design": ["design", "ux", "ui", "design grafico", "web design", "designer"],
    "Multimídia": ["multimidia", "audiovisual", "jogos digitais", "games", "animacao", "producao de audio", "edicao de video"]
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

dados_encontrados = []
urls_ja_visitadas = set()

# Função que limpa o texto: tira acentos e joga pra minúsculo
def limpar_texto(texto):
    if not texto:
        return ""
    # Remove acentos (NFKD separa o caractere do acento, encode/decode remove o acento)
    texto_sem_acento = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto_sem_acento.lower()

def buscar_links_na_web():
    print("Iniciando motor de busca (DuckDuckGo)...")
    links_encontrados = []
    
    with DDGS() as ddgs:
        for termo in TERMOS_BUSCA:
            print(f"Pesquisando por: '{termo}'...")
            try:
                resultados = list(ddgs.text(termo, region='br-pt', max_results=3))
                for res in resultados:
                    url = res.get('href')
                    if url and url not in urls_ja_visitadas and "facebook" not in url and "instagram" not in url:
                        links_encontrados.append({"nome": res.get('title'), "url": url, "termo": termo})
                        urls_ja_visitadas.add(url)
            except Exception as e:
                print(f"[x] Erro na busca por '{termo}': {e}")
            time.sleep(2)
            
    return links_encontrados

def fazer_scraping(sites):
    print(f"\n{len(sites)} sites encontrados na busca! Iniciando varredura com IA de texto...\n")
    
    for site in sites:
        print(f"Analisando: {site['nome'][:40]}... ({site['url']})")
        try:
            resposta = requests.get(site['url'], headers=HEADERS, timeout=10)
            
            if resposta.status_code == 200:
                soup = BeautifulSoup(resposta.text, 'html.parser')
                
                # Pega todo o texto da página e passa pelo nosso "Lava Jato"
                texto_sujo = soup.get_text()
                texto_limpo = limpar_texto(texto_sujo)
                
                cursos_detectados = set()
                
                # Verifica categoria por categoria
                for nome_oficial, variacoes in CATEGORIAS_CURSOS.items():
                    for variacao in variacoes:
                        # O \b garante que é uma palavra inteira (ex: "ti" não pega "tijolo")
                        padrao = r'\b' + re.escape(variacao) + r'\b'
                        
                        # Se encontrou qualquer variação, adiciona o NOME OFICIAL e para de procurar variações dessa mesma categoria
                        if re.search(padrao, texto_limpo):
                            cursos_detectados.add(nome_oficial)
                            break 
                
                if cursos_detectados:
                    cidade_estimada = "Olinda" if "olinda" in site['termo'].lower() else "Recife"
                    
                    dados_encontrados.append({
                        "Escola": site['nome'][:60],
                        "Tipo": "Mapeamento Autônomo",
                        "Cidade": cidade_estimada,
                        "Cursos / Disciplinas": ", ".join(cursos_detectados), # Salva bonitinho: "Robótica, Programação"
                        "Endereço": "Verificar no site",
                        "Contato": site['url'],
                        "Responsável": "Robô Buscador"
                    })
                    print(f"[!] Sucesso: Encontrado {cursos_detectados}")
                else:
                    print("[-] Nenhuma disciplina correspondente detectada.")
            else:
                print(f"[-] Site recusou acesso (Status {resposta.status_code})")
                
        except Exception as e:
            print(f"[x] Falha ao acessar site: {e}")
            
        time.sleep(1)

    if dados_encontrados:
        df = pd.DataFrame(dados_encontrados)
        df.to_csv('novas_escolas_encontradas.csv', index=False, encoding='utf-8-sig')
        print(f"\nVarredura autônoma completa! {len(dados_encontrados)} instituições mapeadas.")
    else:
        print("\nVarredura concluída, mas nenhuma disciplina nova foi validada hoje.")

if __name__ == "__main__":
    links_para_visitar = buscar_links_na_web()
    if links_para_visitar:
        fazer_scraping(links_para_visitar)
    else:
        print("O buscador não retornou nenhum link hoje.")