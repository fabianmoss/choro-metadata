"""Sample records of the Casa do Choro acervo, transcribed.

The dictionaries below reproduce, unchanged, what the acervo publishes at
<https://acervo.casadochoro.com.br/>.  The transformation into FRBR entities
(work, expression, manifestation, item) is done by
:mod:`tools.acervo.sample`, which also resolves the free names used by the
acervo to the corresponding person records.

The sample covers the cases that matter for the modelling:

=========================================  =====================================
"baianinha" (Candinho Trombone)             several manuscript copies, copyist,
                                           dates, provenance, arrangement and edition
"1ª polca a gente nunca esquece"            manuscript by the composer himself
"Amarga saudade"                          restricted edition, arrangement, no digitisation
"Araponga e a Juriti"                      instrumentation, editor, lyrics, arrangement
"baianinha" (P. de Alcântara Bacellar)      namesake, piano score
"Saudade de São João do Príncipe"           copy made by the composer himself
=========================================  =====================================

Only the strings that the acervo itself publishes are kept in Portuguese;
the comments and the notes written by the modeller are in English.
"""

CARDS = [
    {
        "id": "1127",
        "name": "Candinho Trombone",
        "inverted": "Silva, Cândido Pereira da",
        "roles": ["Compositor", "Trombonista", "Violonista", "Maestro"],
        "birth": "30.01.1879",
        "death": "12.12.1960",
        "birth_place": "Rio de Janeiro - RJ",
        "sources": "1. PINTO, Alexandre Gonçalves. O Choro — reminiscências dos chorões antigos. 2ª ed. Rio de Janeiro: Funarte, 1978. (p. 16, 20, 82)\n2. VASCONCELOS, Ary. Panorama da música popular brasileira na Belle Époque. Rio de Janeiro: Livraria Santana Ltda., 1977.\n3. ENCICLOPÉDIA DA MÚSICA BRASILEIRA: POPULAR, ERUDITA E FOLCLÓRICA. São Paulo: Art Editora/Publifolha, 1998.",
        "nworks": 500,
        "bio": "<p>Filho de Jerônimo Silva e Rosa Pereira começou a estudar com seu pai, que também era “chorão”, flautista e compositor. Residiu no Asilo dos Meninos desvalidos,&nbsp;em Vila Isabel, onde sofreu um acidente que lhe tirou a visão do olho esquerdo, porém sua iniciação profissional foi na Banda do Asilo, de onde também saíram músicos como Francisco Braga, Paulino Sacramento e Albertino Pimentel. Casou-se várias vezes e teve duas filhas, para elas dedicou várias composições.</p>\r\n\r\n<p>A obra do trombonista Cândido Pereira da Silva, Candinho Silva ou Candinho Trombone, como se tornou conhecido, abrange mais de 475 composições (das quais pouquíssimas foram editadas), entre elas a polca O Nó, que se tornou, por suas modulações imprevistas, um clássico do repertório do choro. Com seu ponto (grafia musical) inconfundível, Candinho escreveu não só suas próprias composições como também as de diversos chorões que não sabiam música. Dessa forma foi uma figura decisiva na preservação do trabalho desses artistas para as gerações futuras. Nasceu no Rio de Janeiro e iniciou suas atividades como músico na Banda da Fábrica de Tecidos Confiança, em Vila Isabel, onde chegou a contramestre. Aos 19 anos de idade passou a integrar a Banda da Polícia Militar, também como contramestre. Tocava, além de trombone, bombardino e bombardão. Em 1916, com o grupo O Passos no Choro, gravou na Odeon uma de suas músicas mais conhecidas: a polca Soluçando. Em 1918 participou do Conjunto Carioca, ao lado de Antônio Maria Passos (flauta), Nelson Alves (cavaquinho) e Donga (violão). Outros grandes chorões desse tempo foram seus companheiros, entre eles Irineu de Almeida, Licas do Trombone, Mário Álvares, Luiz Gonzaga da Hora (tuba), Anacleto de Medeiros, Albertino Pimentel, Luiz de Souza, Pixinguinha, Quincas Laranjeiras, Juca Kalut, Nolasco, Amora Cavaquinho e Catulo. Em 1924 fez parte, ao lado do cavaquinista e compositor Eurico Batista, do grupo Africanos de Vila Isabel, além de integrar a Sociedade Carnavalesca Pragas do Egito, cujo presidente era Alexandre Gonçalves Pinto. Já nessa época fazia parte da Sociedade de Concertos Sinfônicos do Rio de Janeiro e integrava a Orquestra do Teatro São José. A partir da década de 30 passou a trabalhar como primeiro trombonista da Orquestra Sinfônica Brasileira. Em 1959, já doente, doou seu arquivo musical a Jacob do Bandolim. Hoje esse tesouro faz parte do acervo do Museu da Imagem e do Som. Na coleção de CDs “Princípios do Choro”, gravada em 2002 (Acari Records/ Biscoito Fino), teve um disco inteiramente dedicado à sua obra.</p>",
        "encyclopedia": "Enciclopédia Ilustrada do Choro no Séc. XIX",
    },
    {
        "id": "1865",
        "name": "Maria Souto",
        "inverted": "Souto, Maria",
        "roles": ["Flautista"],
        "birth_place": "Rio de Janeiro - RJ",
        "bio": "<p>Aguardando dados biográficos.</p>",
    },
    {
        "id": "1465",
        "name": "Nabor Pires Camargo",
        "inverted": "Camargo, Nabor Pires",
        "roles": ["Clarinetista", "Compositor", "Pianista"],
        "birth": "09.02.1902",
        "death": "30.10.1996",
        "birth_place": "Indaiatuba - SP",
        "nworks": 64,
        "bio": "<p>Verbete sec XX</p>",
    },
    {
        "id": "1236",
        "name": "Marcelo Tupinambá",
        "inverted": "Lobo, Fernando Álvares",
        "roles": ["Compositor", "Instrumentista"],
        "birth": "29.05.1889",
        "death": "04.07.1953",
        "birth_place": "Tietê - SP",
        "sources": "1. ENCICLOPÉDIA DA MÚSICA BRASILEIRA: POPULAR, ERUDITA E FOLCLÓRICA. São Paulo: Art Editora/Publifolha, 1998.",
        "nworks": 96,
        "bio": "<p>\r\n\tSeu pai, Eduardo Lobo, era regente da Banda Sant&iacute;ssima Trindade e seu tio, o maestro e compositor paulista Elias &Aacute;lvares Lobo (1834&ndash;1901), autor da primeira &oacute;pera brasileira. Desde crian&ccedil;a aprendeu a tocar piano de ouvido e mais tarde, violino, com S&aacute;vio Benedictis. Quando tinha 15 anos, em 1907, chegou a acompanhar ao piano o famoso flautista Pat&aacute;pio Silva, no &uacute;ltimo ano de sua vida, apresentando-se em cidades do interior paulista. Aprendeu a tocar v&aacute;rios instrumentos e, quando cursava o gin&aacute;sio na cidade de Pouso Alegre, MG, atuou como diretor da banda local. Come&ccedil;ou a lan&ccedil;ar suas primeiras composi&ccedil;&otilde;es em 1914, sob o pseud&ocirc;nimo Marcelo Tupinamb&aacute;, na revista <em>S&atilde;o Paulo Futuro</em>, de Danton Vampr&eacute;, ao mesmo tempo em que cursava a Escola Polit&eacute;cnica de S&atilde;o Paulo. Publicou v&aacute;rias pe&ccedil;as dan&ccedil;antes inspiradas em temas sertanejos compostas para o teatro de revista. Entre elas destacam-se algumas m&uacute;sicas de sucesso como os tanguinhos <em>Viola Cantad&ecirc;ra</em> e <em>Maricota Sai da Chuva</em>, inclu&iacute;dos nas revistas <em>Cenas da Ro&ccedil;a</em> e <em>Flor do Sert&atilde;o</em> (com Arlindo Leal); o cateret&ecirc; <em>Matuto</em> (com Claudino Costa) e os tangos <em>Tristeza</em> <em>de Caboclo</em> e <em>Sou Batuta</em>. Formou-se engenheiro civil em 1916 e exerceu a profiss&atilde;o at&eacute; 1923, quando, por motivo de uma doen&ccedil;a dos olhos precisou interromper a carreira. A partir de ent&atilde;o passou a dedicar-se inteiramente &agrave; m&uacute;sica, escrevendo inclusive pe&ccedil;as de concerto e musicando poemas de Manuel Bandeira, Oleg&aacute;rio Mariano, Coelho Neto, entre outros. Teve valsas, tangos, maxixes, cateret&ecirc;s e can&ccedil;&otilde;es gravados por orquestras populares e pelos principais cantores da &eacute;poca.</p>",
        "encyclopedia": "Enciclopédia Ilustrada do Choro no Séc. XIX",
    },
    {
        "id": "110",
        "name": "P. de Alcântara Bacellar",
        "inverted": "Bacellar, P. de Alcântara",
        "roles": ["Compositor"],
        "birth_place": "Local não identificado",
        "bio": "<p>\r\n\tN&atilde;o foram encontrados dados biogr&aacute;ficos.</p>",
        "encyclopedia": "Enciclopédia Ilustrada do Choro no Séc. XIX",
    },
    {
        "id": "1156",
        "name": "Viriato Figueira da Silva",
        "inverted": "Silva, Viriato Figueira da",
        "roles": ["Compositor", "Flautista"],
        "death": "24.04.1883",
        "birth_place": "Macaé - RJ",
        "sources": "1. VASCONCELOS, Ary. Panorama da música popular brasileira na Belle Époque. Rio de Janeiro: Livraria Santana Ltda., 1977.\n2. PINTO, Alexandre Gonçalves. O Choro — reminiscências dos chorões antigos. 2ª ed. Rio de Janeiro: Funarte, 1978. (p. 11, 20, 21, 22, 39)",
        "nworks": 16,
        "bio": "<p>O flautista Viriato Figueira da Silva nasceu em Macaé, RJ. Estudou no Conservatório de Música do Rio de Janeiro com Joaquim Callado, de quem se tornou grande amigo. Foi um dos primeiros a se destacar no Brasil como solista de saxofone. Viajou a São Paulo como integrante da orquestra do Teatro Phoenix Dramática, sob direção do maestro Henrique Alves de Mesquita. Segundo o flautista Pedro de Assis, Viriato “empreendeu com grande êxito artístico e financeiro uma turnê artística às capitais nortistas alguns anos depois de ter feito a mesma digressão o maior flautista do mundo, o célebre flautista belga André Mateus Reichert”. Foram encontradas nove composições de sua autoria, entretanto há dúvida quanto a autoria da polca <em>Uma Dor</em>, cuja melodia é idêntica à da polca <em>Saudosa</em> de Joaquim Callado. <em>Uma Dor</em> foi gravada em 2002 na coleção de CDs “Princípios do Choro” (Acari Records/ Biscoito Fino), além de outras cinco polcas.</p>",
        "encyclopedia": "Enciclopédia Ilustrada do Choro no Séc. XIX",
    },
    {
        "id": "1415",
        "name": "Manoel Pedro do Nascimento",
        "inverted": "Nascimento, Manoel Pedro do",
        "roles": ["Clarinetista", "Compositor", "Copista"],
        "birth_place": "Rio de Janeiro - RJ",
        "nworks": 15,
        "bio": "<p>\r\n\tCopista prol&iacute;fico, registrou as m&uacute;sicas de centenas de compositores de choro em cadernos manuscritos, assinando &ldquo;Nascimento&rdquo; com indica&ccedil;&atilde;o de local e data. As informa&ccedil;&otilde;es biogr&aacute;ficas de muitos desses compositores foram prestadas pelo bandolinista D&eacute;o Rian, que conheceu Nascimento. Segundo Rian, Nascimento morava na Aboli&ccedil;&atilde;o e freq&uuml;entava as rodas de choro do Retiro da Velha Guarda, em Jacarepagu&aacute;. Eis a rela&ccedil;&atilde;o de alguns dos compositores cujas m&uacute;sicas foram registradas por Nascimento: Alem, J. Amaral, R. Apol&ocirc;nio, Arthur Ayr&atilde;o, J. J. Azevedo J&uacute;nior, Adalberto de Azevedo (Betinho), Jo&atilde;o Barbosa, Franco C. Bolaes, J&uacute;lio Braga, Manoel Amorim Lima (Braga), Maur&iacute;cio Braga, C&eacute;sar, Ayres Costa (Santinho), Jos&eacute; Fontes, Marcos Jos&eacute; Francisco, Jos&eacute; Soares de Freitas (Dudinha), Henrique Jo&atilde;o Flauta B. M. Jurandyr, Jos&eacute; do Carmo, Raul Silva, Louren&ccedil;o Lamartine, L&aacute;zaro, Assis Leal (Mac&aacute;rio), Francisco Assis Leal (Macarinho), Francisco Lima, Joaquim de Lima, Luizinho, Rubens Martins, Jo&atilde;o Medeiros, Nory Mendes (O Patativa), Ot&aacute;vio Dias Moreno, Narciso, Arlindo Nascimento, Ilydio Nascimento, Jo&atilde;o Batista do Nascimento, Chico Neto, Abelardo Neves, Nola, Aristides de Oliveira (Moleque Diabo), Biliano de Oliveira, Pedro Oliveira, Oscar Cruz N. Paim, Manoel Passinha, Floriano Pientznauer, Albertino Pimentel (Carramona), Jos&eacute; Ferreira Ramos, Oscar Roxinol, Ari Corr&ecirc;a de S&aacute;, Jo&atilde;o Sampaio, Achiles dos Santos (Caboclo), Dion&iacute;sio da Silva, Sebasti&atilde;o de Lima e Sousa, Jos&eacute; Toledo, Candinho Silva, Nelson Alves, Alfredinho Flautim, M&aacute;rio &Aacute;lvares, Lu&iacute;s Americano, Caninha, Henrique Dourado, Freire J&uacute;nior, Chiquinha Gonzaga, Juca Kalut, Louro, Pixinguinha, Patr&iacute;cio Teixeira, Jos&eacute; da Silva (Baianinho) e Eduardo Souto.</p>",
        "encyclopedia": "Enciclopédia Ilustrada do Choro no Séc. XIX",
    },
    {
        "id": "1585",
        "name": "Pedro Paes",
        "inverted": "Paes, Pedro",
        "roles": ["Arranjador(a)", "Clarinetista", "Compositor", "Saxofonista", "Violonista"],
        "birth_place": "Brasília - DF",
        "nworks": 42,
        "bio": "<p>Depois de graduar-se bacharel em Violão pela Uni-Rio, passou a se dedicar ao estudo do clarinete e do saxofone, instrumentos com os quais vem se destacando como solista de choro nas rodas cariocas. É integrante do Sexteto Mauricio Carrilho e participou de gravações de discos como “Princípios do Choro”, “Choro Carioca, Música do Brasil”, entre outros. Na Escola Portátil, é responsável pelo ensino do clarinete.</p>",
        "encyclopedia": "Enciclopédia Ilustrada do Choro no Séc. XIX",
    },
    {
        "id": "2006",
        "name": "Miguel Rabello",
        "inverted": "Bastos, Miguel Rabello",
        "roles": ["Compositor", "Violonista"],
        "birth_place": "Rio de Janeiro - RJ",
    },
    {
        "id": "2326",
        "name": "Miguel Rabello",
        "inverted": "Rabello, Miguel",
        "roles": ["Compositor", "Violonista"],
        "birth_place": "Rio de Janeiro - RJ",
    },
    {
        "id": "1899",
        "name": "Sergio Valdeos",
        "inverted": "Valdeos, Sergio",
        "roles": ["Arranjador(a)", "Compositor", "Violonista"],
        "birth_place": "Compositor estrangeiro",
        "sources": "http://www.loscuatro.com.br/#!sergio-valdeos/ctmm",
        "bio": "<p>Violonista, compositor e arranjador, trabalhou com diversos músicos e cantores em gravações e shows, entre outros: Eva Ayllon, Pilar de la Hoz, Carmina Canavino, Gian Marco Zignago, Cecilia Barraza, Cecilia Bracamonte, Jane Duboc, Guinga, Leila Pinheiro, Celia Vaz.&nbsp;</p>\r\n\r\n<p>Destaca-se sua participação no grupo da cantora Susana Baca (ganhadora do Grammy Latino 2002) com quem trabalho entre 2001 e 2009 participando em quatro produções musicais e viajando pelos cinco continentes nos principais festivais de “world&nbsp;music.”</p>\r\n\r\n<p>No Peru, foi fundador do “Clube do Choro”, grupo dedicado à difusão do choro e da cultura brasileira e criou o grupo Kenyara com um trabalho livre sobre a música instrumental da costa e os Andes.</p>\r\n\r\n<p>Trabalhou junto a Carlos Hayre (2007-2011) em um livro sobre o violão da costa do Peru, projeto patrocinado pela Universidade Católica del Perú (PUCP) que será apresentado no segundo semestre de 2013.</p>\r\n\r\n<p>Foi professor da escola de folclore José Maria Arguedas (2000-2001). Também tem ministrado aulas particulares de violão e organizado palestras sobre a música Latino-americana tendo como base a rítmica aplicada ao violão.&nbsp;&nbsp;</p>\r\n\r\n<p>Recentemente participou de projetos de integração latino-americana, o primeiro, Romance de mi destino (2010), é um disco de Pasillos e Valses de Equador e Peru respectivamente que inclui a participação de artistas de ambos paises. O segundo, Fiesta em los Andes (2012), foi um show com músicas e músicos da Comunidade Andina que virou disco. &nbsp;Atualmente mantem uma intensa atividade como músico e arranjador participando de varias produções no Perú e em outros lugares.</p>\r\n\r\n<p>No Brasil fundou Los Cuatro (2010) grupo baseado na música instrumental latino-americana dentro da linguagem do choro. Este grupo lançou&nbsp;sua primeira produção fonográfica&nbsp;Outros caminho do Choro em de 2013.</p>\r\n\r\n<p>Também faz parte do quarteto de violões Maogani, grupo que fundou e do qual fez parte de 1996 a 1999, voltando em 2013. Atualmente está&nbsp;trabalhando na última produção de Maogani e Renato Braz que foi&nbsp;gravada em Lima (Peru) com canções de Venezuela, Chile, Peru, Argentina, Cuba, Colombia e Brasil.</p>\r\n\r\n<p>Em Agosto de 2013 gravou em New York, junto a Edward Perez, Erick Kurimski e Yayo Serka, uma produção que inclui algumas músicas próprias, além de algumas músicas tradicionais do folclore Peruano. Este material está&nbsp;sendo editado e será lançado em 2014.</p>",
    },
    {
        "id": "170",
        "name": "Berredo",
        "inverted": "Berredo (Guimarães, Durval Berredo)",
        "roles": ["Compositor", "Funcionário Público", "Flautista"],
        "birth_place": "Rio de Janeiro - RJ",
        "sources": "1. Depoimento do bandolinista Déo Rian.\n2. Depoimento do flautista Gerson Ferreira Pinto.",
        "bio": "<p>Morador do bairro de Marechal Hermes, foi freqüentador de rodas de choro tradicionais como a do Retiro da Velha Guarda em Jacarepaguá, nas décadas de 50 e 60, e a do Suvaco de Cobra na Penha, na década de 70. Possuía cadernos manuscritos com as composições dos chorões de várias gerações, transcritas por Candinho Silva, Manoel Nascimento, entre outros. No final da década de 70, quando faleceu, a sua flauta e esses cadernos foram doados a Gerson Ferreira Pinto, flautista do conjunto Amigos do Choro. Segundo depoimento de Berredo a Gerson, o mais antigo desses cadernos pertenceu ao pai de Pixinguinha.</p>\r\n\r\n<p>Datas de nascimneto e morte aproximadas.</p>",
        "encyclopedia": "Enciclopédia Ilustrada do Choro no Séc. XIX",
    },
    {
        "id": "1681",
        "name": "Paulo Aragão",
        "inverted": "Aragão, Paulo",
        "roles": ["Arranjador(a)", "Violonista"],
        "birth": "05.03.1976",
        "birth_place": "Rio de Janeiro - RJ",
        "bio": "<p>Paulo Aragão é um dos mais destacados arranjadores brasileiros da nova geração, tendo trabalhado ao lado de nomes como Sergio Assad, Mauricio Carrilho e Guinga. Requisitado com frequência por artistas como Yamandu Costa e Hamilton de Holanda, já teve composições e arranjos tocados por orquestras como a Los Angeles Philharmonic Orchestra, a Orchestre National de France, a Gewandhaus Orchestra de Leipzig, a Metropole Orkest (Holanda), a Orquestra Sinfônica Brasileira (OSB), a Orquestra Petrobras Pró-Música (RJ), a Orquestra Jazz Sinfônica (SP), entre outras. É integrante do premiado Quarteto Maogani de Violões, com o qual já ganhou os Prêmios TIM, Caras e Rival BR. É professor da Escola Portátil de Música, no Rio de Janeiro.</p>",
    },
]


