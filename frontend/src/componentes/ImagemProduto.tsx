import { Music2 } from 'lucide-react';
import { useState } from 'react';

const categorias: Record<string, { arquivo: string; descricao: string }> = {
  violao: { arquivo: 'violoes', descricao: 'violão' },
  violoes: { arquivo: 'violoes', descricao: 'violão' },
  guitarra: { arquivo: 'guitarras', descricao: 'guitarra' },
  guitarras: { arquivo: 'guitarras', descricao: 'guitarra' },
  baixo: { arquivo: 'baixos', descricao: 'baixo' },
  baixos: { arquivo: 'baixos', descricao: 'baixo' },
  teclado: { arquivo: 'teclados', descricao: 'teclado' },
  teclados: { arquivo: 'teclados', descricao: 'teclado' },
  bateria: { arquivo: 'baterias-percussao', descricao: 'bateria e percussão' },
  baterias: { arquivo: 'baterias-percussao', descricao: 'bateria e percussão' },
  'baterias e percussao': {
    arquivo: 'baterias-percussao',
    descricao: 'bateria e percussão',
  },
  percussao: {
    arquivo: 'baterias-percussao',
    descricao: 'bateria e percussão',
  },
  acessorios: { arquivo: 'acessorios', descricao: 'acessórios musicais' },
};

/** Somente para futura foto real revisada e fornecida pelo catálogo autorizado. */
export interface ImagemRealProduto {
  src: string;
  alt: string;
}

export function ImagemProduto({
  categoria,
  imagemReal,
}: {
  categoria: string | null;
  imagemReal?: ImagemRealProduto;
}) {
  const chave = (categoria ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();
  const ilustracao = Object.hasOwn(categorias, chave)
    ? categorias[chave]
    : undefined;
  const realValida =
    imagemReal &&
    imagemReal.alt.trim() &&
    /^\/imagens\/produtos\/reais\/[a-zA-Z0-9/_-]+\.(?:png|jpe?g|webp|avif|svg)$/.test(
      imagemReal.src,
    );
  const opcoes = [
    ...(realValida ? [{ ...imagemReal, ilustrativa: false }] : []),
    ...(ilustracao
      ? [
          {
            src: `/imagens/produtos/categorias/${ilustracao.arquivo}.svg`,
            alt: `Ilustração genérica de ${ilustracao.descricao}; não representa o modelo exato.`,
            ilustrativa: true,
          },
        ]
      : []),
  ];
  return (
    <ImagemComFallback
      key={opcoes.map((o) => o.src).join('|')}
      opcoes={opcoes}
    />
  );
}

function ImagemComFallback({
  opcoes,
}: {
  opcoes: { src: string; alt: string; ilustrativa: boolean }[];
}) {
  const [indice, definirIndice] = useState(0);
  const imagem = opcoes[indice];
  return (
    <figure className="imagem-produto">
      <div className="quadro-imagem-produto">
        {imagem ? (
          <img
            src={imagem.src}
            alt={imagem.alt}
            width={320}
            height={208}
            loading="lazy"
            decoding="async"
            onError={() => definirIndice((atual) => atual + 1)}
          />
        ) : (
          <div
            className="imagem-produto-fallback"
            role="img"
            aria-label="Ilustração de categoria indisponível"
          >
            <Music2 size={36} aria-hidden="true" />
            <span>Ilustração indisponível</span>
          </div>
        )}
      </div>
      {(!imagem || imagem.ilustrativa) && (
        <figcaption>Imagem meramente ilustrativa</figcaption>
      )}
    </figure>
  );
}
