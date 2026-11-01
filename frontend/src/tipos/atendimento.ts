export type EstadoResposta =
  | 'social'
  | 'fundamentada'
  | 'sem_evidencias'
  | 'esclarecer'
  | 'fora_escopo'
  | 'bloqueada'
  | 'limite'
  | 'entrada_invalida';
export interface ReferenciaResposta {
  tipo: 'politica' | 'catalogo' | 'categorias' | 'promocoes';
  titulo: string;
  pagina: number | null;
}
export interface ProdutoResposta {
  nome: string;
  preco_centavos: number;
  disponivel: boolean;
  categoria: string | null;
}
export interface RespostaAtendimento {
  estado: EstadoResposta;
  resposta: string;
  referencias: ReferenciaResposta[];
  requisicao_id: string;
  produtos?: ProdutoResposta[];
  complemento?: string;
}
export interface MensagemConversa {
  identificador: number;
  papel: 'usuario' | 'assistente';
  texto: string;
  referencias: ReferenciaResposta[];
  produtos?: ProdutoResposta[];
  complemento?: string;
  horario?: string;
}
export interface DisponibilidadeAtendimento {
  modelo: 'acessivel' | 'indisponivel';
  limite_mensagem: number;
}
