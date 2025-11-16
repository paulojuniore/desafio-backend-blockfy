# Desafio Backend - Blockfy

## Instruções para execução

### Requisitos

É recomendada a criação de um virtualenv para a instalação das dependências utilizadas no projeto, a fim de evitar a instalação das dependências de modo global.

```python
# Criação de ambiente virtual
python3 -m venv nome-do-venv

# Ativação do ambiente virtual
source nome-do-env/bin/activate

# Instalação das dependências
pip3 install -r requirements.txt
```

Nesse projeto utilizei de um banco de dados PostgreSQL. Para realização dos testes será necessária a criação de um banco Postgres e o preenchimentos das variáveis de conexão ao banco de dados em um arquivo **.env** na raiz do projeto. 

Para isso, é necessário a criação de um arquivo .env na raiz do projeto, e dentro dele definirmos os valores para as variáveis no seguinte formato:

```yaml
DB_NAME=nome-do-bd
DB_USER=usuario-do-bd
DB_PASSWORD=senha-do-bd
DB_HOST=localhost
DB_PORT=5432
```

Após isso, execute os seguintes comandos a partir da raiz do projeto:

```python
# Prepara o banco de dados e cria as tabelas
python3 manage.py migrate

# Executa o servidor e inicializa o projeto
python3 manage.py runserver
```

## Instruções para execução dos testes

Para executar os testes, a partir da raiz do projeto, execute o seguinte comando:

```python
python3 manage.py test communication/tests/
```

## Considerações sobre o projeto

Primeiramente, fiz a configuração dos models da aplicação, onde defini todos os campos que seriam necessários para a construção das entidades. Fiz também a criação de um banco de dados PostgreSQL, onde realizei a conexão da aplicação com o banco de dados. Além de guardar os valores de conexão em variáveis de ambiente, evitando assim a exposição em código.

Em relação às rotas, preferi começar com a rota de inserção de mensagens pix, pois ela é a base para todos os testes. Para isso, utilizei da biblioteca Faker, que foi muito útil para a geração de valores aleatórios (nome, uuid, cpf, etc). Que economizou muito tempo para a criação de mensagens de acordo com os parâmetros passados na URL da rota.

Para as rotas de iniciação do stream, comecei com o fluxo básico, onde verificava o header Accept para validar se tinha o valor application/json ou multipart/json para poder filtrar e retornar as mensagens, assinalá-las com visualizado (para que não sejam mais exibidas) e retornar o header Pull-Next com o recurso para continuar o Stream. Caso não existissem mensagens associadas, é retornado um status code 204 "No Content".

Para o controle de streams simultâneos, utilizei de um atributo de controle no model PixStream (is_active) que é inicializado com True sempre que um Stream é criado. No ínicio da função da rota de criação de stream, é realizado um filtro para obter a quantidade de streams que contém o ispb que foi passado por parâmetro e tem seu atributo is_active marcado como true. Então comparo esse valor com uma constante "MAX_STREAMS_PER_ISPB", para validar se já chegou no limite de streams simultâneos (6). Se sim, abortamos a requisição com um status code 429, se não, um novo stream é criado e o status code 200 é retornado.

Para o long pooling, foi criada uma função genérica para retorno das mensagens, que fica repetidamente consultando o banco por mensagens não visualizadas para o recebedor a partir do ispb passado. Se achar mensagens, marca as selecionadas como visualizado=True, as serialize e retorna um Response(200) com os dados. Se o tempo limite (LONG_POLLING_TIMEOUT) expirar sem novas mensagens, retorna 204 No Content e adiciona um header Pull-Next com a URL do stream.

E por fim, para evitar o acesso simultâneo às mesmas mensagens por diferentes sessões de streams, se fez necessária a utilização de transações. De modo que quando um worker inicia uma transação e pega algumas mensagens, é criado um lock (skip_locked=True), onde essas mensagens ficam indisponíveis para outro worker que tentar acessar o mesmo recurso. A transação encerra e o lock é retirado apenas quando as mensagens são marcadas como visualizadas. Nesse processo, também é criada uma associação entre a mensagem e o stream para garantir consistência e evitar que múltiplos workers processem a mesma mensagem ao mesmo tempo.

## Deploy da API: EC2 + Docker com banco de dados PostgreSQL no RDS.

O deploy foi realizado em uma instância EC2, utilizando docker e conectado a um banco de dados PostgreSQL no RDS. Segue os passos realizados para a efetivação do deploy da api na AWS:

- Dockerfile para criação de contêiner Docker englobando a API expondo a porta 8000;
- Criação de instância EC2 na AWS do tipo Ubuntu para deploy;
- Criação de banco de dados PostgreSQL no RDS;
- Criação de security groups com regras inbound/outbound para comunicação entre API e Banco de dados, além de regra para permitir conexão externa;
- Envio de arquivos do projeto para instância EC2 via SCP;
- Instalação do Docker na instância EC2;
- Build da imagem Docker e criação de tabelas;
- Configuração de IP elástico para manter fixo o ip da instância mesmo após restart;
- Run do contêiner e testes da API.
