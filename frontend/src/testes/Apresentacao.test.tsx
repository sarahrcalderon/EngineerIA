import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { AreaMensagens } from '../componentes/AreaMensagens';
import type { MensagemConversa, ProdutoResposta } from '../tipos/atendimento';

const produto: ProdutoResposta = {
  nome: 'Instrumento de teste',
  preco_centavos: 1890000,
  disponivel: true,
  categoria: 'Cordas fictícias',
};
const mensagem: MensagemConversa = {
  identificador: 1,
  papel: 'assistente',
  texto: 'Texto alternativo',
  referencias: [
    { tipo: 'catalogo', titulo: 'Catálogo de produtos', pagina: null },
  ],
  produtos: [produto],
  complemento: '',
  horario: '2026-11-01T15:30:00-03:00',
};

describe('apresentação comercial', () => {
  it('exibe introdução e todos os três produtos ordenados recebidos da API', () => {
    render(
      <AreaMensagens
        mensagens={[
          {
            ...mensagem,
            introducao:
              'Encontrei estas opções com os menores preços do catálogo autorizado:',
            produtos: [10000, 20000, 30000].map((preco, i) => ({
              ...produto,
              nome: `Opção fictícia ${i + 1}`,
              preco_centavos: preco,
            })),
          },
        ]}
        aguardando={false}
      />,
    );
    expect(
      screen.getByText(/Encontrei estas opções com os menores preços/),
    ).toBeVisible();
    const cards = within(
      screen.getByRole('list', { name: 'Produtos encontrados' }),
    ).getAllByRole('listitem');
    expect(cards).toHaveLength(3);
    cards.forEach((card, i) =>
      expect(within(card).getByText(`Opção fictícia ${i + 1}`)).toBeVisible(),
    );
  });
  it('destaca um produto com preço BRL e disponibilidade sem texto técnico', () => {
    render(<AreaMensagens mensagens={[mensagem]} aguardando={false} />);
    const lista = screen.getByRole('list', { name: 'Produtos encontrados' });
    expect(within(lista).getByText('Instrumento de teste')).toBeVisible();
    expect(within(lista).getByText(/R\$\s*18\.900,00/)).toBeVisible();
    expect(within(lista).getByText('Disponível')).toBeVisible();
    expect(screen.queryByText('Texto alternativo')).not.toBeInTheDocument();
    expect(document.querySelector('time')).toHaveAttribute(
      'datetime',
      mensagem.horario,
    );
    const fonte = screen.getByText('Catálogo de produtos');
    expect(fonte).not.toBeVisible();
    fireEvent.click(screen.getByText('Fontes consultadas'));
    expect(fonte).toBeVisible();
  });

  it('mostra vários produtos e indisponibilidade sem sugerir estoque', () => {
    render(
      <AreaMensagens
        mensagens={[
          {
            ...mensagem,
            produtos: [
              produto,
              { ...produto, nome: 'Outro instrumento', disponivel: false },
            ],
          },
        ]}
        aguardando={false}
      />,
    );
    expect(
      within(
        screen.getByRole('list', { name: 'Produtos encontrados' }),
      ).getAllByRole('listitem'),
    ).toHaveLength(2);
    expect(screen.getByText('Indisponível no momento')).toBeVisible();
  });

  it('mantém política complementar e página sem tratar Markdown como HTML', () => {
    render(
      <AreaMensagens
        mensagens={[
          {
            ...mensagem,
            complemento:
              'Trocas fictícias exigem etiqueta violeta. <script>teste</script>',
            referencias: [
              {
                tipo: 'politica',
                titulo: 'Políticas da loja — página 3',
                pagina: 3,
              },
            ],
          },
        ]}
        aguardando={false}
      />,
    );
    expect(screen.getByText(/Trocas fictícias/)).toBeVisible();
    expect(document.querySelector('script')).toBeNull();
    fireEvent.click(screen.getByText('Fontes consultadas'));
    expect(screen.getByText('Políticas da loja — página 3')).toBeVisible();
  });

  it('agrupa mensagens consecutivas sem repetir o avatar', () => {
    render(
      <AreaMensagens
        mensagens={[mensagem, { ...mensagem, identificador: 2 }]}
        aguardando={false}
      />,
    );
    expect(
      document.querySelectorAll(
        '.lista-mensagens > .mensagem .avatar-assistente',
      ),
    ).toHaveLength(1);
    expect(document.querySelectorAll('.espaco-avatar')).toHaveLength(1);
  });

  it('usa favicon musical laranja com versão e avatar circular responsivo', () => {
    const svg = readFileSync('icon_emporio.svg', 'utf8');
    const html = readFileSync('index.html', 'utf8');
    const css = readFileSync('src/estilos/global.css', 'utf8');
    expect(svg).toContain('#EA741C');
    expect(svg).not.toContain('#1C274C');
    expect(html).toContain('/icon_emporio.svg?v=laranja-1');
    expect(css).toContain('border-radius: 50%');
    expect(css).toContain('flex-basis: 36px');
  });
});
