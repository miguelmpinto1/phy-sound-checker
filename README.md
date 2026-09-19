# Physical Layer Sound Checker
O projeto Physical Layer Sound Checker utiliza o meio acústico para o tráfego de informações binárias entre dispositivos, atuando tanto como receptor quanto transmissor de dados; esse processo é realizado por dois métodos, o primeiro visando padronização para comunicação e o segundo para obter a maior taxa de transmissão de dados possível, evitando manipulações do sinal por ruídos.

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

Tal camada também sincroniza os bits para equilibrar o receptor e o transmissor temporalmente, define o meio de transmissão conforme os conectores, voltagem e dispositivos usados, caracteriza o tipo de transmissão (Simplex: unidirecional; Half-Duplex: permite que os dois transmitam e recebam mas, um de cada vez; Full-Duplex: transmite e recebe simultaneamente); controla a taxa de transmissão.

Pela conversão de bits para o meio, deve-se considerar os sinais analógicos e digitais:
- Sinais Analógicos representam dados de forma contínua, podendo assumir um número infinito de valores, oferecendo alta fidelidade na informação, porém, ficando vulnerável à ruídos, interferências ou distorções
- Sinais Digitais representam dados de forma lógica, aqui representados como 0 e 1, sendo resistente a ruídos porém, podendo perder informação na conversão do meio analógico para digital
No sinal analógico, se é quantificado amostras desse sinal em um período de tempo para conversão em sinal digital, tal quantificação se dá pela taxa de amostragem, enquanto o processo de alterar as características de um sinal para transpor em outro meio é chamado de modulação.

Já na funcionalidade de taxa de transmissão da camada, esta é ditada pela largura de banda, a capacidade de um meio em transportar dados de um lugar para o outro em determinado tempo, sendo diferenciada pelo número de bits transmitidos por segundo e influenciada por atrasos (latência), tipo de tráfego (serial/paralela) e goodput.

Assim, os principais problemas nesse contexto se dão pela: formação de ruídos, sinais indesejados que se misturam ao sinal original, causado por problemas físicos como agitação térmica, correntes indesejadas e picos de energia e a atenuação, dada pela perda gradual de intensidade ou potência do sinal, gerada por resistência elétrica, absorção dielétrica e perdas de sinal por reflexão ou dispersão ótica.

### Detecção de erros

## Engenharia e Arquitetura das Soluções:

1. [Método 1]
* 

2. [Método 2]
* 


## Divisão de Tarefas da equipe:

* Iago:
* Joao:
* Marcos: 
* Miguel: 
* Yuri: 

## Desafios, Problemas e Soluções

## Declaração do Uso de Inteligência Artificial

## Conclusão


## Instalação e contribuição

### Passos rápidos

* Clonar o repositório
* git clone
* cd
* [Passo adicional de build/configuração]
* [Passo de execução]
* Acessar a aplicação
* [URL ou porta de acesso]

> Observação: [Outra observação relevante, caso necessário]

### Guia para contribuição

Verificar o arquivo CONTRIBUTING para mais informações.
