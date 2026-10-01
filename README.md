# Physical Layer Sound Checker
O projeto Physical Layer Sound Checker utiliza o meio acústico para o tráfego de informações binárias entre dispositivos baseado nas funcionalidades da camada física do modelo ISO/OSI, atuando tanto como receptor quanto transmissor de dados; esse processo é realizado por dois métodos, o primeiro visando padronização para comunicação e o segundo para obter a maior taxa de transmissão de dados possível, evitando manipulações do sinal por ruídos.

## Fundamentação Teórica do projeto:

### Modelo ISO/OSI
O modelo ISO/OSI (Open Systems Interconnection) é uma padronização feita pela organização ISO para troca de dados entre redes de computadores e é constituída por 7 camadas:

- Aplicação -> Interface entre usuário e rede
- Apresentação -> Fornece tradução de dados
- Sessão -> Estabelecimento da sessão entre origem e destino
- Transporte -> Gerenciamento do transporte de dado
- Rede -> Endereçamento lógico e Roteamento
- Enlace/Data Link -> Detecção de erros, controle de acesso ao meio, endereçamento físico e controle do fluxo de informação
- **Física**

### Camada Física
A camada física utiliza meios de transmissão para realizar o tráfego de dados, convertendo bits na forma interpretável pelo meio, seja por sinais elétricos ou ópticos.

Tal camada também tem como função sincronizar os bits para equilibrar o receptor e o transmissor temporalmente, definir o meio de transmissão conforme os conectores, voltagem e dispositivos usados, controlar a taxa de transmissão e caracterizar o tipo dela (Simplex: unidirecional; Half-Duplex: permite que os dois transmitam e recebam, mas um de cada vez; Full-Duplex: transmite e recebe simultaneamente).

Pela necessidade de conversão de bits para o meio, deve-se considerar os dois tipos de sinais existentes, os analógicos e digitais:
- Sinais Analógicos representam dados de forma contínua, podendo assumir um número infinito de valores e oferecendo alta fidelidade na informação, porém, ficando vulnerável à ruídos, interferências ou distorções
- Sinais Digitais representam dados de forma lógica, aqui representados como 0 e 1, sendo resistente a ruídos, porém, podendo perder informação pela conversão do meio analógico para digital

No sinal analógico, se é quantificado amostras em um período de tempo para conversão em digital, tal quantificação se dá pela taxa de amostragem (quantas vezes por segundo o sinal analógico é medido), enquanto o processo de transformar as características de um sinal para transpor em outro meio é chamado de modulação.

Já na abordagem de taxa de transmissão da camada, esta é ditada pela largura de banda, a capacidade de um meio em transportar dados de um lugar para o outro em determinado tempo, sendo diferenciada pelo número de bits transmitidos por segundo e é influenciada por atrasos (latência), tipo de tráfego (serial/paralela) e goodput.

Assim, os principais problemas nesse contexto se dão pela: formação de ruídos, ou seja, sinais indesejados que se misturam ao sinal original, causados por problemas físicos como agitação térmica, correntes indesejadas e picos de energia, e a atenuação, dada pela perda gradual de intensidade ou potência do sinal, gerada por resistência elétrica, absorção dielétrica e perdas de sinal por reflexão ou dispersão ótica.

### Detecção de erros

Como toda transmissão de dados está sujeita a erros pela conversão de meios, foram implementadas no projeto formas de detecção para análise e validação:
- No método 1 por Paridade Par
- No método 2 pelo CRC-8
  
## Engenharia e Arquitetura das Soluções:

### **Método 1**

---
### **Método 2**
Para o **enquadramento** dos dados utilizamos o modelo: [Início (1,0,1)] + [Tamanho do Dado] + [Dado] + [Erro (CRC-8)] + [Fim (1,0,1)].

O delimitador [1,0,1] marca início e fim do quadro dentro do fluxo de bits, essencial para definir quando o receptor deve receber a mensagem. 
O campo TAMANHO guarda o número de bytes (1 a 255) e o erro do CRC-8.

