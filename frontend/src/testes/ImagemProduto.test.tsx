import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ImagemProduto } from '../componentes/ImagemProduto';
import { ProdutosResposta } from '../componentes/ProdutosResposta';

describe('imagens ilustrativas locais', () => {
  it.each([
    ['Violões', 'violoes'],
    ['Guitarras', 'guitarras'],
    ['Baixos', 'baixos'],
    ['Teclados', 'teclados'],
    ['Baterias e Percussão', 'baterias-percussao'],
    ['Acessórios', 'acessorios'],
  ])('associa %s à categoria autorizada', (categoria, arquivo) => {
    render(<ImagemProduto categoria={categoria} />);
    expect(screen.getByRole('img')).toHaveAttribute(
      'src',
      `/imagens/produtos/categorias/${arquivo}.svg`,
    );
    expect(screen.getByRole('img')).toHaveAccessibleName(/Ilustração genérica/);
    expect(screen.getByRole('img')).toHaveAttribute('loading', 'lazy');
    expect(screen.getByRole('img')).toHaveAttribute('decoding', 'async');
    expect(screen.getByText('Imagem meramente ilustrativa')).toBeVisible();
  });

  it.each([null, 'Categoria desconhecida', '__proto__'])(
    'usa placeholder sem requisição para categoria %s',
    (categoria) => {
      render(<ImagemProduto categoria={categoria} />);
      expect(screen.getByRole('img')).toHaveAccessibleName(
        'Ilustração de categoria indisponível',
      );
      expect(document.querySelector('img')).toBeNull();
    },
  );

  it('trata imagem ausente e recupera quando a categoria muda', () => {
    const { rerender } = render(<ImagemProduto categoria="Guitarras" />);
    fireEvent.error(screen.getByRole('img'));
    expect(screen.getByText('Ilustração indisponível')).toBeVisible();
    rerender(<ImagemProduto categoria="Baixos" />);
    expect(screen.getByRole('img')).toHaveAttribute(
      'src',
      '/imagens/produtos/categorias/baixos.svg',
    );
  });

  it('prioriza futura foto real local e recua para ilustração se ela falhar', () => {
    render(
      <ImagemProduto
        categoria="Guitarras"
        imagemReal={{
          src: '/imagens/produtos/reais/revisada.webp',
          alt: 'Fotografia real revisada do produto',
        }}
      />,
    );
    expect(screen.getByRole('img')).toHaveAttribute(
      'src',
      '/imagens/produtos/reais/revisada.webp',
    );
    expect(
      screen.queryByText('Imagem meramente ilustrativa'),
    ).not.toBeInTheDocument();
    fireEvent.error(screen.getByRole('img'));
    expect(screen.getByRole('img')).toHaveAttribute(
      'src',
      '/imagens/produtos/categorias/guitarras.svg',
    );
    expect(screen.getByText('Imagem meramente ilustrativa')).toBeVisible();
    fireEvent.error(screen.getByRole('img'));
    expect(screen.getByText('Ilustração indisponível')).toBeVisible();
  });

  it('recusa imagens externas', () => {
    render(
      <ImagemProduto
        categoria="Violões"
        imagemReal={{ src: 'https://example.invalid/foto.png', alt: 'Foto' }}
      />,
    );
    expect(screen.getByRole('img')).toHaveAttribute(
      'src',
      '/imagens/produtos/categorias/violoes.svg',
    );
  });

  it('preserva dados comerciais e avisos em múltiplos cards', () => {
    render(
      <ProdutosResposta
        produtos={[
          {
            nome: 'Instrumento fictício A',
            preco_centavos: 1890000,
            disponivel: true,
            categoria: 'Guitarras',
          },
          {
            nome: 'Instrumento fictício B',
            preco_centavos: 59990,
            disponivel: false,
            categoria: 'Baixos',
          },
        ]}
      />,
    );
    const cards = within(screen.getByRole('list')).getAllByRole('listitem');
    expect(cards).toHaveLength(2);
    expect(within(cards[0]).getByText(/18\.900,00/)).toBeVisible();
    expect(within(cards[1]).getByText('Indisponível no momento')).toBeVisible();
    expect(screen.getAllByText('Imagem meramente ilustrativa')).toHaveLength(2);
  });
});
