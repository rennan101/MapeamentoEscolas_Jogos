import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Palavras-chave focadas em tecnologia e currículo
PALAVRAS_CHAVE = ["robótica", "programação", "design", "tecnologia", "multimídia", "maker", "desenvolvimento de sistemas", "jogos digitais", "computação"]

# Lista robusta de instituições de Recife, Olinda e Portais do Governo
sites_escolas = [
    # Públicas / Técnicas (ETEs e IFPE)
    {"nome": "IFPE - Campus Olinda", "url": "https://www.ifpe.edu.br/campus/olinda/", "tipo": "Médio-Técnico", "cidade": "Olinda"},
    {"nome": "IFPE - Campus Recife", "url": "https://www.ifpe.edu.br/campus/recife/", "tipo": "Médio-Técnico", "cidade": "Recife"},
    {"nome": "Secretaria de Educação PE (ETEs e EREMs)", "url": "http://www.educacao.pe.gov.br/", "tipo": "Pública (Estadual)", "cidade": "Recife/Olinda"},
    {"nome": "Prefeitura do Recife - Educação (Escolas Municipais)", "url": "https://educacao.recife.pe.gov.br/", "tipo": "Pública (Municipal)", "cidade": "Recife"},
    {"nome": "Porto Digital (Ecossistema/ETE)", "url": "https://www.portodigital.org/", "tipo": "Médio-Técnico / Inovação", "cidade": "Recife"},
    {"nome": "Oi Futuro - NAVE (ETE Cícero Dias)", "url": "https://oifuturo.org.br/programas/nave/", "tipo": "Médio-Técnico", "cidade": "Recife"},
    
    # Privadas - Recife e Olinda
    {"nome": "Colégio Motivo", "url": "https://www.colegiomotivo.com.br/", "tipo": "Privada", "cidade": "Recife"},
    {"nome": "Colégio Damas", "url": "https://www.colegiodamas.com.br/", "tipo": "Privada", "cidade": "Recife"},
    {"nome": "Colégio Santa Maria", "url": "https://www.santamaria.g12.br/", "tipo": "Privada", "cidade": "Recife"},
    {"nome": "Colégio São Bento", "url": "https://www.saobento.org.br/", "tipo": "Privada", "cidade": "Olinda"},
    {"nome": "Colégio Bairro Novo (CBN)", "url": "https://www.cbn.g12.br/", "tipo": "Privada", "cidade": "Olinda"}
]

dados_encontrados = []

# Cabeçalho para fingir que o robô é um navegador real (evita bloqueios de sites privados)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def fazer_scraping():
    print("Iniciando varredura profunda na internet...\n")
    
    for site in sites_escolas:
        print(f"Buscando em: {site['nome']}...")
        try:
            # Faz a requisição usando o header para evitar bloqueios
            resposta = requests.get(site['url'], headers=headers, timeout=15)
            resposta.raise_for_status() 
            
            # Lê o HTML da página
            soup = BeautifulSoup(resposta.text, 'html.parser')
            
            # Extrai os textos visíveis em tags comuns de conteúdo
            tags_texto = soup.find_all(['p', 'li', 'span', 'h1', 'h2', 'h3'])
            
            cursos_detectados = set()
            
            for tag in tags_texto:
                texto = tag.get_text().lower()
                for palavra in PALAVRAS_CHAVE:
                    if palavra in texto:
                        cursos_detectados.add(palavra.capitalize())
            
            if cursos_detectados:
                dados_encontrados.append({
                    "Escola": site['nome'],
                    "Tipo": site['tipo'],
                    "Cidade": site['cidade'],
                    "Cursos / Disciplinas": ", ".join(cursos_detectados),
                    "Endereço": "Verificar no site",
                    "Contato": site['url'],
                    "Responsável": "Robô Scraper"
                })
                print(f"[!] Sucesso: Encontrado {cursos_detectados}")
            else:
                print("[-] Nenhuma menção clara encontrada na página inicial.")
                
        except Exception as e:
            print(f"[x] Erro ou bloqueio ao acessar {site['nome']}: {e}")
            
        # Pausa de 2 segundos entre as requisições para não sobrecarregar os sites (Boa prática)
        time.sleep(2)

    if dados_encontrados:
        df = pd.DataFrame(dados_encontrados)
        df.to_csv('novas_escolas_encontradas.csv', index=False, encoding='utf-8-sig')
        print(f"\nVarredura completa! {len(dados_encontrados)} instituições foram adicionadas ao CSV.")
    else:
        print("\nVarredura completa. Nenhum dado relevante encontrado dessa vez.")

if __name__ == "__main__":
    fazer_scraping()