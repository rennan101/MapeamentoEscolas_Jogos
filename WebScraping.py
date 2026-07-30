import requests
from bs4 import BeautifulSoup
import pandas as pd

# Palavras que o nosso robô vai procurar nas páginas das escolas
PALAVRAS_CHAVE = ["robótica", "programação", "design", "tecnologia", "multimídia", "maker"]

# Lista de sites que o robô vai vasculhar (Exemplo fictício/educacional)
sites_escolas = [
    {"nome": "Portal Educação PE - IFPE", "url": "https://www.ifpe.edu.br/"},
    # Você pode adicionar URLs de notícias da prefeitura ou páginas específicas de escolas
]

dados_encontrados = []

def fazer_scraping():
    print("Iniciando varredura na internet...\n")
    
    for site in sites_escolas:
        print(f"Buscando em: {site['nome']} ({site['url']})")
        try:
            # Faz a requisição para a página
            resposta = requests.get(site['url'], timeout=10)
            resposta.raise_for_status() # Verifica se deu erro (ex: site fora do ar)
            
            # Converte a página em um objeto que o Python consegue ler (BeautifulSoup)
            soup = BeautifulSoup(resposta.text, 'html.parser')
            
            # Extrai todo o texto da página (parágrafos)
            paragrafos = soup.find_all('p')
            
            cursos_detectados = set()
            
            # Analisa parágrafo por parágrafo
            for p in paragrafos:
                texto = p.get_text().lower()
                for palavra in PALAVRAS_CHAVE:
                    if palavra in texto:
                        cursos_detectados.add(palavra.capitalize())
            
            # Se encontrou alguma palavra-chave, salva na nossa lista
            if cursos_detectados:
                dados_encontrados.append({
                    "Escola": site['nome'],
                    "Tipo": "Mapeado via Web",
                    "Cidade": "Recife/Olinda",
                    "Cursos": ", ".join(cursos_detectados),
                    "Endereço": "Verificar no portal",
                    "Contato": site['url'],
                    "Responsável": "Web Scraper"
                })
                print(f"[!] Sucesso: Encontrado {cursos_detectados}")
            else:
                print("[-] Nenhuma palavra-chave encontrada.")
                
        except Exception as e:
            print(f"[x] Erro ao acessar {site['nome']}: {e}")

    # Salva o resultado em um arquivo CSV
    if dados_encontrados:
        df = pd.DataFrame(dados_encontrados)
        df.to_csv('novas_escolas_encontradas.csv', index=False, encoding='utf-8-sig')
        print("\nVarredura completa! Arquivo 'novas_escolas_encontradas.csv' gerado.")
    else:
        print("\nVarredura completa. Nenhum dado novo relevante encontrado.")

if __name__ == "__main__":
    fazer_scraping()