# ---------------------------------------------------------------------------
# People with no record in the acervo
# ---------------------------------------------------------------------------
# The acervo mentions these people in free-text fields (lyrics, provenance,
# edition) without giving them a record in the encyclopedia.  They are
# registered anyway, with the origin of the identification noted.

EXTRA_PERSONS = [
    {
        "id": "baptista-junior",
        "name": "Baptista Júnior",
        "inverted": "Júnior, Baptista",
        "roles": ["Letrista"],
        "bio": "",
        "note": (
            "The acervo records the lyrics of “A Araponga e a Juriti” as "
            "“Letra de Baptista Junior”, with no record in the encyclopedia. "
            "The identification is provisional: it may be the poet Júlio "
            "Baptista de Mesquita (1881-1947) or the composer Batista Júnior "
            "(1894-1943)."
        ),
    },
    {
        "id": "gerson-ferreira-pinto",
        "name": "Gerson Ferreira Pinto",
        "inverted": "Pinto, Gerson Ferreira",
        "roles": ["Flautista"],
        "bio": "",
        "wikidata": "Q20048060",
        "note": (
            "Mentioned in the provenance of the copy of “A baianinha” "
            "(arquivo de Gerson Ferreira Pinto) and in the biography of "
            "Berredo, who describes him as the flautist of the group Amigos "
            "do Choro. He has no record in the acervo."
        ),
    },
    {
        "id": "a-di-franco",
        "name": "A. Di Franco",
        "inverted": "Di Franco, A.",
        "roles": ["Editor"],
        "bio": "",
        "note": (
            "The acervo records the edition of “A Araponga e a Juriti” as "
            "“editada por A. Di Franco”, with no record in the encyclopedia "
            "and without clarifying whether it is a person or a publishing "
            "house. The identification is provisional."
        ),
    },
]


