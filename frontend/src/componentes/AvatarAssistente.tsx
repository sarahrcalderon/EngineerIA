export function AvatarAssistente({
  cabecalho = false,
}: {
  cabecalho?: boolean;
}) {
  return (
    <span
      className={cabecalho ? 'avatar-cabecalho' : 'avatar-assistente'}
      aria-hidden="true"
    >
      <span className="logotipo-emporio" />
    </span>
  );
}
