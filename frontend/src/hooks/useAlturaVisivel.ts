import { useEffect } from 'react';

/** Mantém a composição dentro da área disponível quando o teclado é aberto. */
export function useAlturaVisivel() {
  useEffect(() => {
    const janela = window.visualViewport;
    if (!janela) return;
    const atualizar = () => {
      document.documentElement.style.setProperty(
        '--altura-visivel',
        `${janela.height}px`,
      );
      document.documentElement.style.setProperty(
        '--topo-visivel',
        `${janela.offsetTop}px`,
      );
    };
    atualizar();
    janela.addEventListener('resize', atualizar);
    janela.addEventListener('scroll', atualizar);
    return () => {
      janela.removeEventListener('resize', atualizar);
      janela.removeEventListener('scroll', atualizar);
      document.documentElement.style.removeProperty('--altura-visivel');
      document.documentElement.style.removeProperty('--topo-visivel');
    };
  }, []);
}