# ---------------------------------------------------------------------------
# Works
# ---------------------------------------------------------------------------
# Records transcribed from the records of the acervo.  The field “Cópia”
# appears here with the verbatim text; its structuring into copyist, editor
# and provenance is done by tools.acervo.fetch.parse_copy.

WORKS = [
    {
        "id": "771",
        "title": "A baianinha",
        "fields": {"Gênero": ["Polca"], "Compasso": ["2/4"]},
        "composers": [{"card": "1127", "name": "Candinho Trombone"}],
        "scores": [
            {
                "index": 0,
                "type": "Partitura melodia",
                "pdf": "score_825",
                "details": {"Cópia": ["manuscrita"]},
                "editorada": False,
                "restriction": None,
            },
            {
                "index": 1,
                "type": "Partitura melodia",
                "pdf": "score_826",
                "details": {
                    "Cópia": ["manuscrita por Manoel Pedro do Nascimento"],
                    "Data": ["06.12.1962"],
                },
                "editorada": False,
                "restriction": None,
            },
            {
                "index": 2,
                "type": "Partitura melodia",
                "pdf": "score_827",
                "details": {
                    "Cópia": ["manuscrita por Manoel Pedro do Nascimento"],
                    "Data": ["16.01.1921"],
                },
                "editorada": False,
                "restriction": None,
            },
            {
                "index": 3,
                "type": "Partitura melodia",
                "pdf": "score_828",
                "details": {
                    "Cópia": [
                        "manuscrita - Obtida do Sr. Berredo "
                        "(arquivo de Gerson Ferreira Pinto)"
                    ],
                },
                "editorada": False,
                "restriction": None,
            },
            {
                "index": 4,
                "type": "Partitura melodia e cifra",
                "pdf": "score_12811",
                "details": {
                    "Arranjo": ["Pedro Paes"],
                    "Cópia": ["editorada Casa do Choro"],
                },
                "editorada": True,
                "restriction": None,
            },
        ],
    },
    {
        "id": "7387",
        "title": "A 1ª polca a gente nunca esquece",
        "fields": {"Gênero": ["Polca"], "Compasso": ["2/4"]},
        "composers": [{"card": "1865", "name": "Maria Souto"}],
        "scores": [
            {
                "index": 0,
                "type": "Partitura melodia e cifra",
                "pdf": "score_9886",
                "details": {"Cópia": ["manuscrita por Maria Souto"]},
                "editorada": False,
                "restriction": None,
            },
        ],
    },
    {
        "id": "6266",
        "title": "Amarga saudade",
        "fields": {"Gênero": ["Valsa"], "Compasso": ["3/4"]},
        "composers": [{"card": "1465", "name": "Nabor Pires Camargo"}],
        "scores": [
            {
                "index": 0,
                "type": "Partitura melodia",
                "pdf": None,
                "details": {"Cópia": ["editada"]},
                "editorada": False,
                "restriction": (
                    "Visualização e consulta não autorizadas pela editora. "
                    "Disponível somente na Casa do Choro."
                ),
            },
            {
                "index": 1,
                "type": "Partitura melodia e cifra",
                "pdf": None,
                "details": {
                    "Arranjo": ["Miguel Rabello"],
                    "Cópia": ["editorada Casa do Choro"],
                },
                "editorada": True,
                "restriction": (
                    "Visualização e consulta não autorizadas pela editora. "
                    "Disponível somente na Casa do Choro."
                ),
            },
        ],
    },
    {
        "id": "3843",
        "title": "A Araponga e a Juriti",
        "fields": {"Gênero": ["Canção Maxixe"], "Compasso": ["2/4"]},
        "composers": [{"card": "1236", "name": "Marcelo Tupinambá"}],
        "scores": [
            {
                "index": 0,
                "type": "Partitura arranjo com letra para pequena orquestra",
                "pdf": "score_5588",
                "details": {
                    "Instrumentação": [
                        "baixo", "cello", "clarinete Bb", "flauta",
                        "piano", "violino 1", "violino 2",
                    ],
                    "Cópia": ["editada por A. Di Franco"],
                    "Letra": ["Letra de Baptista Junior"],
                },
                "editorada": False,
                "restriction": None,
            },
            {
                "index": 1,
                "type": "Partitura melodia e cifra",
                "pdf": "score_10496",
                "details": {
                    "Arranjo": ["Sergio Valdeos"],
                    "Cópia": ["editorada Casa do Choro"],
                },
                "editorada": True,
                "restriction": None,
            },
        ],
    },
    {
        "id": "4138",
        "title": "A baianinha",
        "fields": {"Gênero": ["Choro"], "Compasso": ["2/4"]},
        "composers": [{"card": "110", "name": "P. de Alcântara Bacellar"}],
        "scores": [
            {
                "index": 0,
                "type": "Partitura piano",
                "pdf": "score_5459",
                "details": {
                    "Instrumentação": ["piano"],
                    "Cópia": ["editada"],
                },
                "editorada": False,
                "restriction": None,
            },
        ],
    },
    {
        "id": "2394",
        "title": "Saudade de São João do Príncipe",
        "fields": {"Gênero": ["Choro"], "Compasso": ["2/4"]},
        "composers": [{"card": "1156", "name": "Viriato Figueira da Silva"}],
        "scores": [
            {
                "index": 0,
                "type": "Partitura melodia",
                "pdf": "score_1730",
                "details": {
                    "Cópia": [
                        "manuscrita por Cópia de Cândido Pereira da Silva (Candinho)"
                    ],
                },
                "editorada": False,
                "restriction": None,
            },
            {
                "index": 1,
                "type": "Partitura melodia e cifra",
                "pdf": "score_14094",
                "details": {
                    "Arranjo": ["Paulo Aragão"],
                    "Cópia": ["editorada Casa do Choro"],
                },
                "editorada": True,
                "restriction": None,
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Places
# ---------------------------------------------------------------------------
# The acervo records the place of birth in the format “Cidade - UF”.  The
# MeLODy model provides a single level of containment (city contained in a
# country), so the federal unit goes to the description of the place.

PLACES = [
    {
        "key": "Rio de Janeiro",
        "name": "Rio de Janeiro",
        "geonames": "3451190",
        "description": "Rio de Janeiro - RJ, Brazil.",
        "country": "Brazil",
    },
    {
        "key": "Indaiatuba",
        "name": "Indaiatuba",
        "geonames": "3461311",
        "description": "Indaiatuba - SP, Brazil.",
        "country": "Brazil",
    },
    {
        "key": "Tietê",
        "name": "Tietê",
        "geonames": "3446539",
        "description": "Tietê - SP, Brazil.",
        "country": "Brazil",
    },
    {
        "key": "Macaé",
        "name": "Macaé",
        "geonames": "3458266",
        "description": "Macaé - RJ, Brazil.",
        "country": "Brazil",
    },
    {
        "key": "Brasília",
        "name": "Brasília",
        "geonames": "3469058",
        "description": "Brasília - DF, Brazil.",
        "country": "Brazil",
    },
    {
        "key": "São Paulo",
        "name": "São Paulo",
        "geonames": "3448439",
        "description": "São Paulo - SP, Brazil.",
        "country": "Brazil",
    },
    {
        "key": "Brazil",
        "name": "Brazil",
        "geonames": "3469034",
        "description": "Brazil — country of naturality of the agents of the acervo.",
        "country": None,
        "country_label": "Brasil",
        "country_label_en": "Brazil",
    },
]


# ---------------------------------------------------------------------------
# Institutions
# ---------------------------------------------------------------------------

INSTITUTIONS = [
    {
        "key": "Instituto Casa do Choro",
        "name": "Instituto Casa do Choro",
        "abbreviation": "ICC",
        "address": "Rua da Carioca, 38 - Centro, Rio de Janeiro - RJ, Brasil",
        "location": "Rio de Janeiro",
        "sameAs": "https://acervo.casadochoro.com.br/Pages/view/2",
        "description": (
            "The Instituto Casa do Choro, installed at Rua da Carioca, 38 - "
            "Centro, Rio de Janeiro, in a building protected by INEPAC, built "
            "around 1902 and ceded by the Government of the State of Rio de "
            "Janeiro. It keeps the digitised collection of scores published in "
            "this dataset and is responsible for the editions that bear its "
            "name. Contact: +55 21 2242-9947 / contato@casadochoro.com.br"
        ),
    },
]


# ---------------------------------------------------------------------------
# Instrumentations
# ---------------------------------------------------------------------------
# Finer labels for the sets of instruments that the acervo lists only as a
# sequence of names.  The key is the signature — the list of instruments
# exactly as it appears in the acervo — and the value is the label of the
# instrumentation.  Sets without a label here get a label generated from the
# list itself.

INSTRUMENTATION_LABELS = {
    ("piano",): "Piano",
    (
        "baixo", "cello", "clarinete bb", "flauta", "piano",
        "violino 1", "violino 2",
    ): "Small orchestra",
}

#: Controlled term and external reference for each instrument listed by the
#: acervo.  The key is the normalised name; the value is the term of the
#: MeLODy vocabulary and the code of the instrument list of the Library of
#: Congress (``marcmusperf``).

INSTRUMENT_TERMS = {
    "baixo": ("terms:DoubleBass", "sd"),
    "cello": ("terms:Violoncello", "sc"),
    "clarinete bb": ("terms:Clarinet", "wc"),
    "clarinete": ("terms:Clarinet", "wc"),
    "flauta": ("terms:Flute", "wa"),
    "piano": ("terms:Piano", "ka"),
    "violino": ("terms:Violin", "sa"),
    "violino 1": ("terms:Violin", "sa"),
    "violino 2": ("terms:Violin", "sa"),
    "viola": ("terms:Viola", "sb"),
    "canto": ("terms:HighVoice", "va"),
    "trombone": ("terms:Trombone", "bd"),
    "trompete bb": ("terms:Trumpet", "bb"),
    "sax alto eb": ("terms:Saxophone", "wi"),
    "sax tenor bb": ("terms:Tenor", "vd"),
    "guitarra": ("terms:Guitar", "tb"),
    "violão": ("terms:Guitar", "tb"),
    "bandolim": ("terms:Mandolin", "td"),
    "timpano": ("terms:Timpani", "pa"),
}


# ---------------------------------------------------------------------------
# Bibliography
# ---------------------------------------------------------------------------
# The research sources cited in the records of the people.  The root "bib:"
# receives the text of the citation, so that the same work cited by different
# records yields the same entity.

BIBLIOGRAPHY = [
    {
        "key": "VASCONCELOS 1977",
        "abbreviation": "Vasconcelos 1977",
        "genre": "terms:ArticleBook",
        "title": "Panorama da música popular brasileira na Belle Époque",
        "author": None,
        "start_date": "1977-01-01",
        "location": "Rio de Janeiro",
        "description": "Rio de Janeiro: Livraria Santana Ltda., 1977.",
        # how to recognise this reference inside the citation of the record
        "match": ["vasconcelos", "1977"],
    },
    {
        "key": "PINTO 1978",
        "abbreviation": "Pinto 1978",
        "genre": "terms:ArticleBook",
        "title": "O Choro — reminiscências dos chorões antigos",
        "author": None,
        "start_date": "1978-01-01",
        "location": "Rio de Janeiro",
        "description": "2ª ed. Rio de Janeiro: Funarte, 1978.",
        "match": ["pinto", "1978"],
    },
    {
        "key": "ENCICLOPEDIA 1998",
        "abbreviation": "Enciclopédia da música brasileira 1998",
        "genre": "terms:ArticleBook",
        "title": (
            "Enciclopédia da música brasileira: popular, erudita e folclórica"
        ),
        "author": None,
        "start_date": "1998-01-01",
        "location": "São Paulo",
        "description": "São Paulo: Art Editora/Publifolha, 1998.",
        "match": ["enciclopedia da musica brasileira", "1998"],
    },
]


# ---------------------------------------------------------------------------
# Alternative names
# ---------------------------------------------------------------------------
# The acervo identifies the people by their display name, which is not always
# the civil name — “Candinho Trombone”, “Marcelo Tupinambá”.  These names
# become schema:alternateName; the display name is also added automatically,
# when it differs from the given name and the family name.

ALTERNATE_NAMES = {
    "1127": ["Candinho Trombone", "Candinho Silva"],
    "1236": ["Marcelo Tupinambá"],
    "2326": ["Miguel Rabello", "Miguel Rabello Bastos"],
    "170": ["Berredo"],
}


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------
# Free names used by the acervo that have to be resolved to a person record.
# The key is the normalised name (lower case, without accents, with the
# whitespace collapsed).

ALIASES = {
    # the acervo names the copyist by his full name between brackets
    "copia de candido pereira da silva candinho": "1127",
    "candinho silva": "1127",
    "a. di franco": "a-di-franco",
    "baptista junior": "baptista-junior",
    "gerson ferreira pinto": "gerson-ferreira-pinto",
    "berredo": "170",
}


# ---------------------------------------------------------------------------
# Homonymous records
# ---------------------------------------------------------------------------
# The acervo has two records for “Miguel Rabello” — “Rabello, Miguel”
# (2326) and “Bastos, Miguel Rabello” (2006) — with the same activities
# (composer, violinist), the same place of birth and no biography.  They are
# almost certainly the same person registered twice, so the two records are
# joined into a single entity.  The merge is provisional and is noted in the
# description of the person.

MERGED_CARDS = {
    "2326": ["2326", "2006"],
}


# ---------------------------------------------------------------------------
# Applying the alternative names to the records
# ---------------------------------------------------------------------------

for _card in CARDS:
    _card.setdefault("alternate", [])
    _card["alternate"] = list(ALTERNATE_NAMES.get(_card["id"], [])) + _card["alternate"]

for _person in EXTRA_PERSONS:
    _person.setdefault("alternate", [])
