__Documentação dos Scripts__

**1.0.** Visão Geral:  
    Os scripts desse repositório tem como função anonimizar os exames da base de dados e extrair informações relevantes para as próximas etapas do projeto de pesquisa.  
Esse arquivo detalha a estrutura do repositório, pré-requisitos e instruções de execução dos scripts.  

**2.0.** Estrutura do Repositório:   
  **2.1.** Estrutura de arquivos e pastas: 
    📁 Exams 
    📁 requirements.txt    
    📁 utils.py  
    📁 complete_processing.py  
    📁 anonymization.py  

  **2.2.** Descrição de funcionalidade de cada arquivo: 
    📁 Exams  
         Essa pasta deve conter os pdfs com os exames.

    📁 requirements.txt  
         Esse arquivo contém as bibliotecas com métodos e funções utilizados nos scripts, são elas e suas funções:  
         - pillow : Manipulação de imagens  
         - pymupdf : Leitura e manipulação de arquivos PDF  
         - pandas : Manipulação de dados estruturados  

    📁 anonymization.py  
        Script responsável por anonimizar os nomes dos PDFS, e gera as seguintes saídas:  
        - Exams_anonymized: pasta com os arquivos renomeados  
        - file_maping.csv: arquivo com mapeamento entre o nome antigo e novo de cada arquivo PDF. Este arquivo pode ser deletado, caso não haja interesse em rastrear a origem dos arquivos.

    📁 utils.py  
        Contém funções auxiliares criadas para auxiliar no processamento dos PDF's  
        - process_pdf: Processa um PDF, recorta regiões especificadas (como ECG, velocidade e amplitude) e salva como imagens.  
        - extract_pdf_slices_sequential: Processa todos os PDFs em uma pasta, movendo arquivos com problemas para uma pasta de erros.  
        - extract_information: Extrai informações textuais específicas (data, hora, sexo, etc.) da primeira página de um PDF.  

    📁 complete_processing.py  
        Script principal responsável por processar os dados, realizar recortes de imagens e exrair informações textuais dos PDFs.  
        Gera as seguintes saidas:  
        - extract_information.csv: Arquivo .csv com todas as informações relevantes extraidas de cada exame, (["File", "Data", "Hora", "Sexo", "Data de Nascimento", "Laudo"]).
        - ECG_Images, Amplitude, Speed: pastas contendo informações relevantes não convertidas para texto, ou seja, as imagens recortadas do ECG, e detalhes de amplitude e velocidade de cada exame. 
        - Problems e Errors: pastas criadas para registrar arquivos problematicos, guardando-os separadamente para análise mais cuidadosa.  

**3.0.** Pré-Requisitos:  
  **3.1.** Instalar as dependências:  
    Executar o comando abaixo na raiz do repositório:  
    '''pip install -r requirements.txt'''  
  **3.2.** Verificações antes de iniciar o processamento:  
    1. Tenha um backup dos arquivos originais pois os PDFs serão deletados no final do processo  
    2. Certifique-se de que a pasta Exams_anonymized contenha os PDFs originais e esteja no diretório principal do repositório  

**4.0.** Como Executar:  
  **4.1.** Execute o script de anonimização:  
    Execute o seguinte comando para anonimizar os nomes dos arquivos  

    '''python anonymization.py'''  
    
    Isso criará a nova pasta Exams_anonymized e o arquivo file_mapping.csv  
  **4.2.** Execute o script de processamento e extração de informações:  
    Rode o script principal  
    
    '''python complete_processing.py'''   
    
    Com isso você obterá os dados extraidos de cada PDF (extract_information.csv), pasta com iamgens recortadas decada exame (ECG_Images), recortes de amplitude e velocidade do exame (Pastas Amplitude e Speed respectivamente), arquivos com problemas para revisão manual (pastas Problems e Errors). Caso o processamento seja interrompido por algum motivo, rode o script novamente: ele continuará a partir do último pdf processado.


  





            
