export type EstadoResposta =
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
export interface RespostaAtendimento {
  estado: EstadoResposta;
  resposta: string;
  referencias: ReferenciaResposta[];
  requisicao_id: string;
}
export interface MensagemConversa {
  identificador: number;
  papel: 'usuario' | 'assistente';
  texto: string;
  referencias: ReferenciaResposta[];
}
export interface DisponibilidadeAtendimento {
  modelo: 'acessivel' | 'indisponivel';
  limite_mensagem: number;
}
