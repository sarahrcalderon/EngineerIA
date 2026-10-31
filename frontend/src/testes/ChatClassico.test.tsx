import { fireEvent, render, renderHook, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createRef } from 'react';
import { AreaMensagens } from '../componentes/AreaMensagens';
import { CampoMensagem } from '../componentes/CampoMensagem';
import { useAlturaVisivel } from '../hooks/useAlturaVisivel';
import type { MensagemConversa } from '../tipos/atendimento';

const mensagens: MensagemConversa[] = [
  {
    identificador: 1,
    papel: 'usuario',
    texto: 'Pergunta fictícia\nSegunda linha',
    referencias: [],
  },
  {
    identificador: 2,
    papel: 'assistente',
    texto: 'Retorno fictício',
    referencias: [],
  },
];

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('chat clássico', () => {
  it('mantém saudação no histórico e distingue balões por remetente', () => {
    render(<AreaMensagens mensagens={mensagens} aguardando={false} />);
    expect(screen.getByLabelText('Mensagem de boas-vindas')).toHaveTextContent(
      'Olá! Bem-vindo à Empório da Música.',
    );
    expect(screen.getByLabelText('Sua mensagem')).toHaveClass(
      'mensagem-usuario',
    );
    expect(screen.getByLabelText('Resposta do assistente')).toHaveClass(
      'mensagem-assistente',
    );
    expect(screen.getByLabelText('Sua mensagem').textContent).toContain(
      'Pergunta fictícia\nSegunda linha',
    );
    expect(
      screen.getByRole('region', { name: 'Mensagens do atendimento' }),
    ).toHaveAttribute('tabindex', '0');
    expect(screen.getByRole('log')).toHaveAttribute('aria-live', 'polite');
  });

  it('retira sugestões depois do primeiro envio sem remover a saudação', () => {
    const escolher = vi.fn();
    const { rerender } = render(
      <AreaMensagens mensagens={[]} aguardando={false} aoEscolher={escolher} />,
    );
    fireEvent.click(
      screen.getByRole('button', { name: 'Explore as categorias' }),
    );
    expect(escolher).toHaveBeenCalledWith(
      'Quais categorias estão cadastradas?',
    );
    rerender(
      <AreaMensagens
        mensagens={mensagens}
        aguardando={false}
        aoEscolher={escolher}
      />,
    );
    expect(
      screen.queryByLabelText('Sugestões de perguntas'),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText('Mensagem de boas-vindas')).toBeVisible();
  });

  it('preserva a leitura acima do final e permite voltar às mensagens recentes', () => {
    const rolar = vi.fn();
    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      configurable: true,
      value: rolar,
    });
    const { rerender } = render(
      <AreaMensagens mensagens={mensagens} aguardando={false} />,
    );
    const regiao = screen.getByRole('region');
    Object.defineProperties(regiao, {
      scrollHeight: { value: 1400 },
      clientHeight: { value: 400 },
    });
    fireEvent.scroll(regiao, { target: { scrollTop: 100 } });
    rolar.mockClear();
    rerender(
      <AreaMensagens
        mensagens={[...mensagens, { ...mensagens[0], identificador: 3 }]}
        aguardando={false}
      />,
    );
    expect(rolar).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole('button', { name: 'Ver mensagens recentes' }),
    );
    expect(rolar).toHaveBeenCalledOnce();
    expect(
      screen.queryByRole('button', { name: 'Ver mensagens recentes' }),
    ).not.toBeInTheDocument();
  });

  it('respeita movimento reduzido ao acompanhar novas mensagens', () => {
    const rolar = vi.fn();
    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      configurable: true,
      value: rolar,
    });
    vi.stubGlobal('matchMedia', () => ({ matches: true }));
    render(<AreaMensagens mensagens={mensagens} aguardando />);
    expect(rolar).toHaveBeenCalledWith({ behavior: 'instant', block: 'end' });
    expect(screen.getByRole('status')).toHaveTextContent(
      'Consultando as fontes autorizadas…',
    );
  });

  it('expande o campo até o limite visual e preserva a referência de foco', () => {
    const referencia = createRef<HTMLTextAreaElement>();
    const props = {
      texto: '',
      aoDigitar: vi.fn(),
      aoEnviar: vi.fn(),
      aoInterromper: vi.fn(),
      aguardando: false,
      limite: 1000,
      referencia,
    };
    const { rerender } = render(<CampoMensagem {...props} />);
    const campo = screen.getByRole('textbox');
    Object.defineProperty(campo, 'scrollHeight', {
      configurable: true,
      value: 260,
    });
    rerender(<CampoMensagem {...props} texto={'Linha\n'.repeat(30)} />);
    expect(campo).toHaveStyle({ height: '144px' });
    expect(referencia.current).toBe(campo);
    Object.defineProperty(campo, 'scrollHeight', { value: 44 });
    rerender(<CampoMensagem {...props} texto="Curta" />);
    expect(campo).toHaveStyle({ height: '44px' });
  });

  it('acompanha área visível do teclado e remove listeners ao desmontar', () => {
    const janela = Object.assign(new EventTarget(), {
      height: 430,
      offsetTop: 0,
    });
    vi.stubGlobal('visualViewport', janela);
    const { unmount } = renderHook(useAlturaVisivel);
    expect(
      document.documentElement.style.getPropertyValue('--altura-visivel'),
    ).toBe('430px');
    janela.height = 370;
    janela.offsetTop = 12;
    janela.dispatchEvent(new Event('resize'));
    expect(
      document.documentElement.style.getPropertyValue('--altura-visivel'),
    ).toBe('370px');
    expect(
      document.documentElement.style.getPropertyValue('--topo-visivel'),
    ).toBe('12px');
    unmount();
    janela.dispatchEvent(new Event('resize'));
    expect(
      document.documentElement.style.getPropertyValue('--altura-visivel'),
    ).toBe('');
  });
});