A **modulação** implementada foi a M-FSK (Multiple Frequency-Shift Keying), utilizando 16 frequências, 4 bits por símbolo (em 1000, 1500, 2000 e 2500 Hz), escolhida pela maior eficiência e tolerância à ruídos porém, que demanda mais banda larga.
Enquanto para o processo de recepção da transmissão (demodulação) foi implementada a transformada rápida de Fourier (FFT), onde o algoritmo detecta e analisa o primeiro pico de sinal e a partir dele lê os outros, identificando a maior energia e consequentemente o valor dos bits transmitidos (0 ou 1).
Além das escolhas de modulação, já visando diminuição de ruídos, aplicamos também mais tecnologias com a mesma finalidade:

  Janelamento -> Como o FFT deve identificar o pico de energia, o janelamento diminui as primeiras e últimas ondas de cada sinal, evitando que ruídos pelo corte do início e final de transmissão sejam considerados.
  
  AGC -> Controle de ganho, amplificando o sinal caso esteja baixo e não seja perceptível ou reduzindo caso esteja alto e esteja causando distorção.
  
  Piso de ruído -> Analisa ruídos e traça um mínimo para ignorá-los.
  
  Detecção de início por energia espectral -> Identifica o início da passagem do dado, ignorando ruídos menores antes e depois da mensagem.
  
  Decisão de símbolo por confiança -> Compara o pico identificado com o segundo colocado e com o piso de ruído estimado para sinalização de possíveis erros.

**Taxas de transmissão:**
- A taxa teórica é adquirida por (theoretical_rate()): k / (SYMBOL_DURATION + SYMBOL_GAP) = 2 / 0,022s ≈ **90,9 bps**, ignorando qualquer overhead.
- A taxa prática leva em consideração o enquadramento, incluindo o overhead dos 0,3s de silêncio no início e final do quadro (SILENCE_LEAD), que impacta principalmente em mensagens curtas. Por exemplo, para transmitir a mensagem "A" (1 byte), o quadro completo tem 30 bits = 15 símbolos ≈ 0,33s de dados, mas o tempo total da transmissão (incluindo o overhead de 0,6s) é de aproximadamente 0,93s, ou seja, a taxa prática fica abaixo da teórica para mensagens curtas e se aproxima dela conforme a mensagem aumenta.
  
## Divisão de Tarefas da equipe:

* Iago de Souza Hernandes: Pesquisa, planejamento, vídeo, documentação e software (método 1 e 2)
* João Antonio Gradella: Planejamento e vídeo
* Marcos Vinicius Campelo dos Santos: Planejamento e software (interface)
* Miguel Moura Pinto: Pesquisa, planejamento, vídeo, documentação e software (modulação e método 2)
* Yuri Gustavo dos Santos Simplicio: Pesquisa, planejamento e software (método 1 e 2)

## Desafios, Problemas e Soluções

Durante a implementação do método 2, analisamos e descartamos diversas alternativas, como implementações de: ruído e volume fixos para um dispositivo ideal, sincronismo por preâmbulo acústico, algoritmo de Goertzel na demodulação ao invés de FFT e algoritmos de correção de erros simples (Hamming) e complexos (Reed-Solomon). Tais tentativas não aumentavam a eficiência do sistema, adicionando complexidade em questões simples, ou apenas eram ineficientes dentre nosso contexto. 

O maior desafio prático desse método foi saber onde o sinal realmente começa durante gravação, sem isso, a captação e decodificação falham por inteiro, a solução encontrada para esse problema foi detectar a primeira amostra que supera parte do pico do próprio sinal gravado, em vez de um valor fixo, assim o mesmo código se adapta à gravações ruins.

Portanto, diversos testes foram feitos, tanto simulados quanto em prática, individualmente ou intergrupos com sistemas diferentes, as principais dificuldades foram relacionadas ao meio acústico de transmissão, sobretudo na questão de emissão de ruídos, onde focamos para diminuir essa vulnerabilidade o máximo possível, mas sem um ambiente acústico ideal, ao menos para início e finalização do quadro, é inviável o envio de dados pela corrupção do meio, onde foi fundamental o uso dos detectores de erros em ambos os métodos, facilitando na identificação do problema.


## Declaração do Uso de Inteligência Artificial
O uso de ferramentas de Inteligência Artificial Generativa foi autorizado pela atividade e utilizado apenas na geração de código e pesquisa, estes, que passaram pela análise e aprovação dos membros do grupo.

## Conclusão


## Instalação, contribuição e licença

### Passos rápidos

* Clonar o repositório
* `git clone https://github.com/miguelmpinto1/phy-sound-checker.git`
* `cd phy-sound-checker`
* `docker compose run --rm app bash` (ou configurar um ambiente Python local com as dependências de `docker/requirements.txt`)
* `python src/main.py`
* Seguir o assistente interativo no terminal

> Observação: é necessário um dispositivo de entrada (microfone) e saída (alto-falante) de áudio disponíveis no sistema para o uso real, sem eles, o Emissor armazena o sinal em `.wav` para reprodução manual.

### Guia para contribuição

Verifique o arquivo CONTRIBUTING para mais informações.

### Licença

Este projeto é distribuído sob a **MIT License**.

Verifique o arquivo LICENSE para mais informações.
