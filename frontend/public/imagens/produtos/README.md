# Ilustrações de categorias

Os SVGs em `categorias/` são ilustrações vetoriais originais criadas para esta interface, sem recursos de terceiros, marcas ou modelos específicos. Não há atribuição externa obrigatória. São imagens genéricas de categoria e não fotografias dos produtos.

Arquivos estáveis: `violoes.svg`, `guitarras.svg`, `baixos.svg`, `teclados.svg`, `baterias-percussao.svg` e `acessorios.svg`. Categorias desconhecidas usam um fallback visual local. Cada card ilustrado exibe “Imagem meramente ilustrativa”.

O componente `ImagemProduto` possui uma entrada opcional `imagemReal`, reservada a futuras fotografias reais revisadas e fornecidas pelo catálogo autorizado. Aceita somente caminhos locais em `/imagens/produtos/reais/` e texto alternativo explícito; prioriza essa imagem e, em caso de falha, tenta a ilustração da categoria antes do placeholder. Essa entrada ainda não é enviada pela API, não busca fotografias automaticamente e não modifica as autorizações atuais.
