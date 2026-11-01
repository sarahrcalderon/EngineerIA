import type { ProdutoResposta } from '../tipos/atendimento';
import { ImagemProduto } from './ImagemProduto';

const moeda = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

export function ProdutosResposta({
  produtos,
}: {
  produtos: ProdutoResposta[];
}) {
  return (
    <ul className="produtos-resposta" aria-label="Produtos encontrados">
      {produtos.map((produto, indice) => (
        <li className="produto-resposta" key={indice}>
          <ImagemProduto categoria={produto.categoria} />
          <div className="dados-produto">
            {produto.categoria && (
              <span className="categoria-produto">{produto.categoria}</span>
            )}
            <strong className="nome-produto">{produto.nome}</strong>
            <strong className="preco-produto">
              {moeda.format(produto.preco_centavos / 100)}
            </strong>
            <span
              className={`disponibilidade-produto ${produto.disponivel ? 'disponivel' : 'indisponivel'}`}
            >
              <span aria-hidden="true">{produto.disponivel ? '●' : '○'}</span>{' '}
              {produto.disponivel ? 'Disponível' : 'Indisponível no momento'}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
