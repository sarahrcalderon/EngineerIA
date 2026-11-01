# Imagens ilustrativas nos cards

Data: 01/11/2026. Escopo exclusivamente de apresentação frontend.

Criados seis SVGs originais em `frontend/public/imagens/produtos/categorias/`: violões, guitarras, baixos, teclados, baterias/percussão e acessórios. Não usam marcas, modelos ou recursos de terceiros. O README nesse diretório documenta a origem, o caráter genérico e o uso futuro de fotos reais. As categorias autorizadas encontradas no catálogo foram guitarras, baixos e baterias/percussão; todas estão cobertas. As demais ilustrações ficam disponíveis para categorias correspondentes, sem criar ou alterar registros do catálogo.

`ImagemProduto.tsx` associa somente a categoria autorizada recebida, normalizando acentos e maiúsculas. Os caminhos são locais e estáveis. A imagem tem proporção 20:13, dimensões explícitas, `object-fit: contain`, fundo neutro, bordas arredondadas, alt descritivo, carregamento lazy e decodificação assíncrona. Cada ilustração tem a legenda “Imagem meramente ilustrativa”. Categoria desconhecida ou imagem que falhou usa ícone musical e texto de indisponibilidade, sem tentativas de carregamento em loop.

O componente aceita opcionalmente uma futura imagem real revisada com caminho local sob `/imagens/produtos/reais/` e alt explícito. Quando fornecida, tem prioridade e não recebe o rótulo de ilustração. Se falhar, tenta a ilustração da categoria e depois o placeholder. URLs externas são recusadas. Nenhuma foto real foi adicionada, nem foi criado campo novo na API: uma futura integração deve fornecer apenas fotografias aprovadas do catálogo.

Modificados `ProdutosResposta.tsx` e `global.css`: a imagem fica acima dos dados em telas menores e ao lado em desktop. Nome, preço BRL, disponibilidade, avatar e favicon foram preservados. Não há extração de dados do texto, mudanças no backend, Ollama, manifesto, arquivos operacionais ou política de publicação.

Regressões em `ImagemProduto.test.tsx`: seis categorias, desconhecida/nula, chave inesperada, erro de carregamento, mudança de categoria, prioridade e falha de foto real, recusa de URL externa, múltiplos cards e preservação dos dados comerciais.

Validação: **69 testes frontend aprovados**, incluindo duas integrações HTTP reais contra 8001; **342 testes backend aprovados**, com 11 homologações Ollama optativas puladas porque a inferência não foi modificada nesta etapa. ESLint, TypeScript/build, Prettier e `git diff --check` aprovados. Permanece o aviso preexistente de depreciação TestClient/httpx.

Edge headless com perfil temporário: componente real renderizado com sete produtos fictícios, sem substituir respostas da API. Foram conferidos carregamento das seis imagens locais, sete legendas, categoria desconhecida, `contain`, ausência de excesso horizontal em 320/390/768/1440 px e fallback após erro de imagem. Nenhuma exceção JavaScript observada. A captura móvel foi inspecionada visualmente. Esses ensaios validam apresentação; não afirmam nova homologação da seleção de produtos pelo modelo.

Limites: ilustrações não representam o modelo, cor ou acessórios exatos do produto; categorias não mapeadas usam placeholder. A seleção de vários produtos pelo modelo mantém as limitações já registradas na etapa anterior. Não houve staging, commit ou push.
