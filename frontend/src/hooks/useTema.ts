import { useEffect, useState } from 'react';
type Tema = 'claro' | 'escuro';

function temaInicial(): Tema {
  try {
    const salvo = localStorage.getItem('emporio-tema');
    if (salvo === 'claro' || salvo === 'escuro') return salvo;
  } catch {
    /* Armazenamento visual opcional. */
  }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches
    ? 'escuro'
    : 'claro';
}

export function useTema() {
  const [tema, definirTema] = useState<Tema>(temaInicial);
  useEffect(() => {
    document.documentElement.dataset.tema = tema;
    document.documentElement.style.colorScheme =
      tema === 'escuro' ? 'dark' : 'light';
  }, [tema]);
  function alternarTema() {
    const proximo = tema === 'claro' ? 'escuro' : 'claro';
    definirTema(proximo);
    try {
      localStorage.setItem('emporio-tema', proximo);
    } catch {
      /* O tema funciona sem persistência. */
    }
  }
  return { tema, alternarTema };
}
