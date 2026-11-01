import type {
  DisponibilidadeAtendimento,
  ReferenciaResposta,
  RespostaAtendimento,
} from '../tipos/atendimento';
import { ErroHttp, requisitarJson } from './http';

function objeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === 'object' && valor !== null;
}

function referenciaValida(valor: unknown): valor is ReferenciaResposta {
  return (
    objeto(valor) &&
    typeof valor.titulo === 'string' &&
    valor.titulo.length > 0 &&
    valor.titulo.length <= 200 &&
    ['politica', 'catalogo', 'categorias', 'promocoes'].includes(
      String(valor.tipo),
    ) &&
    (valor.tipo === 'politica'
      ? Number.isInteger(valor.pagina) &&
        Number(valor.pagina) >= 1 &&
        Number(valor.pagina) <= 500
      : valor.pagina === null)
  );
}

export async function enviarPergunta(
  mensagem: string,
  sinal?: AbortSignal,
): Promise<RespostaAtendimento> {
  const configurado = Number(
    import.meta.env.VITE_ATENDIMENTO_TIMEOUT_MS ?? 130000,
  );
  const timeout =
    Number.isFinite(configurado) && configurado >= 1000 && configurado <= 600000
      ? configurado
      : 130000;
  const valor = await requisitarJson('/api/atendimento/mensagens', {
    corpo: { mensagem },
    sinal,
    timeout,
  });
  if (
    !objeto(valor) ||
    typeof valor.resposta !== 'string' ||
    !valor.resposta.trim() ||
    valor.resposta.length > 16000 ||
    ![
      'social',
      'fundamentada',
      'sem_evidencias',
      'esclarecer',
      'fora_escopo',
      'bloqueada',
      'limite',
      'entrada_invalida',
    ].includes(String(valor.estado)) ||
    !Array.isArray(valor.referencias) ||
    valor.referencias.length > 20 ||
    !valor.referencias.every(referenciaValida) ||
    typeof valor.requisicao_id !== 'string' ||
    !/^[a-f0-9-]{36}$/i.test(valor.requisicao_id)
  )
    throw new ErroHttp(502, 'resposta_invalida');
  return valor as unknown as RespostaAtendimento;
}

export async function consultarDisponibilidade(
  sinal?: AbortSignal,
): Promise<DisponibilidadeAtendimento> {
  const valor = await requisitarJson('/api/atendimento/disponibilidade', {
    sinal,
    timeout: 7000,
  });
  if (
    !objeto(valor) ||
    valor.api !== 'disponivel' ||
    !['acessivel', 'indisponivel'].includes(String(valor.modelo)) ||
    !Number.isInteger(valor.limite_mensagem) ||
    Number(valor.limite_mensagem) < 1 ||
    Number(valor.limite_mensagem) > 1000
  )
    throw new ErroHttp(502, 'resposta_invalida');
  return {
    modelo: valor.modelo as DisponibilidadeAtendimento['modelo'],
    limite_mensagem: Number(valor.limite_mensagem),
  };
}

export function mensagemErro(erro: unknown): string {
  if (erro instanceof DOMException && erro.name === 'TimeoutError')
    return 'A consulta demorou além do limite. Tente novamente.';
  if (erro instanceof ErroHttp) {
    if (erro.status === 429)
      return 'Há muitas consultas ou outra resposta em andamento. Aguarde um pouco e tente novamente.';
    if (erro.codigo === 'modelo_indisponivel')
      return 'O modelo local está indisponível. Tente novamente mais tarde.';
    if (erro.codigo === 'consulta_indisponivel')
      return 'Não foi possível consultar as informações da loja agora. Tente novamente mais tarde.';
    if (erro.codigo === 'publicacao_indisponivel')
      return 'As informações da loja ainda não estão liberadas para atendimento. Tente novamente mais tarde.';
    if (erro.codigo === 'geracao_interrompida')
      return 'O atendimento atingiu o limite de geração. Tente uma pergunta mais específica.';
    if (erro.codigo === 'resposta_modelo_invalida')
      return 'O atendimento recebeu uma resposta inválida do modelo. Tente novamente.';
    if (erro.codigo === 'resposta_invalida')
      return 'A API retornou uma resposta inválida. Tente novamente.';
    if (erro.status === 504 || erro.status === 408)
      return 'A consulta demorou além do limite. Tente novamente.';
    if ([413, 422].includes(erro.status))
      return 'Confira o conteúdo e o tamanho da sua pergunta.';
    if (erro.status === 503)
      return 'As informações autorizadas ou o serviço não estão disponíveis no momento.';
    return 'Não foi possível concluir a consulta. Verifique a conexão com a API.';
  }
  return 'A API não respondeu. Verifique a conexão e tente novamente.';
}
